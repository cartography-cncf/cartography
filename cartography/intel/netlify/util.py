import logging
from typing import Any
from urllib.parse import urljoin
from urllib.parse import urlsplit

import requests

from cartography.util import timeit

logger = logging.getLogger(__name__)

# (connect, read) timeouts, matching the convention used by the other intel modules.
_TIMEOUT = (60, 60)
# Netlify caps `per_page` at 100.
# https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/
_PER_PAGE = 100
# Backstop against a server that keeps advertising a next page. At 100 items per page this
# still allows 100k objects of a single kind, far beyond any real Netlify team.
_MAX_PAGES = 1000
# Netlify allows 500 requests per minute and reports the remaining budget on every response.
_RATE_LIMIT_WARN_THRESHOLD = 25


# MongoDB extended JSON wrappers Netlify sends instead of the bare scalar. Netlify's API is
# Mongo-backed and leaks the raw BSON encoding on some fields, so an id can arrive as
# `{"$oid": "..."}` and a timestamp as `{"$date": "..."}`.
_EXTENDED_JSON_KEYS = frozenset(
    {"$oid", "$date", "$numberInt", "$numberLong", "$numberDouble"},
)


def unwrap_extended_json(value: Any) -> Any:
    """
    Reduce a MongoDB extended JSON wrapper to the scalar it wraps, leaving anything else alone.

    Neo4j only stores primitives and arrays of primitives, so a wrapped value fails the whole
    write batch rather than just its own property: `Property values can only be of primitive
    types or arrays thereof. Encountered: Map{$oid -> String(...)}`.

    Observed on `invite_id` in the team members payload for an outstanding invitation, where the
    same list also reports plain-string ids. The wrapper is the API's serialisation leaking
    through rather than a property of that one field, so it is applied to a payload's values as a
    whole instead of to a named field.

    :param value: A value straight off a Netlify response.
    :return: The unwrapped scalar for a recognised wrapper, otherwise the value unchanged.
    """
    if isinstance(value, dict) and len(value) == 1:
        ((key, wrapped),) = value.items()
        if key in _EXTENDED_JSON_KEYS and isinstance(wrapped, (str, int, float, bool)):
            return wrapped
    return value


class NetlifyPaginationError(Exception):
    """
    Netlify advertised another page but did not give a usable URL to reach it.

    Never downgrade this to a warning-and-stop: the cleanup jobs treat whatever list they are
    handed as the exhaustive set of live resources, so a silently truncated list deletes every
    resource past the last page we managed to read.
    """


class NetlifyPlanGatedError(Exception):
    """
    Netlify answered 403, so this endpoint is not available to the token or the team's plan.

    Raised rather than returning an empty list so the caller has to decide explicitly. Treating
    it as "the team has none of these" would let cleanup delete inventory a previous run on a
    higher plan had legitimately ingested; callers that tolerate it must skip their cleanup for
    the run, not just their load.
    """


def _warn_if_rate_limit_low(response: requests.Response) -> None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is None:
        return
    try:
        remaining_int = int(remaining)
    except ValueError:
        return
    if remaining_int <= _RATE_LIMIT_WARN_THRESHOLD:
        # We do not pre-emptively sleep: the window is only a minute wide and the session's
        # Retry adapter already honours Retry-After on the 429 itself.
        logger.warning(
            "Netlify API rate limit is nearly exhausted: %d requests remaining in the "
            "current one-minute window.",
            remaining_int,
        )


def _resolve_next_url(current_url: str, candidate: str) -> str:
    """
    Resolve a `Link` header URL against the request it came from, refusing to leave the origin.

    The session carries the Netlify bearer token on every request it makes, so following a link
    verbatim would hand that token to whatever host the header named. Netlify sends absolute
    same-origin URLs today; a relative one is resolved, and anything pointing elsewhere is
    rejected rather than requested.

    :raises NetlifyPaginationError: if the candidate resolves to a different scheme or host.
    """
    resolved = urljoin(current_url, candidate)
    current = urlsplit(current_url)
    target = urlsplit(resolved)
    if (target.scheme, target.netloc) != (current.scheme, current.netloc):
        raise NetlifyPaginationError(
            f"Netlify pagination link for {current_url} points at a different origin "
            f"({target.scheme}://{target.netloc}); refusing to send the API token there.",
        )
    return resolved


