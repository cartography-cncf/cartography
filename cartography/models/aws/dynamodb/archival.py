from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DynamoDBArchivalSummaryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    archival_date_time: PropertyRef = PropertyRef("ArchivalDateTime")
    archival_reason: PropertyRef = PropertyRef("ArchivalReason")
    archival_backup_arn: PropertyRef = PropertyRef("ArchivalBackupArn")


@dataclass(frozen=True)
class DynamoDBArchivalSummaryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBArchivalSummaryToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "DynamoDBTable"
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
    target_node_label: str = "DynamoDBBackup"
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
    label: str = "DynamoDBArchivalSummary"
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
