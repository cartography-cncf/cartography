import logging
from typing import Dict
from typing import List

import boto3
import neo4j

from cartography.client.core.tx import run_write_query
from cartography.util import aws_handle_regions
from cartography.util import run_cleanup_job
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
@aws_handle_regions
def get_configuration_recorders(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client("config", region_name=region)
    recorders: List[Dict] = []
    response = client.describe_configuration_recorders()
    for recorder in response.get("ConfigurationRecorders"):
        recorders.append(recorder)
    return recorders


@timeit
@aws_handle_regions
def get_delivery_channels(
    boto3_session: boto3.session.Session,
    region: str,
) -> List[Dict]:
    client = boto3_session.client("config", region_name=region)
    channels: List[Dict] = []
    response = client.describe_delivery_channels()
    for channel in response.get("DeliveryChannels"):
        channels.append(channel)
    return channels


@timeit
@aws_handle_regions
def get_config_rules(boto3_session: boto3.session.Session, region: str) -> List[Dict]:
    client = boto3_session.client("config", region_name=region)
    paginator = client.get_paginator("describe_config_rules")
    rules: List[Dict] = []
    for page in paginator.paginate():
        rules.extend(page["ConfigRules"])
    return rules


@timeit
def load_configuration_recorders(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_configuration_recorders = """
    UNWIND $Recorders as recorder
        MERGE (n:AWSConfigurationRecorder{id: recorder._id})
        ON CREATE SET n.firstseen = timestamp()
        SET n.name = recorder.name, n.role_arn = recorder.roleARN,
            n.recording_group_all_supported = recorder.recordingGroup.allSupported,
            n.recording_group_include_global_resource_types = recorder.recordingGroup.includeGlobalResourceTypes,
            n.recording_group_resource_types = recorder.recordingGroup.resourceTypes,
            n.region = $Region, n.lastupdated = $aws_update_tag
        WITH n
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(n)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    # Recorders don't have a unique ID, as the name is autoset to "default", but we can
    # generate a unique id using a combo of the name, account id and region, since the name
    # itself is unique per region.
    for recorder in data:
        recorder["_id"] = f'{recorder["name"]}:{current_aws_account_id}:{region}'

    run_write_query(
        neo4j_session,
        ingest_configuration_recorders,
        Recorders=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_delivery_channels(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_delivery_channels = """
    UNWIND $Channels as channel
        MERGE (n:AWSConfigDeliveryChannel{id: channel._id})
        ON CREATE SET n.firstseen = timestamp()
        SET n.name = channel.name,
            n.s3_bucket_name = channel.s3BucketName,
            n.s3_key_prefix = channel.s3KeyPrefix,
            n.s3_kms_key_arn = channel.s3KmsKeyArn,
            n.sns_topic_arn = channel.snsTopicARN,
            n.config_snapshot_delivery_properties_delivery_frequency = channel.configSnapshotDeliveryProperties.deliveryFrequency,
            n.region = $Region, n.lastupdated = $aws_update_tag
        WITH n
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(n)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """  # noqa:E501
    # Delivery channels don't have a unique ID, as the name is autoset to "default", but we can
    # generate a unique id using a combo of the name, account id and region, since the name
    # itself is unique per region.
    for channel in data:
        channel["_id"] = f'{channel["name"]}:{current_aws_account_id}:{region}'

    run_write_query(
        neo4j_session,
        ingest_delivery_channels,
        Channels=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def load_config_rules(
    neo4j_session: neo4j.Session,
    data: List[Dict],
    region: str,
    current_aws_account_id: str,
    aws_update_tag: int,
) -> None:
    ingest_config_rules = """
    UNWIND $Rules as rule
        MERGE (n:AWSConfigRule{id: rule.ConfigRuleArn})
        ON CREATE SET n.firstseen = timestamp()
        SET n.name = rule.ConfigRuleName, n.description = rule.Description,
            n.arn = rule.ConfigRuleArn,
            n.rule_id = rule.ConfigRuleId,
            n.scope_compliance_resource_types = rule.Scope.ComplianceResourceTypes,
            n.scope_tag_key = rule.Scope.TagKey,
            n.scope_tag_value = rule.Scope.TagValue,
            n.scope_tag_compliance_resource_id = rule.Scope.ComplianceResourceId,
            n.source_owner = rule.Source.Owner,
            n.source_identifier = rule.Source.SourceIdentifier,
            n.source_details = rule._source_details,
            n.input_parameters = rule.InputParameters,
            n.maximum_execution_frequency = rule.MaximumExecutionFrequency,
            n.created_by = rule.CreatedBy,
            n.region = $Region, n.lastupdated = $aws_update_tag
        WITH n
        MATCH (owner:AWSAccount{id: $AWS_ACCOUNT_ID})
        MERGE (owner)-[r:RESOURCE]->(n)
        ON CREATE SET r.firstseen = timestamp()
        SET r.lastupdated = $aws_update_tag
    """
    for rule in data:
        details = []
        if rule.get("Source", {}).get("SourceDetails"):
            for detail in rule["Source"]["SourceDetails"]:
                details.append(f"{detail}")
        rule["_source_details"] = details
    run_write_query(
        neo4j_session,
        ingest_config_rules,
        Rules=data,
        Region=region,
        AWS_ACCOUNT_ID=current_aws_account_id,
        aws_update_tag=aws_update_tag,
    )


@timeit
def cleanup_config(neo4j_session: neo4j.Session, common_job_parameters: Dict) -> None:
    run_cleanup_job(
        "aws_import_config_cleanup.json",
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
) -> None:
    for region in regions:
        logger.info(
            "Syncing AWS Config for region '%s' in account '%s'.",
            region,
            current_aws_account_id,
        )
        recorders = get_configuration_recorders(boto3_session, region)
        load_configuration_recorders(
            neo4j_session,
            recorders,
            region,
            current_aws_account_id,
            update_tag,
        )
        channels = get_delivery_channels(boto3_session, region)
        load_delivery_channels(
            neo4j_session,
            channels,
            region,
            current_aws_account_id,
            update_tag,
        )
        rules = get_config_rules(boto3_session, region)
        load_config_rules(
            neo4j_session,
            rules,
            region,
            current_aws_account_id,
            update_tag,
        )
    cleanup_config(neo4j_session, common_job_parameters)
