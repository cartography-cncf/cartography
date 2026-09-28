import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.helpers import normalize_email_for_matching
from cartography.intel.github.util import fetch_page
from cartography.intel.github.util import get_retry_sleep_seconds_for_http_error
from cartography.intel.github.util import handle_rate_limit_sleep
from cartography.intel.github.util import sleep_with_jitter
from cartography.models.github.external_identities import GitHubExternalIdentitySchema
from cartography.util import timeit

logger = logging.getLogger(__name__)
_MAX_PAGE_ATTEMPTS = 5


class ExternalIdentitySnapshotError(RuntimeError):
    """The provider did not return a complete identity snapshot."""


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
    for attempt in range(_MAX_PAGE_ATTEMPTS):
        delay = 2 ** (attempt + 1)
        try:
            handle_rate_limit_sleep(token, api_url)
            response = fetch_page(
                token, api_url, organization, EXTERNAL_IDENTITIES_QUERY, cursor
            )
        except requests.HTTPError as error:
            retry_delay = get_retry_sleep_seconds_for_http_error(error, attempt + 1)
            if retry_delay is None or attempt + 1 == _MAX_PAGE_ATTEMPTS:
                raise
            delay = retry_delay
        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ):
            if attempt + 1 == _MAX_PAGE_ATTEMPTS:
                raise
        else:
            errors = response.get("errors") or []
            if (
                not errors
                or attempt + 1 == _MAX_PAGE_ATTEMPTS
                or not all(
                    error.get("type") == "RATE_LIMITED"
                    or error.get("message") == "timedout"
                    for error in errors
                )
            ):
                return response
            if any(error.get("type") == "RATE_LIMITED" for error in errors):
                # The next attempt checks the primary reset; back off here
                # for secondary limits, which /rate_limit cannot report.
                delay = 60 * 2**attempt
        logger.warning(
            "Retrying GitHub external identity page for %s in %s seconds (attempt %d/%d).",
            organization,
            delay,
            attempt + 2,
            _MAX_PAGE_ATTEMPTS,
        )
        sleep_with_jitter(delay)
    raise RuntimeError("Unreachable: final attempt returns or raises")


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
            raise ExternalIdentitySnapshotError(
                f"GitHub external identity query failed for {organization}; "
                "preserving previously synced identities."
            )
        org = response["data"]["organization"]
        if org is None:
            raise ExternalIdentitySnapshotError(
                f"GitHub organization {organization} was not returned"
            )
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
            raise ExternalIdentitySnapshotError(
                "GitHub external identity pagination did not advance"
            )
        cursor = next_cursor


def transform_external_identities(
    identities: list[dict[str, Any]], org_url: str
) -> list[dict[str, Any]]:
    data = []
    for identity in identities:
        name_id = (identity.get("samlIdentity") or {}).get("nameId")
        data.append(
            {
                "id": f"{org_url}|{identity['id']}",
                "saml_name_id": name_id,
                "saml_name_id_normalized": normalize_email_for_matching(name_id),
                "user_url": (identity.get("user") or {}).get("url"),
            }
        )
    return data


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    token: Any,
    api_url: str,
    organization: str,
) -> None:
    logger.info("Syncing GitHub external identities for %s", organization)
    try:
        snapshot = get_external_identities(token, api_url, organization)
    except (requests.RequestException, ExternalIdentitySnapshotError) as error:
        logger.warning(
            "Skipping GitHub external identities for %s after %s; "
            "preserving previously synced identities.",
            organization,
            type(error).__name__,
        )
        return
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
