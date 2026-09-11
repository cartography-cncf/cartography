import logging
import time
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.github.util import _extract_error_message
from cartography.intel.github.util import _get_retry_sleep_seconds_for_http_error
from cartography.intel.github.util import _TRANSIENT_STATUS_CODES
from cartography.intel.github.util import fetch_page
from cartography.models.github.external_identities import GitHubExternalIdentitySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

EXTERNAL_IDENTITIES_QUERY = """
query($login: String!, $cursor: String) {
    organization(login: $login) {
        url
        samlIdentityProvider {
            externalIdentities(first: 100, after: $cursor) {
                nodes {
                    id
                    samlIdentity { nameId }
                    user { url }
                }
                pageInfo { endCursor hasNextPage }
            }
        }
    }
}
"""


def _fetch_identity_page(
    token: Any, api_url: str, organization: str, cursor: str | None
) -> dict[str, Any]:
    for attempt in range(5):
        delay = 2 ** (attempt + 1)
        try:
            response = fetch_page(
                token, api_url, organization, EXTERNAL_IDENTITIES_QUERY, cursor
            )
        except requests.HTTPError as error:
            http_response = error.response
            if http_response is None:
                raise
            rate_limited = http_response.status_code == 403 and (
                http_response.headers.get("x-ratelimit-remaining") == "0"
                or "retry-after" in http_response.headers
                or "secondary rate limit"
                in _extract_error_message(http_response).lower()
                or "abuse detection" in _extract_error_message(http_response).lower()
            )
            if (
                http_response.status_code not in _TRANSIENT_STATUS_CODES
                and not rate_limited
            ):
                raise
            delay = _get_retry_sleep_seconds_for_http_error(error, attempt + 1)
            # Do not retry earlier than GitHub permits or let a server-provided
            # reset time hold this optional stage indefinitely.
            if attempt == 4 or delay > 300:
                raise
        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ):
            if attempt == 4:
                raise
        else:
            errors = response.get("errors") or []
            if (
                not errors
                or attempt == 4
                or not all(
                    error.get("type") == "RATE_LIMITED"
                    or error.get("message") == "timedout"
                    for error in errors
                )
            ):
                return response
            if any(error.get("type") == "RATE_LIMITED" for error in errors):
                delay = 60
        logger.warning(
            "Retrying GitHub external identity page for %s in %s seconds (attempt %d/5).",
            organization,
            delay,
            attempt + 2,
        )
        time.sleep(delay)
    raise AssertionError("Unreachable: final attempt returns or raises")


def get_external_identities(
    token: Any, api_url: str, organization: str
) -> tuple[list[dict[str, Any]], str] | None:
    # Complete the snapshot before writing: a denied later page must not remove
    # identities or their account links from a previous successful sync.
    identities: list[dict[str, Any]] = []
    cursor = None
    while True:
        response = _fetch_identity_page(token, api_url, organization, cursor)
        errors = response.get("errors")
        if errors:
            if all(
                error.get("type") in {"FORBIDDEN", "INSUFFICIENT_SCOPES"}
                for error in errors
            ):
                logger.warning(
                    "Skipping GitHub external identities for %s: access denied; "
                    "preserving previously synced identities.",
                    organization,
                )
                return None
            raise RuntimeError(
                f"GitHub external identity query failed for {organization}; "
                "preserving previously synced identities."
            )
        org = response["data"]["organization"]
        if org is None:
            raise RuntimeError(f"GitHub organization {organization} was not returned")
        provider = org["samlIdentityProvider"]
        if provider is None:
            # This nullable field is visible only to authorized credentials;
            # absence alone cannot establish that SAML was disabled.
            logger.info(
                "GitHub SAML provider unavailable for %s; preserving previously synced identities.",
                organization,
            )
            return None
        connection = provider["externalIdentities"]
        identities.extend(connection["nodes"])
        page_info = connection["pageInfo"]
        if not page_info["hasNextPage"]:
            return identities, org["url"]
        next_cursor = page_info["endCursor"]
        if not next_cursor or next_cursor == cursor:
            raise RuntimeError("GitHub external identity pagination did not advance")
        cursor = next_cursor


def transform_external_identities(
    identities: list[dict[str, Any]], org_url: str
) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{org_url}|{identity['id']}",
            "saml_name_id": (identity.get("samlIdentity") or {}).get("nameId"),
            "user_url": (identity.get("user") or {}).get("url"),
        }
        for identity in identities
    ]


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    token: Any,
    api_url: str,
    organization: str,
) -> None:
    logger.info("Syncing GitHub external identities for %s", organization)
    snapshot = get_external_identities(token, api_url, organization)
    if snapshot is None:
        return
    identities, org_url = snapshot
    data = transform_external_identities(identities, org_url)
    load(
        neo4j_session,
        GitHubExternalIdentitySchema(),
        data,
        lastupdated=common_job_parameters["UPDATE_TAG"],
        org_url=org_url,
    )
    GraphJob.from_node_schema(
        GitHubExternalIdentitySchema(),
        {**common_job_parameters, "org_url": org_url},
    ).run(neo4j_session)
    logger.info("Synced %d GitHub external identities for %s", len(data), organization)
