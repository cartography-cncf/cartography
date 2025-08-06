import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.cognito.identity_pool import CognitoIdentityPoolSchema
from cartography.models.aws.cognito.user_pool import CognitoUserPoolSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_identity_pools(
    boto3_session: boto3.Session, region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "cognito-identity", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("list_identity_pools")

    all_identity_pools = []

    for page in paginator.paginate(MaxResults=50):
        identity_pools = page.get("IdentityPools", [])
        all_identity_pools.extend(identity_pools)
    return all_identity_pools


@timeit
@aws_handle_regions
def get_identity_pool_roles(
    boto3_session: boto3.Session, identity_pools: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "cognito-identity", region_name=region, config=get_botocore_config()
    )
    all_identity_pool_details = []
    for identity_pool in identity_pools:
        response = client.get_identity_pool_roles(
            IdentityPoolId=identity_pool["IdentityPoolId"]
        )
        all_identity_pool_details.append(response)
    return all_identity_pool_details


@timeit
@aws_handle_regions
def get_user_pools(boto3_session: boto3.Session, region: str) -> List[Dict[str, Any]]:
    client = boto3_session.client(
        "cognito-idp", region_name=region, config=get_botocore_config()
    )
    paginator = client.get_paginator("list_user_pools")
    all_user_pools = []

    for page in paginator.paginate(MaxResults=50):
        user_pools = page.get("UserPools", [])
        all_user_pools.extend(user_pools)
    return all_user_pools


def transform_identity_pools(
    identity_pools: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    transformed_identity_pools = []
    for pool in identity_pools:
        transformed_pool = {
            "IdentityPoolId": pool["IdentityPoolId"],
            "Region": region,
            "Roles": list(pool.get("Roles", {}).values()),
        }
        transformed_identity_pools.append(transformed_pool)
    return transformed_identity_pools


def transform_user_pools(
    user_pools: List[Dict[str, Any]], region: str
) -> List[Dict[str, Any]]:
    transformed_user_pools = []
    for pool in user_pools:
        transformed_pool = {
            "Id": pool["Id"],
            "Region": region,
            "Name": pool["Name"],
            "Status": pool.get("Status"),
        }
        transformed_user_pools.append(transformed_pool)
    return transformed_user_pools


@timeit
def load_identity_pools(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Cognito Identity Pools {len(data)} for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CognitoIdentityPoolSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_user_pools(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    logger.info(
        f"Loading Cognito User Pools {len(data)} for region '{region}' into graph.",
    )
    load(
        neo4j_session,
        CognitoUserPoolSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    logger.debug("Running Efs cleanup job.")
    GraphJob.from_node_schema(CognitoIdentityPoolSchema(), common_job_parameters).run(
        neo4j_session
    )
    GraphJob.from_node_schema(CognitoUserPoolSchema(), common_job_parameters).run(
        neo4j_session
    )


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
            f"Syncing Cognito Identity Pools for region '{region}' in account '{current_aws_account_id}'.",
        )

        identity_pools = get_identity_pools(boto3_session, region)
        if not identity_pools:
            logger.info(
                f"No Cognito Identity Pools found in region '{region}'. Skipping sync."
            )
        else:
            identity_pool_roles = get_identity_pool_roles(
                boto3_session, identity_pools, region
            )
            transformed_identity_pools = transform_identity_pools(
                identity_pool_roles, region
            )

            load_identity_pools(
                neo4j_session,
                transformed_identity_pools,
                region,
                current_aws_account_id,
                update_tag,
            )

            user_pools = get_user_pools(boto3_session, region)
            transformed_user_pools = transform_user_pools(user_pools, region)

            load_user_pools(
                neo4j_session,
                transformed_user_pools,
                region,
                current_aws_account_id,
                update_tag,
            )

    cleanup(neo4j_session, common_job_parameters)
