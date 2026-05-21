import logging
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Iterable

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import run_write_query
from cartography.graph.job import GraphJob
from cartography.intel.aws.iam import sync_root_principal
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.account import AWSAccountSchema
from cartography.models.aws.account import AWSOrganizationAccountSchema
from cartography.models.aws.organization import AWSOrganizationalUnitSchema
from cartography.models.aws.organization import AWSOrganizationRootSchema
from cartography.models.aws.organization import AWSOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


class AWSOrganizationSyncStatus(str, Enum):
    """Structured outcome for one AWS Organizations sync attempt."""

    # A complete hierarchy was enumerated, loaded, and cleaned up for this org.
    SYNCED = "SYNCED"
    # This org was already successfully synced earlier in the current run.
    ALREADY_SYNCED = "ALREADY_SYNCED"
    # The account is not a member of an AWS Organization.
    NOT_IN_ORG = "NOT_IN_ORG"
    # The account cannot describe or enumerate AWS Organizations data.
    ACCESS_DENIED = "ACCESS_DENIED"
    # Some non-permission error prevented complete hierarchy enumeration.
    INCOMPLETE = "INCOMPLETE"


@dataclass(frozen=True)
class AWSOrganizationSyncResult:
    account_id: str
    status: AWSOrganizationSyncStatus
    organization_id: str | None = None
    error_code: str | None = None


def _get_client_error_code(error: botocore.exceptions.ClientError) -> str | None:
    return error.response.get("Error", {}).get("Code")


def _is_access_denied_error(error: botocore.exceptions.ClientError) -> bool:
    return _get_client_error_code(error) in {"AccessDenied", "AccessDeniedException"}


def get_aws_organization_sync_result_from_client_error(
    account_id: str,
    error: botocore.exceptions.ClientError,
    organization_id: str | None = None,
) -> AWSOrganizationSyncResult:
    error_code = _get_client_error_code(error)
    if error_code == "AWSOrganizationsNotInUseException":
        return AWSOrganizationSyncResult(
            account_id,
            AWSOrganizationSyncStatus.NOT_IN_ORG,
            organization_id=organization_id,
            error_code=error_code,
        )
    if _is_access_denied_error(error):
        return AWSOrganizationSyncResult(
            account_id,
            AWSOrganizationSyncStatus.ACCESS_DENIED,
            organization_id=organization_id,
            error_code=error_code,
        )
    return AWSOrganizationSyncResult(
        account_id,
        AWSOrganizationSyncStatus.INCOMPLETE,
        organization_id=organization_id,
        error_code=error_code,
    )


def get_account_from_arn(arn: str) -> str:
    # TODO use policyuniverse to parse ARN?
    return arn.split(":")[4]


def get_caller_identity(boto3_session: boto3.session.Session) -> dict[str, Any]:
    client = create_boto3_client(boto3_session, "sts")
    return client.get_caller_identity()


def get_current_aws_account_id(boto3_session: boto3.session.Session) -> str:
    return get_caller_identity(boto3_session)["Account"]


def get_aws_organization(organizations_client: Any) -> dict[str, Any]:
    return organizations_client.describe_organization()["Organization"]


