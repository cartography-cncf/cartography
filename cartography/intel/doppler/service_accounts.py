from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.doppler.util import paginated_get
from cartography.models.doppler.service_account import DopplerServiceAccountSchema
from cartography.models.doppler.service_account_identity import (
    DopplerServiceAccountIdentitySchema,
)
from cartography.models.doppler.service_account_token import (
    DopplerServiceAccountTokenSchema,
)
from cartography.util import timeit


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    accounts, tokens, identities = get(api_session, common_job_parameters["BASE_URL"])
    accounts = transform(accounts)
    load_service_accounts(
        neo4j_session,
        accounts,
        tokens,
        identities,
        common_job_parameters["WORKPLACE_ID"],
        common_job_parameters["UPDATE_TAG"],
    )
    cleanup(neo4j_session, common_job_parameters)


@timeit
def get(
    api_session: requests.Session,
    base_url: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accounts = paginated_get(
        api_session, f"{base_url}/workplace/service_accounts", "service_accounts"
    )
    tokens: list[dict[str, Any]] = []
    identities: list[dict[str, Any]] = []
    for account in accounts:
        slug = account["slug"]
        base = f"{base_url}/workplace/service_accounts/service_account/{slug}"
        for token in paginated_get(api_session, f"{base}/tokens", "api_tokens"):
            token["service_account_slug"] = slug
            tokens.append(token)
        for identity in paginated_get(api_session, f"{base}/identities", "identities"):
            identity["service_account_slug"] = slug
            identities.append(identity)
    return accounts, tokens, identities


def transform(accounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for account in accounts:
        role = account.get("workplace_role") or {}
        account["workplace_role"] = role.get("identifier")
    return accounts


@timeit
def load_service_accounts(
    neo4j_session: neo4j.Session,
    accounts: list[dict[str, Any]],
    tokens: list[dict[str, Any]],
    identities: list[dict[str, Any]],
    workplace_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        DopplerServiceAccountSchema(),
        accounts,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )
    load(
        neo4j_session,
        DopplerServiceAccountTokenSchema(),
        tokens,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )
    load(
        neo4j_session,
        DopplerServiceAccountIdentitySchema(),
        identities,
        lastupdated=update_tag,
        WORKPLACE_ID=workplace_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(DopplerServiceAccountSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(
        DopplerServiceAccountTokenSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        DopplerServiceAccountIdentitySchema(), common_job_parameters
    ).run(neo4j_session)
