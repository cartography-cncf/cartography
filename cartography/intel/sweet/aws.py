import logging
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.sweet import api
from cartography.models.sweet.aws import SweetAWSAccountSchema
from cartography.models.sweet.aws import SweetAWSOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_accounts(
    session: requests.Session,
    api_url: str,
) -> list[dict[str, Any]]:
    return api.get_list(session, api_url, "/v1/aws/account")


@timeit
def get_organizations(
    session: requests.Session,
    api_url: str,
) -> list[dict[str, Any]]:
    return api.get_list(session, api_url, "/v1/aws/organization")


def _connection_id(tenant_id: str, account_id: str) -> str:
    # One AWS account can be connected to more than one Sweet tenant, and each
    # connection has its own role, regions, and enabled state.
    return f"{tenant_id}:{account_id}"


def transform_accounts(
    raw_accounts: list[dict[str, Any]],
    tenant_id: str,
) -> list[dict[str, Any]]:
    # The external ID guards the cross-account role against confused-deputy use,
    # so it is deliberately not stored in the graph.
    return [
        {
            "id": _connection_id(tenant_id, account["accountId"]),
            "account_id": account["accountId"],
            "role_arn": account.get("roleArn"),
            "regions": account.get("regions"),
            "enabled": account.get("enabled"),
        }
        for account in raw_accounts
    ]


def transform_organizations(
    raw_organizations: list[dict[str, Any]],
    tenant_id: str,
) -> list[dict[str, Any]]:
    return [
        {
            "id": _connection_id(tenant_id, organization["accountId"]),
            "management_account_id": organization["accountId"],
            "role_arn": organization.get("roleArn"),
            "regions": organization.get("regions"),
            "enabled": organization.get("enabled"),
        }
        for organization in raw_organizations
    ]


@timeit
def load_accounts(
    neo4j_session: neo4j.Session,
    accounts: list[dict[str, Any]],
    organizations: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        SweetAWSAccountSchema(),
        accounts,
        lastupdated=update_tag,
        SWEET_TENANT_ID=tenant_id,
    )
    load(
        neo4j_session,
        SweetAWSOrganizationSchema(),
        organizations,
        lastupdated=update_tag,
        SWEET_TENANT_ID=tenant_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    GraphJob.from_node_schema(SweetAWSAccountSchema(), common_job_parameters).run(
        neo4j_session,
    )
    GraphJob.from_node_schema(
        SweetAWSOrganizationSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    session: requests.Session,
    api_url: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw_accounts = get_accounts(session, api_url)
    raw_organizations = get_organizations(session, api_url)
    logger.info(
        "Syncing %d Sweet AWS account and %d AWS organization connections.",
        len(raw_accounts),
        len(raw_organizations),
    )
    load_accounts(
        neo4j_session,
        transform_accounts(raw_accounts, tenant_id),
        transform_organizations(raw_organizations, tenant_id),
        tenant_id,
        update_tag,
    )
    cleanup(neo4j_session, common_job_parameters)
