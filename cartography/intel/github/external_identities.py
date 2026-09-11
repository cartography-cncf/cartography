import logging
from typing import Any

import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
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


def get_external_identities(
    token: Any, api_url: str, organization: str
) -> tuple[list[dict[str, Any]], str] | None:
    # Complete the snapshot before writing: a denied later page must not remove
    # identities or their account links from a previous successful sync.
    identities: list[dict[str, Any]] = []
    cursor = None
    while True:
        response = fetch_page(
            token, api_url, organization, EXTERNAL_IDENTITIES_QUERY, cursor
        )
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
