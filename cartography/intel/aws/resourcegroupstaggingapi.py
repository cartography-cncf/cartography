import json
import logging
from typing import Any
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.helpers import batch
from cartography.intel.aws.iam import get_role_tags
from cartography.intel.aws.iam import get_user_tags
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.resourcegroupstaggingapi.tag import (
    AWSResourceToTagMatchLink,
)
from cartography.models.aws.resourcegroupstaggingapi.tag import AWSTagSchema
from cartography.models.aws_tagging import AWS_TAGGABLE_RESOURCES
from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import make_source_node_matcher
from cartography.util import aws_handle_regions
from cartography.util import load_resource_binary
from cartography.util import run_scoped_analysis_job
from cartography.util import timeit

logger = logging.getLogger(__name__)

DEFAULT_CLEANUP_BATCH_SIZE = 1000

# IAM is a global service, so its tags are not regional. We fetch IAM tags once
# per sync rather than once per region, passing this marker as the region so the
# IAM path skips the regional resource matching used for regional services.
GLOBAL_REGION = "global"
IAM_TAG_RESOURCE_TYPES = frozenset({"iam:role", "iam:user"})


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


_TAG_ID_PARSERS = {
    "ec2_short_id": get_short_id_from_ec2_arn,
    "elb_short_id": get_short_id_from_elb_arn,
    "lb2_short_id": get_short_id_from_lb2_arn,
    "s3_bucket_name": get_bucket_name_from_arn,
}


def _tag_resource_type_mappings() -> dict[str, dict[str, Any]]:
    """Build the legacy runtime mapping from the shared declarative catalog."""
    mappings: dict[str, dict[str, Any]] = {}
    for resource in AWS_TAGGABLE_RESOURCES:
        mapping: dict[str, Any] = {
            "label": resource.label,
            "property": resource.property,
        }
        if resource.id_parser:
            mapping["id_func"] = _TAG_ID_PARSERS[resource.id_parser]
        if resource.region_property:
            mapping["region_property"] = resource.region_property
        mappings[resource.resource_type] = mapping
    return mappings


# Keep this public mapping backward compatible for callers that customize tag sync.
TAG_RESOURCE_TYPE_MAPPINGS: dict[str, dict[str, Any]] = _tag_resource_type_mappings()


@timeit
@aws_handle_regions
def get_tags(
    boto3_session: boto3.session.Session,
    resource_types: list[str],
    region: str,
) -> list[dict[str, Any]]:
    """Retrieve tag data for the provided resource types."""
    resources: list[dict[str, Any]] = []

    if not resource_types:
        return resources

    client = create_boto3_client(
        boto3_session, "resourcegroupstaggingapi", region_name=region
    )
    paginator = client.get_paginator("get_resources")

    # Batch resource types into groups of 100
    # (https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/API_GetResources.html)
    for resource_types_batch in batch(resource_types, size=100):
        for page in paginator.paginate(ResourceTypeFilters=resource_types_batch):
            resources.extend(page["ResourceTagMappingList"])
    return resources


