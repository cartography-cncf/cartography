import logging
import re
import time
from typing import Any

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)

# (connect, read) timeouts, matching the convention used by the other intel modules.
_TIMEOUT = (60, 60)
_MAX_RETRIES = 5
# Railway's rate limit window is one hour. If the API asks us to wait longer than this we
# would rather fail loudly than silently stall a sync for the better part of an hour.
_MAX_RETRY_AFTER_SECONDS = 300
_DEFAULT_RETRY_AFTER_SECONDS = 30
_RATE_LIMIT_WARN_THRESHOLD = 10
_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")


class RailwayGraphQLError(Exception):
    """
    Railway answers with HTTP 200 even when the query failed, reporting the problem in the
    `errors` array of the response body instead. Callers must never treat such a response as
    an empty result set: doing so would let a cleanup job delete every node in the workspace.
    """

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        self.errors = errors
        messages = "; ".join(error.get("message", "unknown error") for error in errors)
        super().__init__(f"Railway API returned GraphQL errors: {messages}")

    @property
    def is_not_authorized(self) -> bool:
        """
        True when every reported error is an authorization failure.

        Railway returns `Not Authorized` for fields the token cannot read (for example
        `apiTokens` with a workspace-scoped token) rather than omitting them, and it labels
        those errors `INTERNAL_SERVER_ERROR`, so the message is the only usable signal.
        Callers syncing optional resources use this to skip instead of aborting the sync.
        """
        return bool(self.errors) and all(
            "not authorized" in error.get("message", "").lower()
            for error in self.errors
        )


# ServiceDomainSyncStatus, CustomDomainSyncStatus and TCPProxySyncStatus share one set of
# values: ACTIVE, CREATING, DELETING, DELETED, UPDATING, UNSPECIFIED. Only these two mean the
# entry point is actually serving traffic. CREATING has not come up yet and DELETING/DELETED
# are on the way out, so counting them as exposure would over-report the attack surface.
LIVE_SYNC_STATUSES = frozenset({"ACTIVE", "UPDATING"})


def is_live_entrypoint(entrypoint: dict[str, Any]) -> bool:
    """
    True when a service domain, custom domain or TCP proxy is in a serving state.

    A custom domain additionally has to have passed DNS verification before it resolves.
    """
    if entrypoint.get("syncStatus") not in LIVE_SYNC_STATUSES:
        return False
    status = entrypoint.get("status")
    if isinstance(status, dict) and not status.get("verified"):
        return False
    return True


class RailwayPaginationError(Exception):
    """
    Railway reported another page but gave no usable cursor to reach it.

    Never downgrade this to a warning-and-stop: the cleanup jobs treat whatever they are
    handed as the exhaustive set, so a silently truncated list deletes every resource past
    the last page we managed to read.
    """


def _get_retry_after_seconds(response: requests.Response) -> int:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return max(0, int(retry_after))
        except ValueError:
            logger.warning(
                "Railway returned an unparseable Retry-After header: %s",
                retry_after,
            )
    reset = response.headers.get("X-RateLimit-Reset")
    if reset:
        try:
            return max(0, int(reset))
        except ValueError:
            logger.warning(
                "Railway returned an unparseable X-RateLimit-Reset header: %s",
                reset,
            )
    return _DEFAULT_RETRY_AFTER_SECONDS


def _warn_if_rate_limit_low(response: requests.Response) -> None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is None:
        return
    try:
        remaining_int = int(remaining)
    except ValueError:
        return
    if remaining_int <= _RATE_LIMIT_WARN_THRESHOLD:
        # Unlike GitHub we do not pre-emptively sleep here: Railway's window is an hour, so
        # sleeping would stall the sync far longer than it would save.
        logger.warning(
            "Railway API rate limit is nearly exhausted: %d requests remaining in the "
            "current hourly window.",
            remaining_int,
        )


