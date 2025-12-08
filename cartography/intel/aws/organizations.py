import logging
from typing import Dict

import boto3
import botocore.exceptions
import neo4j

from cartography.client.core.tx import run_write_query
from cartography.intel.aws.iam import sync_root_principal
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_account_from_arn(arn: str) -> str:
    # TODO use policyuniverse to parse ARN?
    return arn.split(":")[4]


def get_caller_identity(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client("sts")
    return client.get_caller_identity()


def get_current_aws_account_id(boto3_session: boto3.session.Session) -> Dict:
    return get_caller_identity(boto3_session)["Account"]


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


def load_aws_accounts(
    neo4j_session: neo4j.Session,
    aws_accounts: Dict,
    aws_update_tag: int,
    common_job_parameters: Dict,
) -> None:
    query = """
    MERGE (aa:AWSAccount{id: $ACCOUNT_ID})
    ON CREATE SET aa.firstseen = timestamp()
    SET aa.lastupdated = $aws_update_tag, aa.name = $ACCOUNT_NAME, aa.inscope=true
    REMOVE aa.foreign
    """
    for account_name, account_id in aws_accounts.items():
        root_arn = f"arn:aws:iam::{account_id}:root"
        run_write_query(
            neo4j_session,
            query,
            ACCOUNT_ID=account_id,
            ACCOUNT_NAME=account_name,
            RootArn=root_arn,
            aws_update_tag=aws_update_tag,
        )
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