def _paginate_aws_organizations(
    organizations_client: Any,
    paginator_name: str,
    result_key: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    paginator = organizations_client.get_paginator(paginator_name)
    results: list[dict[str, Any]] = []
    for page in paginator.paginate(**kwargs):
        results.extend(page[result_key])
    return results


def get_aws_organization_roots(
    organizations_client: Any,
) -> list[dict[str, Any]]:
    return _paginate_aws_organizations(organizations_client, "list_roots", "Roots")


def get_aws_organizational_units_for_parent(
    organizations_client: Any,
    parent_id: str,
) -> list[dict[str, Any]]:
    return _paginate_aws_organizations(
        organizations_client,
        "list_organizational_units_for_parent",
        "OrganizationalUnits",
        ParentId=parent_id,
    )


def get_aws_organization_accounts_for_parent(
    organizations_client: Any,
    parent_id: str,
) -> list[dict[str, Any]]:
    return _paginate_aws_organizations(
        organizations_client,
        "list_accounts_for_parent",
        "Accounts",
        ParentId=parent_id,
    )


def _get_account_state(account: dict[str, Any]) -> str | None:
    return account.get("State") or account.get("Status")


def _is_active_account(account: dict[str, Any]) -> bool:
    return _get_account_state(account) == "ACTIVE"


def _make_org_scoped_id(organization_id: str, resource_id: str) -> str:
    return f"{organization_id}/{resource_id}"


def transform_aws_organization(
    organization: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": organization["Id"],
        "arn": organization.get("Arn"),
        "feature_set": organization.get("FeatureSet"),
        "management_account_arn": organization.get("MasterAccountArn"),
        "management_account_id": organization.get("MasterAccountId"),
        "management_account_email": organization.get("MasterAccountEmail"),
    }


def transform_aws_organization_accounts(
    accounts: Iterable[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed = []
    for account in accounts:
        transformed.append(
            {
                "id": account["Id"],
                "arn": account.get("Arn"),
                "email": account.get("Email"),
                "name": account.get("Name"),
                "state": _get_account_state(account),
                # TODO: Remove status after AWS retires it on 2026-09-09.
                "status": account.get("Status"),
                "joined_method": account.get("JoinedMethod"),
                "joined_timestamp": account.get("JoinedTimestamp"),
                "org_id": organization_id,
            }
        )
    return transformed


def transform_aws_organization_roots(
    roots: Iterable[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed = []
    for root in roots:
        transformed.append(
            {
                "id": _make_org_scoped_id(organization_id, root["Id"]),
                "root_id": root["Id"],
                "arn": root.get("Arn"),
                "name": root.get("Name"),
                "org_id": organization_id,
                "child_ou_ids": [
                    _make_org_scoped_id(organization_id, child_ou_id)
                    for child_ou_id in root.get("child_ou_ids", [])
                ],
                "account_ids": root.get("account_ids", []),
            }
        )
    return transformed


def transform_aws_organizational_units(
    organizational_units: Iterable[dict[str, Any]],
    organization_id: str,
) -> list[dict[str, Any]]:
    transformed = []
    for organizational_unit in organizational_units:
        transformed.append(
            {
                "id": _make_org_scoped_id(organization_id, organizational_unit["Id"]),
                "ou_id": organizational_unit["Id"],
                "arn": organizational_unit.get("Arn"),
                "name": organizational_unit.get("Name"),
                "org_id": organization_id,
                "root_id": _make_org_scoped_id(
                    organization_id,
                    organizational_unit["root_id"],
                ),
                "parent_root_id": (
                    _make_org_scoped_id(
                        organization_id,
                        organizational_unit["parent_root_id"],
                    )
                    if organizational_unit.get("parent_root_id")
                    else None
                ),
                "parent_ou_id": (
                    _make_org_scoped_id(
                        organization_id,
                        organizational_unit["parent_ou_id"],
                    )
                    if organizational_unit.get("parent_ou_id")
                    else None
                ),
                "child_ou_ids": [
                    _make_org_scoped_id(organization_id, child_ou_id)
                    for child_ou_id in organizational_unit.get("child_ou_ids", [])
                ],
                "account_ids": organizational_unit.get("account_ids", []),
            }
        )
    return transformed


def get_aws_organization_hierarchy(
    organizations_client: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    roots = [dict(root) for root in get_aws_organization_roots(organizations_client)]
    organizational_units: list[dict[str, Any]] = []
    accounts: list[dict[str, Any]] = []

    for root in roots:
        root_id = root["Id"]
        root["child_ou_ids"] = []
        root["account_ids"] = []

        queue: deque[tuple[str, str]] = deque([(root_id, "ROOT")])
        organizational_unit_by_id: dict[str, dict[str, Any]] = {}

        while queue:
            parent_id, parent_type = queue.popleft()
            child_ous = get_aws_organizational_units_for_parent(
                organizations_client,
                parent_id,
            )
            child_accounts = get_aws_organization_accounts_for_parent(
                organizations_client,
                parent_id,
            )
            active_child_account_ids = [
                account["Id"]
                for account in child_accounts
                if _is_active_account(account)
            ]
            accounts.extend(child_accounts)

            if parent_type == "ROOT":
                root["child_ou_ids"] = [ou["Id"] for ou in child_ous]
                root["account_ids"] = active_child_account_ids
            else:
                parent_ou = organizational_unit_by_id[parent_id]
                parent_ou["child_ou_ids"] = [ou["Id"] for ou in child_ous]
                parent_ou["account_ids"] = active_child_account_ids

            for child_ou in child_ous:
                child_ou_record = dict(child_ou)
                child_ou_record["root_id"] = root_id
                child_ou_record["parent_root_id"] = (
                    parent_id if parent_type == "ROOT" else None
                )
                child_ou_record["parent_ou_id"] = (
                    parent_id if parent_type == "ORGANIZATIONAL_UNIT" else None
                )
                child_ou_record["child_ou_ids"] = []
                child_ou_record["account_ids"] = []
                organizational_units.append(child_ou_record)
                organizational_unit_by_id[child_ou_record["Id"]] = child_ou_record
                queue.append((child_ou_record["Id"], "ORGANIZATIONAL_UNIT"))

    return roots, organizational_units, accounts


def get_aws_account_default(boto3_session: boto3.session.Session) -> dict[str, str]:
    try:
        return {boto3_session.profile_name: get_current_aws_account_id(boto3_session)}
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        logger.debug(
            "Error occurred getting default AWS account number.",
            exc_info=True,
        )
        logger.error(
            (
                "Unable to get AWS account number, an error occurred: '%s'. Make sure your AWS credentials are "
                "configured correctly, your AWS config file is valid, and your credentials have the SecurityAudit "
                "policy attached."
            ),
            e,
        )
        return {}


def get_aws_accounts_from_botocore_config(
    boto3_session: boto3.session.Session,
) -> dict[str, str]:
    d = {}
    for profile_name in boto3_session.available_profiles:
        if profile_name == "default":
            logger.debug("Skipping AWS profile 'default'.")
            continue
        try:
            profile_boto3_session = boto3.Session(profile_name=profile_name)
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            logger.debug(
                "Error occurred calling boto3.Session() with profile_name '%s'.",
                profile_name,
                exc_info=True,
            )
            logger.error(
                (
                    "Unable to initialize an AWS session using profile '%s', an error occurred: '%s'. Make sure your "
                    "AWS credentials are configured correctly, your AWS config file is valid, and your credentials "
                    "have the SecurityAudit policy attached."
                ),
                profile_name,
                e,
            )
            continue
        try:
            d[profile_name] = get_current_aws_account_id(profile_boto3_session)
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            logger.debug(
                "Error occurred getting AWS account number with profile_name '%s'.",
                profile_name,
                exc_info=True,
            )
            logger.error(
                (
                    "Unable to get AWS account number using profile '%s', an error occurred: '%s'. Make sure your AWS "
                    "credentials are configured correctly, your AWS config file is valid, and your credentials have "
                    "the SecurityAudit policy attached."
                ),
                profile_name,
                e,
            )
            continue
        logger.debug(
            "Discovered AWS account '%s' associated with configured profile '%s'.",
            d[profile_name],
            profile_name,
        )
    return d


def load_aws_account_nodes_from_config(
    neo4j_session: neo4j.Session,
    aws_accounts: Iterable[dict[str, Any]],
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSAccountSchema(),
        list(aws_accounts),
        lastupdated=aws_update_tag,
        inscope=True,
    )


def load_aws_account_nodes_from_organization(
    neo4j_session: neo4j.Session,
    aws_accounts: Iterable[dict[str, Any]],
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSOrganizationAccountSchema(),
        list(aws_accounts),
        lastupdated=aws_update_tag,
    )


def load_aws_accounts(
    neo4j_session: neo4j.Session,
    aws_accounts: dict[str, str],
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    account_data = [
        {
            "id": account_id,
            "name": account_name,
            "foreign": None,
        }
        for account_name, account_id in aws_accounts.items()
    ]
    load_aws_account_nodes_from_config(neo4j_session, account_data, aws_update_tag)
    for account_id in aws_accounts.values():
        # Every AWS account has a root principal
        sync_root_principal(
            neo4j_session,
            account_id,
            aws_update_tag,
        )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    accounts: dict[str, str],
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    load_aws_accounts(neo4j_session, accounts, update_tag, common_job_parameters)


def load_aws_organization(
    neo4j_session: neo4j.Session,
    organization: dict[str, Any],
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSOrganizationSchema(),
        [transform_aws_organization(organization)],
        lastupdated=update_tag,
    )


def load_aws_organization_roots(
    neo4j_session: neo4j.Session,
    roots: Iterable[dict[str, Any]],
    organization_id: str,
    update_tag: int,
) -> None:
    root_list = list(roots)
    if not root_list:
        return
    load(
        neo4j_session,
        AWSOrganizationRootSchema(),
        transform_aws_organization_roots(root_list, organization_id),
        lastupdated=update_tag,
        ORG_ID=organization_id,
    )


def load_aws_organizational_units(
    neo4j_session: neo4j.Session,
    organizational_units: Iterable[dict[str, Any]],
    organization_id: str,
    root_id: str,
    update_tag: int,
) -> None:
    organizational_unit_list = list(organizational_units)
    if not organizational_unit_list:
        return
    load(
        neo4j_session,
        AWSOrganizationalUnitSchema(),
        transform_aws_organizational_units(
            organizational_unit_list,
            organization_id,
        ),
        lastupdated=update_tag,
        ROOT_ID=root_id,
    )


def get_existing_aws_organization_root_ids(
    neo4j_session: neo4j.Session,
    organization_id: str,
) -> list[str]:
    return [
        record["root_id"]
        for record in neo4j_session.run(
            """
            MATCH (:AWSOrganization {id: $ORG_ID})-[:RESOURCE]->(root:AWSOrganizationRoot)
            RETURN root.id AS root_id
            """,
            ORG_ID=organization_id,
        )
    ]


def cleanup_aws_organization_hierarchy(
    neo4j_session: neo4j.Session,
    update_tag: int,
    organization_id: str,
    root_ids: Iterable[str],
) -> None:
    root_ids_to_cleanup = set(root_ids)
    root_ids_to_cleanup.update(
        get_existing_aws_organization_root_ids(
            neo4j_session,
            organization_id,
        )
    )
    for root_id in sorted(root_ids_to_cleanup):
        GraphJob.from_node_schema(
            AWSOrganizationalUnitSchema(),
            {"UPDATE_TAG": update_tag, "ROOT_ID": root_id},
        ).run(neo4j_session)
    GraphJob.from_node_schema(
        AWSOrganizationRootSchema(),
        {"UPDATE_TAG": update_tag, "ORG_ID": organization_id},
    ).run(neo4j_session)


def cleanup_stale_aws_account_organization_metadata(
    neo4j_session: neo4j.Session,
    organization_id: str,
    current_account_ids: Iterable[str],
    update_tag: int,
) -> None:
    run_write_query(
        neo4j_session,
        """
        MATCH (account:AWSAccount {org_id: $ORG_ID})
        WHERE NOT account.id IN $CURRENT_ACCOUNT_IDS
        SET account.arn = null,
            account.email = null,
            account.state = null,
            account.status = null,
            account.joined_method = null,
            account.joined_timestamp = null,
            account.org_id = null,
            account.lastupdated = $UPDATE_TAG
        """,
        ORG_ID=organization_id,
        CURRENT_ACCOUNT_IDS=list(current_account_ids),
        UPDATE_TAG=update_tag,
    )


@timeit
def sync_aws_organization(
    neo4j_session: neo4j.Session,
    organizations_client: Any,
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> AWSOrganizationSyncResult:
    try:
        organization = get_aws_organization(organizations_client)
    except botocore.exceptions.ClientError as e:
        result = get_aws_organization_sync_result_from_client_error(
            current_aws_account_id,
            e,
        )
        if result.status == AWSOrganizationSyncStatus.NOT_IN_ORG:
            logger.info(
                "The current account (%s) is not a member of an AWS Organization.",
                current_aws_account_id,
            )
            return result
        if result.status == AWSOrganizationSyncStatus.ACCESS_DENIED:
            logger.warning(
                "The current account (%s) doesn't have enough permissions to sync AWS Organizations hierarchy. "
                "AWS Organizations error code: %s.",
                current_aws_account_id,
                result.error_code,
                exc_info=True,
            )
            return result
        logger.warning(
            "Unable to describe AWS Organization for account %s; skipping AWS Organizations sync. "
            "AWS Organizations error code: %s.",
            current_aws_account_id,
            result.error_code,
            exc_info=True,
        )
        return result

    organization_id = organization["Id"]
    synced_organization_ids = common_job_parameters.setdefault(
        "_SYNCED_AWS_ORGANIZATION_IDS",
        [],
    )
    if organization_id in synced_organization_ids:
        logger.debug(
            "Skipping AWS Organizations sync for organization %s; it was already synced in this run.",
            organization_id,
        )
        return AWSOrganizationSyncResult(
            current_aws_account_id,
            AWSOrganizationSyncStatus.ALREADY_SYNCED,
            organization_id=organization_id,
        )

    try:
        roots, organizational_units, raw_accounts = get_aws_organization_hierarchy(
            organizations_client,
        )
    except botocore.exceptions.ClientError as e:
        result = get_aws_organization_sync_result_from_client_error(
            current_aws_account_id,
            e,
            organization_id=organization_id,
        )
        logger.warning(
            "Unable to enumerate AWS Organization hierarchy for organization %s; skipping AWS Organizations sync.",
            organization_id,
            exc_info=True,
        )
        return result

    organization_accounts = transform_aws_organization_accounts(
        raw_accounts,
        organization_id,
    )
    active_organization_accounts = [
        account for account in organization_accounts if account["state"] == "ACTIVE"
    ]
    load_aws_account_nodes_from_organization(
        neo4j_session,
        organization_accounts,
        update_tag,
    )
    for account in active_organization_accounts:
        sync_root_principal(
            neo4j_session,
            account["id"],
            update_tag,
        )
    load_aws_organization(neo4j_session, organization, update_tag)
    load_aws_organization_roots(
        neo4j_session,
        roots,
        organization_id,
        update_tag,
    )
    for root in roots:
        load_aws_organizational_units(
            neo4j_session,
            (
                organizational_unit
                for organizational_unit in organizational_units
                if organizational_unit["root_id"] == root["Id"]
            ),
            organization_id,
            _make_org_scoped_id(organization_id, root["Id"]),
            update_tag,
        )
    cleanup_aws_organization_hierarchy(
        neo4j_session,
        update_tag,
        organization_id,
        (_make_org_scoped_id(organization_id, root["Id"]) for root in roots),
    )
    cleanup_stale_aws_account_organization_metadata(
        neo4j_session,
        organization_id,
        (account["Id"] for account in raw_accounts),
        update_tag,
    )
    synced_organization_ids.append(organization_id)
    return AWSOrganizationSyncResult(
        current_aws_account_id,
        AWSOrganizationSyncStatus.SYNCED,
        organization_id=organization_id,
    )
