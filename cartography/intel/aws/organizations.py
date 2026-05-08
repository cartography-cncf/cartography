import logging
from typing import Any
from typing import Dict
from typing import Iterable

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.iam import sync_root_principal
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.organization import AWSAccountOrganizationIdSchema
from cartography.models.aws.organization import AWSAccountSchema
from cartography.models.aws.organization import AWSOrganizationAccountSchema
from cartography.models.aws.organization import AWSOrganizationSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_account_from_arn(arn: str) -> str:
    # TODO use policyuniverse to parse ARN?
    return arn.split(":")[4]


def get_caller_identity(boto3_session: boto3.session.Session) -> Dict:
    client = create_boto3_client(boto3_session, "sts")
    return client.get_caller_identity()


def get_current_aws_account_id(boto3_session: boto3.session.Session) -> Dict:
    return get_caller_identity(boto3_session)["Account"]


def get_aws_organization(organizations_client: Any) -> dict[str, Any]:
    return organizations_client.describe_organization()["Organization"]


def get_aws_organization_accounts(organizations_client: Any) -> list[dict[str, Any]]:
    paginator = organizations_client.get_paginator("list_accounts")
    accounts: list[dict[str, Any]] = []
    for page in paginator.paginate():
        accounts.extend(page["Accounts"])
    return accounts


def _get_account_state(account: dict[str, Any]) -> str | None:
    return account.get("State") or account.get("Status")


def _is_active_account(account: dict[str, Any]) -> bool:
    return _get_account_state(account) == "ACTIVE"


def transform_aws_organization(
    organization: dict[str, Any],
    account_ids: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "id": organization["Id"],
        "arn": organization.get("Arn"),
        "feature_set": organization.get("FeatureSet"),
        "management_account_arn": organization.get("MasterAccountArn"),
        "management_account_id": organization.get("MasterAccountId"),
        "management_account_email": organization.get("MasterAccountEmail"),
        "account_ids": list(account_ids),
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
                "status": account.get("Status"),
                "joined_method": account.get("JoinedMethod"),
                "joined_timestamp": account.get("JoinedTimestamp"),
                "org_id": organization_id,
            }
        )
    return transformed


def get_aws_account_default(boto3_session: boto3.session.Session) -> Dict:
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


def get_aws_accounts_from_botocore_config(boto3_session: boto3.session.Session) -> Dict:
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
        inscope=True,
    )


def load_aws_account_organization_ids(
    neo4j_session: neo4j.Session,
    aws_accounts: Iterable[dict[str, Any]],
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSAccountOrganizationIdSchema(),
        list(aws_accounts),
        lastupdated=aws_update_tag,
    )


def load_aws_accounts(
    neo4j_session: neo4j.Session,
    aws_accounts: Dict,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    account_data = [
        {
            "id": account_id,
            "name": account_name,
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
    accounts: Dict,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    load_aws_accounts(neo4j_session, accounts, update_tag, common_job_parameters)


def load_aws_organization(
    neo4j_session: neo4j.Session,
    organization: dict[str, Any],
    update_tag: int,
    sync_account_id: str,
    account_ids: Iterable[str] = (),
) -> None:
    load(
        neo4j_session,
        AWSOrganizationSchema(),
        [transform_aws_organization(organization, account_ids)],
        lastupdated=update_tag,
        AWS_ID=sync_account_id,
    )


def cleanup_aws_account_organization_memberships(
    neo4j_session: neo4j.Session,
    update_tag: int,
    sync_account_id: str,
) -> None:
    GraphJob.from_node_schema(
        AWSOrganizationSchema(),
        {"UPDATE_TAG": update_tag, "AWS_ID": sync_account_id},
    ).run(neo4j_session)


@timeit
def sync_aws_organization(
    neo4j_session: neo4j.Session,
    organizations_client: Any,
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
) -> None:
    organization = get_aws_organization(organizations_client)
    organization_id = organization["Id"]

    try:
        raw_accounts = get_aws_organization_accounts(organizations_client)
    except botocore.exceptions.ClientError:
        logger.warning(
            "Unable to list AWS Organization accounts; linking current account %s to organization %s only.",
            current_aws_account_id,
            organization_id,
            exc_info=True,
        )
        load_aws_account_organization_ids(
            neo4j_session,
            [{"id": current_aws_account_id, "org_id": organization_id}],
            update_tag,
        )
        load_aws_organization(
            neo4j_session,
            organization,
            update_tag,
            current_aws_account_id,
            [current_aws_account_id],
        )
        return

    organization_accounts = transform_aws_organization_accounts(
        (account for account in raw_accounts if _is_active_account(account)),
        organization_id,
    )
    load_aws_account_nodes_from_organization(
        neo4j_session,
        organization_accounts,
        update_tag,
    )
    for account in organization_accounts:
        sync_root_principal(
            neo4j_session,
            account["id"],
            update_tag,
        )
    load_aws_organization(
        neo4j_session,
        organization,
        update_tag,
        current_aws_account_id,
        [account["id"] for account in organization_accounts],
    )
    cleanup_aws_account_organization_memberships(
        neo4j_session,
        update_tag,
        current_aws_account_id,
    )