@timeit
def call_railway_api(
    api_session: requests.Session,
    base_url: str,
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Execute a single GraphQL document against the Railway public API.

    :param api_session: Authenticated requests session.
    :param base_url: The Railway GraphQL endpoint.
    :param query: The GraphQL document to execute.
    :param variables: GraphQL variables for the document.
    :return: The `data` object of the response.
    :raises RailwayGraphQLError: if the response body contains any GraphQL errors.
    """
    payload = {"query": query, "variables": variables or {}}

    for attempt in range(_MAX_RETRIES):
        response = api_session.post(base_url, json=payload, timeout=_TIMEOUT)
        if response.status_code != 429:
            break
        sleep_seconds = _get_retry_after_seconds(response)
        if sleep_seconds > _MAX_RETRY_AFTER_SECONDS:
            raise RuntimeError(
                f"Railway API rate limit exhausted: the API asked us to wait "
                f"{sleep_seconds}s, which exceeds the {_MAX_RETRY_AFTER_SECONDS}s cap. "
                f"Use a token on a higher Railway plan or sync fewer projects.",
            )
        logger.warning(
            "Railway API returned 429, sleeping %ds before retry %d/%d.",
            sleep_seconds,
            attempt + 1,
            _MAX_RETRIES,
        )
        time.sleep(sleep_seconds)

    _warn_if_rate_limit_low(response)
    response.raise_for_status()

    body = response.json()
    if body.get("errors"):
        raise RailwayGraphQLError(body["errors"])
    return body["data"]


def unwrap_edges(connection: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Flatten a Relay connection into the list of its nodes.
    """
    return [edge["node"] for edge in connection["edges"]]


def paginated_query(
    api_session: requests.Session,
    base_url: str,
    query: str,
    variables: dict[str, Any],
    connection_path: tuple[str, ...],
    page_size: int = 100,
    after: str | None = None,
) -> list[dict[str, Any]]:
    """
    Walk every page of a Relay-style connection and return the flattened list of nodes.

    :param api_session: Authenticated requests session.
    :param base_url: The Railway GraphQL endpoint.
    :param query: A GraphQL document accepting `$first` and `$after` variables.
    :param variables: Any other variables the document needs.
    :param connection_path: Path of keys from `data` down to the connection object,
        e.g. ``("projects",)`` or ``("project", "services")``.
    :param page_size: Number of items to request per page.
    :param after: Cursor to resume from. Used to fetch the remainder of a connection whose
        first page already arrived inside a larger nested document.
    :return: Every node from `after` onwards, across every remaining page.
    """
    results: list[dict[str, Any]] = []
    cursor: str | None = after

    while True:
        data = call_railway_api(
            api_session,
            base_url,
            query,
            {**variables, "first": page_size, "after": cursor},
        )
        connection = data
        for key in connection_path:
            connection = connection[key]

        results.extend(unwrap_edges(connection))

        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break

        next_cursor = page_info["endCursor"]
        # A page that claims more results but gives no usable cursor to reach them cannot be
        # completed. Stopping here would hand a truncated list to a cleanup job that treats
        # it as exhaustive and deletes everything past this page, and restarting from a null
        # cursor would loop over page one forever. Fail loudly instead.
        if not next_cursor or next_cursor == cursor:
            raise RailwayPaginationError(
                f"Railway reported more pages for {'.'.join(connection_path)} but returned "
                f"an unusable endCursor ({next_cursor!r}); refusing to continue with an "
                f"incomplete result set.",
            )
        cursor = next_cursor

    return results


def build_tcp_proxy_batch_query(pairs: list[tuple[str, str]]) -> str:
    """
    Build a single GraphQL document querying `tcpProxies` for many (service, environment)
    pairs at once.

    `tcpProxies` is a root field requiring both ids, so a workspace with N services across M
    environments would otherwise cost N*M requests. GraphQL has no syntax for dynamic
    aliases, so the ids have to be interpolated into the document rather than passed as
    variables; they come from the Railway API and are validated as UUIDs first.
    """
    fields = []
    for index, (service_id, environment_id) in enumerate(pairs):
        for value in (service_id, environment_id):
            if not _UUID_RE.match(value):
                raise ValueError(
                    f"Refusing to interpolate non-UUID value into a GraphQL document: {value!r}",
                )
        fields.append(
            f'p{index}: tcpProxies(serviceId: "{service_id}", '
            f'environmentId: "{environment_id}") '
            f"{{ id domain proxyPort applicationPort syncStatus createdAt }}",
        )
    joined = "\n  ".join(fields)
    return f"query TcpProxies {{\n  {joined}\n}}"