def _build_tagged_matchlink(
    label: str,
    property: str,
    region_property: str | None = None,
) -> AWSResourceToTagMatchLink:
    """Specialize the TAGGED MatchLink for one taggable resource label.

    Region-scoped resource types (those with a ``region_property`` mapping) also
    match on the synced region so that same-named resources in different regions
    are not cross-tagged.
    """
    matcher = {property: PropertyRef("resource_id")}
    if region_property:
        matcher[region_property] = PropertyRef("Region", set_in_kwargs=True)
    return AWSResourceToTagMatchLink(
        source_node_label=label,
        source_node_matcher=make_source_node_matcher(matcher),
    )


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
    mapping = TAG_RESOURCE_TYPE_MAPPINGS[resource_type]
    region_property = mapping.get("region_property")

    tags: Dict[str, Dict[str, str]] = {}
    links: List[Dict[str, str]] = []
    for tag_mapping in tag_data:
        for tag in tag_mapping["Tags"]:
            tag_id = f"{tag['Key']}:{tag['Value']}"
            tags[tag_id] = {"id": tag_id, "key": tag["Key"], "value": tag["Value"]}
            links.append({"resource_id": tag_mapping["resource_id"], "tag_id": tag_id})

    load(
        neo4j_session,
        AWSTagSchema(),
        list(tags.values()),
        lastupdated=aws_update_tag,
    )
    load_matchlinks(
        neo4j_session,
        _build_tagged_matchlink(mapping["label"], mapping["property"], region_property),
        links,
        lastupdated=aws_update_tag,
        Region=region,
        _sub_resource_label="AWSAccount",
        _sub_resource_id=current_aws_account_id,
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
    """Clean up this account's stale TAGGED relationships.

    AWSTag nodes are shared across accounts, so an account's cleanup only removes
    its own stale relationships. Tag nodes are removed by `cleanup_orphan_tags()`
    once every account has synced.
    """
    cleanup_batch_size = common_job_parameters.get(
        "aws_tagging_api_cleanup_batch", DEFAULT_CLEANUP_BATCH_SIZE
    )
    for label in sorted({resource.label for resource in AWS_TAGGABLE_RESOURCES}):
        GraphJob.from_matchlink(
            AWSResourceToTagMatchLink(source_node_label=label),
            "AWSAccount",
            common_job_parameters["AWS_ID"],
            common_job_parameters["UPDATE_TAG"],
            iterationsize=cleanup_batch_size,
        ).run(neo4j_session)
    run_scoped_analysis_job(
        "aws_tag_legacy_relationship_cleanup.json",
        neo4j_session,
        common_job_parameters,
    )


@timeit
def cleanup_orphan_tags(
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict,
) -> None:
    """Delete AWSTag nodes that no relationship uses.

    Tags are loaded for every resource the tagging API reports, and linked only to
    resources already in the graph. This must run once, after every account's
    `sync()`: an earlier run would delete tags that a later account is about to
    link. Callers that run `_sync_one_account()` themselves must call this after
    their account loop.
    """
    blob = json.load(
        load_resource_binary(
            "cartography.data.jobs.cleanup", "aws_tag_orphan_cleanup.json"
        )
    )
    # Large tenants hold many tags, so the sweep honors the same batch setting as
    # the per-account relationship cleanup.
    batch_size = common_job_parameters.get(
        "aws_tagging_api_cleanup_batch", DEFAULT_CLEANUP_BATCH_SIZE
    )
    for statement in blob["statements"]:
        statement["iterationsize"] = batch_size
    job = GraphJob.from_json(blob, "aws_tag_orphan_cleanup")
    job.merge_parameters({"UPDATE_TAG": common_job_parameters["UPDATE_TAG"]})
    job.run(neo4j_session)


def _load_resource_type_tags(
    neo4j_session: neo4j.Session,
    grouped_tag_data: Dict[str, List[Dict]],
    resource_types: List[str],
    region: str,
    current_aws_account_id: str,
    update_tag: int,
) -> None:
    for resource_type in resource_types:
        tag_data = grouped_tag_data.get(resource_type, [])
        transform_tags(tag_data, resource_type)  # type: ignore[arg-type]
        logger.info(
            f"Loading {len(tag_data)} tags for resource type {resource_type} (region={region})",
        )
        load_tags(
            neo4j_session=neo4j_session,
            tag_data=tag_data,  # type: ignore[arg-type]
            resource_type=resource_type,
            region=region,
            current_aws_account_id=current_aws_account_id,
            aws_update_tag=update_tag,
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
    iam_resource_types = [
        rt for rt in tag_resource_type_mappings if rt in IAM_TAG_RESOURCE_TYPES
    ]
    regional_resource_types = [
        rt for rt in tag_resource_type_mappings if rt not in IAM_TAG_RESOURCE_TYPES
    ]

    if iam_resource_types:
        logger.info(
            f"Syncing AWS IAM tags (global) for account {current_aws_account_id}",
        )
        iam_tag_data: List[Dict] = []
        if "iam:role" in iam_resource_types:
            iam_tag_data.extend(get_role_tags(boto3_session))
        if "iam:user" in iam_resource_types:
            iam_tag_data.extend(get_user_tags(boto3_session))
        iam_grouped = _group_tag_data_by_resource_type(
            iam_tag_data, tag_resource_type_mappings
        )
        _load_resource_type_tags(
            neo4j_session=neo4j_session,
            grouped_tag_data=iam_grouped,
            resource_types=iam_resource_types,
            region=GLOBAL_REGION,
            current_aws_account_id=current_aws_account_id,
            update_tag=update_tag,
        )

    for region in regions:
        logger.info(
            f"Syncing AWS tags for account {current_aws_account_id} and region {region}",
        )
        all_tag_data = get_tags(boto3_session, regional_resource_types, region)
        grouped = _group_tag_data_by_resource_type(
            all_tag_data, tag_resource_type_mappings
        )
        _load_resource_type_tags(
            neo4j_session=neo4j_session,
            grouped_tag_data=grouped,
            resource_types=regional_resource_types,
            region=region,
            current_aws_account_id=current_aws_account_id,
            update_tag=update_tag,
        )
    cleanup(
        neo4j_session,
        common_job_parameters,
    )
