from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.intel.aws.ec2.util import get_botocore_config
from cartography.models.aws.iam.instanceprofile import InstanceProfileSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit


@timeit
@aws_handle_regions
def get_iam_instance_profiles(boto3_session: boto3.Session) -> list[dict[str, Any]]:
    client = boto3_session.client("iam", config=get_botocore_config())
    paginator = client.get_paginator("list_instance_profiles")
    instance_profiles = []
    for page in paginator.paginate():
        instance_profiles.extend(page["InstanceProfiles"])
    return instance_profiles


def transform_instance_profiles(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transformed = []
    for profile in data:
        transformed_profile = {
            "Arn": profile["Arn"],
            "CreateDate": profile["CreateDate"],
            "InstanceProfileId": profile["InstanceProfileId"],
            "InstanceProfileName": profile["InstanceProfileName"],
            "Path": profile["Path"],
            "Roles": [role["Arn"] for role in profile.get("Roles", [])],
        }
        transformed.append(transformed_profile)
    return transformed


@timeit
def load_iam_instance_profiles(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    load(
        neo4j_session,
        InstanceProfileSchema(),
        data,
        AWS_ID=current_aws_account_id,
        lastupdated=update_tag,
    )


@timeit
def sync_iam_instance_profiles(
    boto3_session: boto3.Session,
    neo4j_session: neo4j.Session,
    current_aws_account_id: str,
    update_tag: int,
    regions: list[str],
    common_job_parameters: dict[str, Any],
) -> None:
    profiles = get_iam_instance_profiles(boto3_session)
    profiles = transform_instance_profiles(profiles)
    load_iam_instance_profiles(
        neo4j_session,
        profiles,
        common_job_parameters["AWS_ID"],
        common_job_parameters["UPDATE_TAG"],
        common_job_parameters,
    )
