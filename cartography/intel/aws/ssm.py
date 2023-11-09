import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.models.aws.ssm.instance_information import SSMInstanceInformationSchema
from cartography.models.aws.ssm.instance_patch import SSMInstancePatchSchema
from cartography.util import aws_handle_regions
from cartography.util import dict_date_to_epoch
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_instance_ids(neo4j_session: neo4j.Session, region: str, current_aws_account_id: str) -> List[str]:
    get_instances_query = """
    MATCH (:AWSAccount{id: $AWS_ACCOUNT_ID})-[:RESOURCE]->(i:EC2Instance)
    WHERE i.region = $Region
    RETURN i.id
    """
    results = neo4j_session.run(get_instances_query, AWS_ACCOUNT_ID=current_aws_account_id, Region=region)
    instance_ids = []
    for r in results:
        instance_ids.append(r['i.id'])
    return instance_ids


@timeit
@aws_handle_regions
def get_instance_information(
        boto3_session: boto3.session.Session,
        region: str,
        instance_ids: List[str],
) -> List[Dict[str, Any]]:
    client = boto3_session.client('ssm', region_name=region)
    instance_information: List[Dict[str, Any]] = []
    paginator = client.get_paginator('describe_instance_information')
    for i in range(0, len(instance_ids), 50):
        instance_ids_chunk = instance_ids[i:i + 50]
        for info_chunk in paginator.paginate(
            Filters=[{"Key": "InstanceIds", "Values": instance_ids_chunk}],
            MaxResults=50,
        ):
            instance_information.extend(info_chunk.get('InstanceInformationList', []))
    return instance_information


def transform_instance_information(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for ii in data_list:
        ii["LastPingDateTime"] = dict_date_to_epoch(ii, "LastPingDateTime")
        ii["RegistrationDate"] = dict_date_to_epoch(ii, "RegistrationDate")
        ii["LastAssociationExecutionDate"] = dict_date_to_epoch(ii, "LastAssociationExecutionDate")
        ii["LastSuccessfulAssociationExecutionDate"] = dict_date_to_epoch(ii, "LastSuccessfulAssociationExecutionDate")
    return data_list


@timeit
@aws_handle_regions
def get_instance_patches(
        boto3_session: boto3.session.Session,
        region: str,
        instance_ids: List[str],
) -> List[Dict[str, Any]]:
    client = boto3_session.client('ssm', region_name=region)
    instance_patches: List[Dict[str, Any]] = []
    paginator = client.get_paginator('describe_instance_patches')
    for instance_id in instance_ids:
        patches = []
        for page in paginator.paginate(InstanceId=instance_id):
            patches.extend(page["Patches"])
        # to avoid complicating the load function, inject the instance ID into the patch
        for patch in patches:
            patch["_instance_id"] = instance_id
        instance_patches.extend(patches)
    return instance_patches


def transform_instance_patches(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for p in data_list:
        p["Id"] = f"{p['_instance_id']}-{p['Title']}"
        p["InstalledTime"] = dict_date_to_epoch(p, "InstalledTime")
        # Split the comma separated CVEIds, if they exist, and strip
        # the empty string from the list if not.
        p["CVEIds"] = list(filter(None, p.get("CVEIds", "").split(",")))
    return data_list


@timeit
def load_instance_information(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        SSMInstanceInformationSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def load_instance_patches(
    neo4j_session: neo4j.Session,
    data: List[Dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        SSMInstancePatchSchema(),
        data,
        Region=region,
        AWS_ID=current_aws_account_id,
        lastupdated=aws_update_tag,
    )


@timeit
def cleanup_ssm(neo4j_session: neo4j.Session, common_job_parameters: Dict[str, Any]) -> None:
    logger.info("Running SSM cleanup")
    GraphJob.from_node_schema(SSMInstanceInformationSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_node_schema(SSMInstancePatchSchema(), common_job_parameters).run(neo4j_session)


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
        logger.info("Syncing SSM for region '%s' in account '%s'.", region, current_aws_account_id)
        instance_ids = get_instance_ids(neo4j_session, region, current_aws_account_id)
        data = get_instance_information(boto3_session, region, instance_ids)
        data = transform_instance_information(data)
        load_instance_information(neo4j_session, data, region, current_aws_account_id, update_tag)

        data = get_instance_patches(boto3_session, region, instance_ids)
        data = transform_instance_patches(data)
        load_instance_patches(neo4j_session, data, region, current_aws_account_id, update_tag)
    cleanup_ssm(neo4j_session, common_job_parameters)
