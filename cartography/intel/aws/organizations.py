import logging
import time
from typing import Dict

import boto3
import botocore.exceptions
import neo4j

from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_account_from_arn(arn: str) -> str:
    # TODO use policyuniverse to parse ARN?
    return arn.split(":")[4]


def get_organization(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client('organizations')
    try:
        return client.describe_organization()['Organization']
    except Exception as e:
        logger.info(f"error to get organization details- {e}")
        return


def get_caller_identity(boto3_session: boto3.session.Session) -> Dict:
    client = boto3_session.client('sts')
    return client.get_caller_identity()


def get_current_aws_account_id(boto3_session: boto3.session.Session) -> Dict:
    return get_caller_identity(boto3_session)['Account']


def get_aws_account_default(boto3_session: boto3.session.Session) -> Dict:
    try:
        return {boto3_session.profile_name: get_current_aws_account_id(boto3_session)}
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        logger.debug("Error occurred getting default AWS account number.", exc_info=True)
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
        if profile_name == 'default':
            logger.debug("Skipping AWS profile 'default'.")
            continue
        try:
            profile_boto3_session = boto3.Session(profile_name=profile_name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            logger.debug("Error occurred calling boto3.Session() with profile_name '%s'.", profile_name, exc_info=True)
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
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
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
    neo4j_session: neo4j.Session, aws_accounts: Dict, aws_update_tag: int, organization: Dict,
    common_job_parameters: Dict,
) -> None:
    query = """
    MERGE (w:CloudanixWorkspace{id: $WORKSPACE_ID})
    ON CREATE SET w.firstseen = timestamp()
    SET w.lastupdated = $UPDATE_TAG,
    w.name = $WORKSPACE_NAME,
    w.account_id = $ACCOUNT_ID
    WITH w
    MERGE (org:AWSOrganization{id: $organizationId})
    ON CREATE SET org.firstseen = timestamp()
    SET org.lastupdated = $UPDATE_TAG,
    org.arn = $organizationArn,
    org.masterAccountArn = $masterAccountArn,
    org.masterAccountId = $masterAccountId,
    org.masterAccountEmail = $masterAccountEmail,
    org.isSystemGenerated = $isSystemGenerated
    WITH w, org
    MERGE (w)-[o:OWNER]->(org)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UPDATE_TAG
    WITH org
    MERGE (aa:AWSAccount{id: $ACCOUNT_ID})
    ON CREATE SET aa.firstseen = timestamp()
    SET aa.lastupdated = $UPDATE_TAG,
    aa.region = $region,
    aa.name = $ACCOUNT_NAME
    WITH aa, org
    MERGE (org)-[o:OWNER]->(aa)
    ON CREATE SET o.firstseen = timestamp()
    SET o.lastupdated = $UPDATE_TAG
    MERGE (root:AWSPrincipal{arn: $RootArn})
    ON CREATE SET root.firstseen = timestamp(), root.type = 'AWS'
    SET root.lastupdated = $UPDATE_TAG
    WITH aa, root
    MERGE (aa)-[r:RESOURCE]->(root)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $UPDATE_TAG;
    """
    for account_name, account_id in aws_accounts.items():
        root_arn = f'arn:aws:iam::{account_id}:root'
        neo4j_session.run(
            query,
            WORKSPACE_ID=common_job_parameters['WORKSPACE_ID'],
            WORKSPACE_NAME=common_job_parameters['WORKSPACE_NAME'],
            ACCOUNT_ID=account_id,
            ACCOUNT_NAME=account_name,
            RootArn=root_arn,
            region="global",
            UPDATE_TAG=aws_update_tag,
            organizationId=organization.get("Id"),
            isSystemGenerated=organization.get("IsSystemGenerated", None),
            organizationArn=organization.get("Arn", None),
            masterAccountArn=organization.get("MasterAccountArn", None),
            masterAccountId=organization.get("MasterAccountId", None),
            masterAccountEmail=organization.get("MasterAccountEmail", None),
        )

        cleanup(neo4j_session, account_id, common_job_parameters)


@timeit
def cleanup(neo4j_session: neo4j.Session, account_id: str, common_job_parameters: Dict) -> None:
    common_job_parameters['AWS_ID'] = account_id
    run_cleanup_job('aws_account_cleanup.json', neo4j_session, common_job_parameters)


@timeit
def sync(neo4j_session: neo4j.Session, accounts: Dict, organization: Dict, update_tag: int, common_job_parameters: Dict) -> None:
    tic = time.perf_counter()
    logger.info("Syncing AWS Organizations")
    load_aws_accounts(neo4j_session, accounts, update_tag, organization, common_job_parameters)
    toc = time.perf_counter()
    logger.info(f"Time to process AWS Organizations ({len(accounts)} accounts): {toc - tic:0.4f} seconds")
