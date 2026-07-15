from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DynamoDBArchivalSummaryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Id", description='Unique identifier (table ARN + "/archival")'
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    archival_date_time: PropertyRef = PropertyRef(
        "ArchivalDateTime",
        description="The date and time when table archival was initiated",
    )
    archival_reason: PropertyRef = PropertyRef(
        "ArchivalReason", description="The reason for archiving the table"
    )
    archival_backup_arn: PropertyRef = PropertyRef(
        "ArchivalBackupArn",
        description="The ARN of the backup created when the table was archived",
    )


@dataclass(frozen=True)
class DynamoDBArchivalSummaryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBArchivalSummaryToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSDynamoDBArchivalSummary`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBArchivalSummaryToAWSAccountRelProperties = (
        DynamoDBArchivalSummaryToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBArchivalSummaryToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBArchivalSummaryToTableRel(CartographyRelSchema):
    "Represents a `HAS_ARCHIVAL` relationship from `AWSDynamoDBTable` to `AWSDynamoDBArchivalSummary`."

    target_node_label: str = "AWSDynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TableArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ARCHIVAL"
    properties: DynamoDBArchivalSummaryToTableRelProperties = (
        DynamoDBArchivalSummaryToTableRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBArchivalSummaryToBackupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBArchivalSummaryToBackupRel(CartographyRelSchema):
    "Represents a `ARCHIVED_TO_BACKUP` relationship from `AWSDynamoDBArchivalSummary` to `AWSDynamoDBBackup`."

    target_node_label: str = "AWSDynamoDBBackup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ArchivalBackupArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ARCHIVED_TO_BACKUP"
    properties: DynamoDBArchivalSummaryToBackupRelProperties = (
        DynamoDBArchivalSummaryToBackupRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBArchivalSummarySchema(CartographyNodeSchema):
    "Represents an `AWSDynamoDBArchivalSummary` node in the AWS graph."

    label: str = "AWSDynamoDBArchivalSummary"
    # DEPRECATED: legacy DynamoDBArchivalSummary node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DynamoDBArchivalSummary"])
    properties: DynamoDBArchivalSummaryNodeProperties = (
        DynamoDBArchivalSummaryNodeProperties()
    )
    sub_resource_relationship: DynamoDBArchivalSummaryToAWSAccountRel = (
        DynamoDBArchivalSummaryToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBArchivalSummaryToTableRel(),
            DynamoDBArchivalSummaryToBackupRel(),
        ]
    )
