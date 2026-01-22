import logging
from string import Template
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.intel.aws.iam import get_role_tags
from cartography.util import aws_handle_regions
from cartography.util import batch
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


def get_short_id_from_ec2_arn(arn: str) -> str:
    """
    Return the short-form resource ID from an EC2 ARN.
    For example, for "arn:aws:ec2:us-east-1:test_account:instance/i-1337", return 'i-1337'.
    :param arn: The ARN
    :return: The resource ID
    """
    return arn.split("/")[-1]


def get_bucket_name_from_arn(bucket_arn: str) -> str:
    """
    Return the bucket name from an S3 bucket ARN.
    For example, for "arn:aws:s3:::bucket_name", return 'bucket_name'.
    :param arn: The S3 bucket's full ARN
    :return: The S3 bucket's name
    """
    return bucket_arn.split(":")[-1]


def get_short_id_from_elb_arn(alb_arn: str) -> str:
    """
    Return the ELB name from the ARN
    For example, for arn:aws:elasticloadbalancing:::loadbalancer/foo", return 'foo'.
    :param arn: The ELB's full ARN
    :return: The ELB's name
    """
    return alb_arn.split("/")[-1]


def get_short_id_from_lb2_arn(alb_arn: str) -> str:
    """
    Return the (A|N)LB name from the ARN
    For example, for arn:aws:elasticloadbalancing:::loadbalancer/app/foo/ab123", return 'foo'.
    For example, for arn:aws:elasticloadbalancing:::loadbalancer/net/foo/ab123", return 'foo'.
    :param arn: The (N|A)LB's full ARN
    :return: The (N|A)LB's name
    """
    return alb_arn.split("/")[-2]


def get_resource_type_from_arn(arn: str) -> str:
    """Return the resource type format expected by the Tagging API.

    The Resource Groups Tagging API requires resource types in the form
    ``service:resource``. Most ARNs embed the resource type in the fifth segment
    after the service name. Load balancer ARNs add an extra ``app`` or ``net``
    component that must be preserved. S3 and SQS ARNs only contain the service
    name.  This helper extracts the appropriate string so that ARNs can be
    grouped correctly for API calls.
    """

    parts = arn.split(":", 5)
    service = parts[2]
    if service in {"s3", "sqs"}:
        return service

    resource = parts[5]
    if service == "elasticloadbalancing" and resource.startswith("loadbalancer/"):
        segments = resource.split("/")
        if len(segments) > 2 and segments[1] in {"app", "net"}:
            resource_type = f"{segments[0]}/{segments[1]}"
        else:
            resource_type = segments[0]
    else:
        resource_type = resource.split("/")[0].split(":")[0]

    return f"{service}:{resource_type}" if resource_type else service


