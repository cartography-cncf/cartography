import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.sagemaker.util import sagemaker_handle_regions
from cartography.intel.aws.sagemaker.util import sync_sagemaker_resource
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.sagemaker.user_profile import AWSSageMakerUserProfileSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@sagemaker_handle_regions
def get_user_profiles(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict[str, Any]]:
    """
    Get all SageMaker User Profiles in the given region.
    """
    client = create_boto3_client(boto3_session, "sagemaker", region_name=region)
    paginator = client.get_paginator("list_user_profiles")
    user_profiles: list[dict[str, Any]] = []

    # Get all user profile identifiers (DomainId + UserProfileName)
    user_profile_ids: list[dict[str, str]] = []
    for page in paginator.paginate():
        for profile in page.get("UserProfiles", []):
            user_profile_ids.append(
                {
                    "DomainId": profile["DomainId"],
                    "UserProfileName": profile["UserProfileName"],
                }
            )

    # Get detailed information for each user profile
    for profile_id in user_profile_ids:
        response = client.describe_user_profile(
            DomainId=profile_id["DomainId"],
            UserProfileName=profile_id["UserProfileName"],
        )
        user_profiles.append(response)

    return user_profiles


def transform_user_profiles(
    user_profiles: list[dict[str, Any]],
    region: str,
) -> list[dict[str, Any]]:
    """
    Transform user profile data for loading into Neo4j.
    """
    transformed_profiles = []

    for profile in user_profiles:
        # Extract execution role from UserSettings
        user_settings = profile.get("UserSettings", {})
        execution_role = user_settings.get("ExecutionRole")

        transformed_profile = {
            "UserProfileArn": profile.get("UserProfileArn"),
            "DomainId": profile.get("DomainId"),
            "UserProfileName": profile.get("UserProfileName"),
            "Status": profile.get("Status"),
            "CreationTime": profile.get("CreationTime"),
            "LastModifiedTime": profile.get("LastModifiedTime"),
            "HomeEfsFileSystemUid": profile.get("HomeEfsFileSystemUid"),
            "ExecutionRole": execution_role,
            "Region": region,
        }
        transformed_profiles.append(transformed_profile)

    return transformed_profiles


@timeit
def load_user_profiles(
    neo4j_session: neo4j.Session,
    user_profiles: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    """
    Load user profiles into Neo4j.
    """
    load(
        neo4j_session,
        AWSSageMakerUserProfileSchema(),
        user_profiles,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_user_profiles(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Remove user profiles that no longer exist in AWS.
    """
    GraphJob.from_node_schema(
        AWSSageMakerUserProfileSchema(),
        common_job_parameters,
    ).run(neo4j_session)


@timeit
def sync_user_profiles(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    aws_update_tag: int,
    common_job_parameters: dict[str, Any],
    skip_regions: set[str],
) -> set[str]:
    """
    Sync SageMaker User Profiles for all specified regions.
    """
    return sync_sagemaker_resource(
        neo4j_session=neo4j_session,
        boto3_session=boto3_session,
        regions=regions,
        current_aws_account_id=current_aws_account_id,
        aws_update_tag=aws_update_tag,
        common_job_parameters=common_job_parameters,
        skip_regions=skip_regions,
        submodule_name="user_profiles",
        get_resources=get_user_profiles,
        transform_resources=transform_user_profiles,
        load_resources=load_user_profiles,
        cleanup_resources=cleanup_user_profiles,
    )
