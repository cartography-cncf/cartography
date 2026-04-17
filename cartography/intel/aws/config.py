import logging
from typing import Any

import boto3
import neo4j

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.aws.util.botocore_config import create_boto3_client
from cartography.models.aws.config import AWSConfigDeliveryChannelSchema
from cartography.models.aws.config import AWSConfigRuleSchema
from cartography.models.aws.config import AWSConfigurationRecorderSchema
from cartography.util import aws_handle_regions
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_configuration_recorders(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict]:
    client = create_boto3_client(boto3_session, "config", region_name=region)
    recorders: list[dict] = []
    response = client.describe_configuration_recorders()
    for recorder in response.get("ConfigurationRecorders"):
        recorders.append(recorder)
    return recorders


@timeit
@aws_handle_regions
def get_delivery_channels(
    boto3_session: boto3.session.Session,
    region: str,
) -> list[dict]:
    client = create_boto3_client(boto3_session, "config", region_name=region)
    channels: list[dict] = []
    response = client.describe_delivery_channels()
    for channel in response.get("DeliveryChannels"):
        channels.append(channel)
    return channels


@timeit
@aws_handle_regions
def get_config_rules(boto3_session: boto3.session.Session, region: str) -> list[dict]:
    client = create_boto3_client(boto3_session, "config", region_name=region)
    paginator = client.get_paginator("describe_config_rules")
    rules: list[dict] = []
    for page in paginator.paginate():
        rules.extend(page["ConfigRules"])
    return rules


def transform_configuration_recorders(
    recorders: list[dict],
    region: str,
    current_aws_account_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for recorder in recorders:
        recording_group = recorder.get("recordingGroup", {})
        result.append(
            {
                "id": f'{recorder["name"]}:{current_aws_account_id}:{region}',
                "name": recorder["name"],
                "role_arn": recorder.get("roleARN"),
                "recording_group_all_supported": recording_group.get("allSupported"),
                "recording_group_include_global_resource_types": recording_group.get(
                    "includeGlobalResourceTypes",
                ),
                "recording_group_resource_types": recording_group.get("resourceTypes"),
            }
        )
    return result


def transform_delivery_channels(
    channels: list[dict],
    region: str,
    current_aws_account_id: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for channel in channels:
        result.append(
            {
                "id": f'{channel["name"]}:{current_aws_account_id}:{region}',
                "name": channel["name"],
                "s3_bucket_name": channel.get("s3BucketName"),
                "s3_key_prefix": channel.get("s3KeyPrefix"),
                "s3_kms_key_arn": channel.get("s3KmsKeyArn"),
                "sns_topic_arn": channel.get("snsTopicARN"),
                "config_snapshot_delivery_properties_delivery_frequency": channel.get(
                    "configSnapshotDeliveryProperties",
                    {},
                ).get("deliveryFrequency"),
            }
        )
    return result


def transform_config_rules(rules: list[dict]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for rule in rules:
        scope = rule.get("Scope", {})
        source = rule.get("Source", {})
        source_details = []
        if source.get("SourceDetails"):
            for detail in source["SourceDetails"]:
                source_details.append(f"{detail}")
        result.append(
            {
                **rule,
                "scope_compliance_resource_types": scope.get("ComplianceResourceTypes"),
                "scope_tag_key": scope.get("TagKey"),
                "scope_tag_value": scope.get("TagValue"),
                "scope_tag_compliance_resource_id": scope.get("ComplianceResourceId"),
                "source_owner": source.get("Owner"),
                "source_identifier": source.get("SourceIdentifier"),
                "source_details": source_details,
            }
        )
    return result


@timeit
def load_configuration_recorders(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSConfigurationRecorderSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_delivery_channels(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSConfigDeliveryChannelSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def load_config_rules(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    load(
        neo4j_session,
        AWSConfigRuleSchema(),
        data,
        lastupdated=aws_update_tag,
        Region=region,
        AWS_ID=current_aws_account_id,
    )


@timeit
def cleanup_config(neo4j_session: neo4j.Session, common_job_parameters: dict) -> None:
    GraphJob.from_node_schema(
        AWSConfigurationRecorderSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(
        AWSConfigDeliveryChannelSchema(), common_job_parameters
    ).run(neo4j_session)
    GraphJob.from_node_schema(AWSConfigRuleSchema(), common_job_parameters).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    boto3_session: boto3.session.Session,
    regions: list[str],
    current_aws_account_id: str,
    update_tag: int,
    common_job_parameters: dict,
) -> None:
    for region in regions:
        logger.info(
            "Syncing AWS Config for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        recorders = get_configuration_recorders(boto3_session, region)
        transformed_recorders = transform_configuration_recorders(
            recorders,
            region,
            current_aws_account_id,
        )
        load_configuration_recorders(
            neo4j_session,
            transformed_recorders,
            region,
            current_aws_account_id,
            update_tag,
        )

        channels = get_delivery_channels(boto3_session, region)
        transformed_channels = transform_delivery_channels(
            channels,
            region,
            current_aws_account_id,
        )
        load_delivery_channels(
            neo4j_session,
            transformed_channels,
            region,
            current_aws_account_id,
            update_tag,
        )

        rules = get_config_rules(boto3_session, region)
        transformed_rules = transform_config_rules(rules)
        load_config_rules(
            neo4j_session,
            transformed_rules,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_config(neo4j_session, common_job_parameters)
