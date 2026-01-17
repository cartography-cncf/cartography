from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DynamoDBTableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Arn")
    arn: PropertyRef = PropertyRef("Arn")
    name: PropertyRef = PropertyRef("TableName")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Basic table properties
    rows: PropertyRef = PropertyRef("Rows")
    size: PropertyRef = PropertyRef("Size")
    table_status: PropertyRef = PropertyRef("TableStatus")
    creation_date_time: PropertyRef = PropertyRef("CreationDateTime")

    # Provisioned throughput
    provisioned_throughput_read_capacity_units: PropertyRef = PropertyRef(
        "ProvisionedThroughputReadCapacityUnits",
    )
    provisioned_throughput_write_capacity_units: PropertyRef = PropertyRef(
        "ProvisionedThroughputWriteCapacityUnits",
    )

    # Billing
    billing_mode: PropertyRef = PropertyRef("BillingMode")
    last_update_to_pay_per_request_date_time: PropertyRef = PropertyRef(
        "LastUpdateToPayPerRequestDateTime",
    )

    # Streams
    latest_stream_arn: PropertyRef = PropertyRef("LatestStreamArn")
    latest_stream_label: PropertyRef = PropertyRef("LatestStreamLabel")
    stream_enabled: PropertyRef = PropertyRef("StreamEnabled")
    stream_view_type: PropertyRef = PropertyRef("StreamViewType")

    # Encryption
    sse_status: PropertyRef = PropertyRef("SSEStatus")
    sse_type: PropertyRef = PropertyRef("SSEType")
    sse_kms_key_arn: PropertyRef = PropertyRef("SSEKMSKeyArn")

    # Archival
    archival_backup_arn: PropertyRef = PropertyRef("ArchivalBackupArn")
    archival_date_time: PropertyRef = PropertyRef("ArchivalDateTime")
    archival_reason: PropertyRef = PropertyRef("ArchivalReason")

    # Restore
    restore_date_time: PropertyRef = PropertyRef("RestoreDateTime")
    restore_in_progress: PropertyRef = PropertyRef("RestoreInProgress")
    source_backup_arn: PropertyRef = PropertyRef("SourceBackupArn")
    source_table_arn: PropertyRef = PropertyRef("SourceTableArn")


@dataclass(frozen=True)
class DynamoDBTableToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DynamoDBTable)<-[:RESOURCE]-(:AWSAccount)
class DynamoDBTableToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBTableToAWSAccountRelRelProperties = (
        DynamoDBTableToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBTableSchema(CartographyNodeSchema):
    label: str = "DynamoDBTable"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: DynamoDBTableNodeProperties = DynamoDBTableNodeProperties()
    sub_resource_relationship: DynamoDBTableToAWSAccountRel = (
        DynamoDBTableToAWSAccountRel()
    )