# We maintain a mapping from AWS resource types to their associated labels and unique identifiers.
# label: the node label used in cartography for this resource type
# property: the field of this node that uniquely identified this resource type
# id_func: [optional] - EC2 instances and S3 buckets in cartography currently use non-ARNs as their primary identifiers
# so we need to supply a function pointer to translate the ARN returned by the resourcegroupstaggingapi to the form that
# cartography uses.
# TODO - we should make EC2 and S3 assets query-able by their full ARN so that we don't need this workaround.
TAG_RESOURCE_TYPE_MAPPINGS: Dict = {
    "autoscaling:autoScalingGroup": {"label": "AutoScalingGroup", "property": "arn"},
    "dynamodb:table": {"label": "DynamoDBTable", "property": "id"},
    "ec2:instance": {
        "label": "EC2Instance",
        "property": "id",
        "id_func": get_short_id_from_ec2_arn,
    },
    "ec2:internet-gateway": {
        "label": "AWSInternetGateway",
        "property": "id",
        "id_func": get_short_id_from_ec2_arn,
    },
    "ec2:key-pair": {"label": "EC2KeyPair", "property": "id"},
    "ec2:network-interface": {
        "label": "NetworkInterface",
        "property": "id",
        "id_func": get_short_id_from_ec2_arn,
    },
    "ecr:repository": {"label": "ECRRepository", "property": "id"},
    "ec2:security-group": {
        "label": "EC2SecurityGroup",
        "property": "id",
        "id_func": get_short_id_from_ec2_arn,
    },
    "ec2:subnet": {
        "label": "EC2Subnet",
        "property": "subnetid",
        "id_func": get_short_id_from_ec2_arn,
    },
    "ec2:transit-gateway": {"label": "AWSTransitGateway", "property": "id"},
    "ec2:transit-gateway-attachment": {
        "label": "AWSTransitGatewayAttachment",
        "property": "id",
    },
    "ec2:vpc": {
        "label": "AWSVpc",
        "property": "id",
        "id_func": get_short_id_from_ec2_arn,
    },
    "ec2:volume": {
        "label": "EBSVolume",
        "property": "id",
        "id_func": get_short_id_from_ec2_arn,
    },
    "ec2:elastic-ip-address": {
        "label": "ElasticIPAddress",
        "property": "id",
        "id_func": get_short_id_from_ec2_arn,
    },
    "ecs:cluster": {"label": "ECSCluster", "property": "id"},
    "ecs:container": {"label": "ECSContainer", "property": "id"},
    "ecs:container-instance": {"label": "ECSContainerInstance", "property": "id"},
    "ecs:task": {"label": "ECSTask", "property": "id"},
    "ecs:task-definition": {"label": "ECSTaskDefinition", "property": "id"},
    "eks:cluster": {"label": "EKSCluster", "property": "id"},
    "elasticache:cluster": {"label": "ElasticacheCluster", "property": "arn"},
    "elasticloadbalancing:loadbalancer": {
        "label": "LoadBalancer",
        "property": "name",
        "id_func": get_short_id_from_elb_arn,
    },
    "elasticloadbalancing:loadbalancer/app": {
        "label": "LoadBalancerV2",
        "property": "name",
        "id_func": get_short_id_from_lb2_arn,
    },
    "elasticloadbalancing:loadbalancer/net": {
        "label": "LoadBalancerV2",
        "property": "name",
        "id_func": get_short_id_from_lb2_arn,
    },
    "elasticmapreduce:cluster": {"label": "EMRCluster", "property": "arn"},
    "es:domain": {"label": "ESDomain", "property": "arn"},
    "kms:key": {"label": "KMSKey", "property": "arn"},
    "iam:group": {"label": "AWSGroup", "property": "arn"},
    "iam:role": {"label": "AWSRole", "property": "arn"},
    "iam:user": {"label": "AWSUser", "property": "arn"},
    "lambda:function": {"label": "AWSLambda", "property": "id"},
    "redshift:cluster": {"label": "RedshiftCluster", "property": "id"},
    "rds:db": {"label": "RDSInstance", "property": "id"},
    "rds:subgrp": {"label": "DBSubnetGroup", "property": "id"},
    "rds:cluster": {"label": "RDSCluster", "property": "id"},
    "rds:snapshot": {"label": "RDSSnapshot", "property": "id"},
    # Buckets are the only objects in the S3 service: https://docs.aws.amazon.com/AmazonS3/latest/dev/s3-arn-format.html
    "s3": {"label": "S3Bucket", "property": "id", "id_func": get_bucket_name_from_arn},
    "secretsmanager:secret": {"label": "SecretsManagerSecret", "property": "id"},
    "sqs": {"label": "SQSQueue", "property": "id"},
}


@timeit
@aws_handle_regions
def get_tags(
    boto3_session: boto3.session.Session,
    resource_types: list[str],
    region: str,
) -> list[dict[str, Any]]:
    """Retrieve tag data for the provided resource types."""
    resources: list[dict[str, Any]] = []

    if "iam:role" in resource_types:
        resources.extend(get_role_tags(boto3_session))
        resource_types = [rt for rt in resource_types if rt != "iam:role"]

    if not resource_types:
        return resources

    client = boto3_session.client("resourcegroupstaggingapi", region_name=region)
    paginator = client.get_paginator("get_resources")

    # Batch resource types into groups of 100
    # (https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/API_GetResources.html)
    for resource_types_batch in batch(resource_types, size=100):
        for page in paginator.paginate(ResourceTypeFilters=resource_types_batch):
            resources.extend(page["ResourceTagMappingList"])
    return resources