@timeit
def paginated_get(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    per_page: int = _PER_PAGE,
    allow_plan_gated: bool = False,
    allow_missing: bool = False,
) -> list[dict[str, Any]]:
    """
    Fetch every page of a Netlify list endpoint.

    Netlify paginates with `?page=N&per_page=M` and advertises the next page in an RFC-5988
    `Link` header, which requests already parses into `response.links`.

    Both tolerance flags default to False. Everything this returns is handed to a cleanup job
    that treats it as the exhaustive set of live resources, so turning a failed read into an
    empty list deletes real inventory. Only opt in for an endpoint whose absent or forbidden
    response has actually been observed, and skip the cleanup as well when you do.

    :param api_session: Authenticated requests session.
    :param url: Full URL of the API endpoint.
    :param params: Query parameters for the first request only. The `Link` URL already carries
        `page` and `per_page`, so re-sending them on later requests would fight the cursor.
    :param per_page: Page size, capped at 100 by the API.
    :param allow_plan_gated: When True a 403 returns the results gathered so far instead of
        raising NetlifyPlanGatedError.
    :param allow_missing: When True a 404 returns an empty list instead of raising.
    :return: Every object across every page.
    :raises NetlifyPaginationError: if a page advertises a successor it cannot reach, if that
        successor is off-origin, or if the endpoint returns something other than a JSON array.
    :raises NetlifyPlanGatedError: on a 403, unless allow_plan_gated is set.
    """
    all_results: list[dict[str, Any]] = []
    request_params: dict[str, Any] = {"per_page": per_page}
    if params:
        request_params.update(params)

    next_url: str | None = url
    pages_read = 0
    while next_url:
        # Only the first request carries our params; later ones use the Link URL verbatim.
        response = api_session.get(
            next_url,
            params=request_params if pages_read == 0 else None,
            timeout=_TIMEOUT,
        )
        if response.status_code == 404 and allow_missing:
            logger.debug("Netlify returned 404 for %s, treating as empty.", next_url)
            return []
        if response.status_code == 403:
            if not allow_plan_gated:
                raise NetlifyPlanGatedError(
                    f"Netlify returned 403 Forbidden for {next_url}. If this endpoint is "
                    f"plan-gated for this team, the caller must opt in and skip its cleanup.",
                )
            logger.warning(
                "Netlify returned 403 Forbidden for %s, skipping (likely plan-gated).",
                next_url,
            )
            return all_results
        _warn_if_rate_limit_low(response)
        response.raise_for_status()

        data = response.json()
        # A few endpoints answer `null` rather than `[]` when the resource does not exist.
        if data is None:
            return all_results
        if not isinstance(data, list):
            raise NetlifyPaginationError(
                f"Expected a JSON array from {next_url} but got {type(data).__name__}; "
                f"refusing to hand a misread response to a cleanup job.",
            )
        all_results.extend(data)
        pages_read += 1

        link = response.links.get("next")
        if not link:
            break
        candidate = link.get("url")
        # A page that claims more results but cannot say where they are cannot be completed.
        # Returning what we have would let cleanup delete everything past this page.
        if not candidate:
            raise NetlifyPaginationError(
                f"Netlify advertised another page for {url} but returned an unusable next "
                f"link ({candidate!r}); refusing to continue with an incomplete result set.",
            )
        resolved = _resolve_next_url(next_url, candidate)
        if resolved == next_url:
            raise NetlifyPaginationError(
                f"Netlify advertised another page for {url} but the next link points back at "
                f"the current page; refusing to loop on an incomplete result set.",
            )
        if pages_read >= _MAX_PAGES:
            raise NetlifyPaginationError(
                f"Netlify still advertised more pages for {url} after {_MAX_PAGES} pages; "
                f"refusing to continue with an incomplete result set.",
            )
        next_url = resolved

    return all_results


@timeit
def get_list(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    result_key: str | None = None,
    allow_missing: bool = False,
) -> list[dict[str, Any]]:
    """
    Fetch a Netlify collection that is not paginated.

    Normalises the three shapes Netlify uses for such endpoints: a bare array, an envelope
    object holding the array under a key (`{"branches": [...]}`), and a bare object where the
    array would have had a single element (the site functions endpoint does this).

    `allow_missing` defaults to False for the same reason as in paginated_get: the result goes
    straight to a cleanup job as the exhaustive set of live resources. Netlify answers an empty
    array, not a 404, for a site that simply has none of a given resource, so no caller in this
    module needs the tolerant path.

    :param api_session: Authenticated requests session.
    :param url: Full URL of the API endpoint.
    :param params: Query parameters.
    :param result_key: Envelope key holding the array, when the endpoint uses one.
    :param allow_missing: When True, a 404 returns an empty list instead of raising.
    :return: The collection.
    """
    response = api_session.get(url, params=params, timeout=_TIMEOUT)
    if response.status_code == 404 and allow_missing:
        logger.debug("Netlify returned 404 for %s, treating as empty.", url)
        return []
    _warn_if_rate_limit_low(response)
    response.raise_for_status()

    data = response.json()
    if data is None:
        return []
    # The site functions endpoint answers `200 {}` for a site with no functions, so an empty
    # object means an empty collection rather than a one-element one. Handled explicitly: falling
    # through to the bare-object branch below would return a phantom `[{}]` bundle that only
    # happens to be harmless because every caller reads its members with .get().
    if data == {}:
        return []
    if result_key is not None:
        # Strict access: surface an endpoint/key mismatch instead of silently handing an empty
        # list to a cleanup job that would then delete everything.
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a JSON object with key '{result_key}' from {url} but got "
                f"{type(data).__name__}",
            )
        return data[result_key]
    if isinstance(data, dict):
        return [data]
    return data


@timeit
def get_one(
    api_session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    allow_missing: bool = True,
) -> dict[str, Any] | None:
    """
    Fetch a single Netlify object.

    Unlike the collection helpers this defaults to tolerating absence, because the endpoints it
    serves are per-site singletons whose absence is a normal, observed state rather than a failed
    read: a site with no custom domain answers the TLS certificate endpoint with a JSON `null`.
    A caller still has to decide what an absent object means for its cleanup.

    :param api_session: Authenticated requests session.
    :param url: Full URL of the API endpoint.
    :param params: Query parameters.
    :param allow_missing: When True, a 404 or a JSON `null` body returns None.
    :return: The object, or None when it does not exist.
    """
    response = api_session.get(url, params=params, timeout=_TIMEOUT)
    if response.status_code == 404 and allow_missing:
        logger.debug("Netlify returned 404 for %s, treating as absent.", url)
        return None
    _warn_if_rate_limit_low(response)
    response.raise_for_status()
    data = response.json()
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object from {url} but got {type(data).__name__}",
        )
    return data
