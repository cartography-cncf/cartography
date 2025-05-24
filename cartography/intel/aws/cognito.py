import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.cognito.user_pools import CognitoUserPoolSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_list_user_pools(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "cognito-idp",
        region_name=region,
        config=get_botocore_config(),
    )

    paginator = client.get_paginator("list_user_pools")
    user_pools_description = []
    for page in paginator.paginate(MaxResults=60):
        for user_pool in page["UserPools"]:
            user_pool_description = client.describe_user_pool(
                UserPoolId=user_pool["Id"]
            )
            user_pools_description.append(user_pool_description)
    return user_pools_description


@timeit
def load_user_pools(
    neo4j_session: neo4j.Session,
    user_pools_data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Cognito UserPools {len(user_pools_data)}  for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CognitoUserPoolSchema(),
        user_pools_data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def transform_user_pool_data(user_pools: List[Dict]) -> List[Dict]:
    user_pools_extracted = []
    for user_pool in user_pools:
        user_pools_extracted.append(user_pool["UserPool"])
    return user_pools_extracted


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running Cognito cleanup job.")
    cleanup_job = GraphJob.from_node_schema(
        CognitoUserPoolSchema(), common_job_parameters
    )
    cleanup_job.run(neo4j_session)


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict[str, Any],
) -> None:
    for region in regions:
        logger.info(
            f"Syncing Cognito for region '{region}' in account '{current_aws_account_id}'.",
        )

        user_pools_list = get_list_user_pools(boto3_session, region)
        if not user_pools_list:
            continue

        user_pools_data = transform_user_pool_data(user_pools_list)
        load_user_pools(
            neo4j_session,
            user_pools_data,
            region,
            current_aws_account_id,
            update_tag,
        )

    cleanup(neo4j_session, common_job_parameters)