def _load_tags_tx(
    tx: neo4j.Transaction,
    tag_data: Dict,
    resource_type: str,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    INGEST_TAG_TEMPLATE = Template(
        """
    UNWIND $TagData as tag_mapping
        UNWIND tag_mapping.Tags as input_tag
            MATCH
            (a:AWSAccount{id:$Account})-[res:RESOURCE]->(resource:$resource_label{$property:tag_mapping.resource_id})
            MERGE
            (aws_tag:AWSTag:Tag{id:input_tag.Key + ":" + input_tag.Value})
            ON CREATE SET aws_tag.firstseen = timestamp()

            SET aws_tag.lastupdated = $UpdateTag,
            aws_tag.key = input_tag.Key,
            aws_tag.value =  input_tag.Value,
            aws_tag.region = $Region

            MERGE (resource)-[r:TAGGED]->(aws_tag)
            SET r.lastupdated = $UpdateTag,
            r.firstseen = timestamp()
    """,
    )
    if not tag_data:
        return

    query = INGEST_TAG_TEMPLATE.safe_substitute(
        resource_label=TAG_RESOURCE_TYPE_MAPPINGS[resource_type]["label"],
        property=TAG_RESOURCE_TYPE_MAPPINGS[resource_type]["property"],
    )
    tx.run(
        query,
        TagData=tag_data,
        UpdateTag=aws_update_tag,
        Region=region,
        Account=current_aws_account_id,
    ).consume()


@timeit
def load_tags(
    neo4j_session: neo4j.Session,
    tag_data: Dict,
    resource_type: str,
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    if len(tag_data) == 0:
        # If there is no data to load, save some time.
        return
    for tag_data_batch in batch(tag_data, size=100):
        neo4j_session.write_transaction(
            _load_tags_tx,
            tag_data=tag_data_batch,
            resource_type=resource_type,
            region=region,
            current_aws_account_id=current_aws_account_id,
            aws_update_tag=aws_update_tag,
        )


@timeit
def transform_tags(tag_data: Dict, resource_type: str) -> None:
    for tag_mapping in tag_data:
        tag_mapping["resource_id"] = compute_resource_id(tag_mapping, resource_type)


def compute_resource_id(tag_mapping: Dict, resource_type: str) -> str:
    resource_id = tag_mapping["ResourceARN"]
    if "id_func" in TAG_RESOURCE_TYPE_MAPPINGS[resource_type]:
        parse_resource_id_from_arn = TAG_RESOURCE_TYPE_MAPPINGS[resource_type][
            "id_func"
        ]
        resource_id = parse_resource_id_from_arn(tag_mapping["ResourceARN"])
    return resource_id


def _group_tag_data_by_resource_type(
    tag_data: List[Dict],
    tag_resource_type_mappings: Dict,
) -> Dict[str, List[Dict]]:
    """Group raw tag data by the resource types Cartography supports."""

    grouped: Dict[str, List[Dict]] = {rtype: [] for rtype in tag_resource_type_mappings}
    for mapping in tag_data:
        rtype = get_resource_type_from_arn(mapping["ResourceARN"])
        if rtype in grouped:
            grouped[rtype].append(mapping)
        else:
            logger.debug(
                "Unknown tag resource type %s from ARN %s",
                rtype,
                mapping["ResourceARN"],
            )
    return grouped


@timeit
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "aws_import_tags_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: List[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: Dict,
    tag_resource_type_mappings: Dict = TAG_RESOURCE_TYPE_MAPPINGS,
) -> None:
    for region in regions:
        logger.info(
            f"Syncing AWS tags for account {current_aws_account_id} and region {region}",
        )
        all_tag_data = get_tags(
            boto3_session, list(tag_resource_type_mappings.keys()), region
        )
        grouped = _group_tag_data_by_resource_type(
            all_tag_data, tag_resource_type_mappings
        )
        for resource_type in tag_resource_type_mappings.keys():
            tag_data = grouped.get(resource_type, [])
            transform_tags(tag_data, resource_type)  # type: ignore
            logger.info(
                f"Loading {len(tag_data)} tags for resource type {resource_type}",
            )
            load_tags(
                neo4j_session=neo4j_session,
                tag_data=tag_data,  # type: ignore
                resource_type=resource_type,
                region=region,
                current_aws_account_id=current_aws_account_id,
                aws_update_tag=update_tag,
            )
    cleanup(neo4j_session, common_job_parameters)
