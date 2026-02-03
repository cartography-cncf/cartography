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
class DynamoDBRestoreSummaryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    restore_date_time: PropertyRef = PropertyRef("RestoreDateTime")
    restore_in_progress: PropertyRef = PropertyRef("RestoreInProgress")
    source_backup_arn: PropertyRef = PropertyRef("SourceBackupArn")
    source_table_arn: PropertyRef = PropertyRef("SourceTableArn")


@dataclass(frozen=True)
class DynamoDBRestoreSummaryToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBRestoreSummaryToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBRestoreSummaryToAWSAccountRelProperties = (
        DynamoDBRestoreSummaryToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBRestoreSummaryToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBRestoreSummaryToTableRel(CartographyRelSchema):
    target_node_label: str = "DynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TableArn")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RESTORE"
    properties: DynamoDBRestoreSummaryToTableRelProperties = (
        DynamoDBRestoreSummaryToTableRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBRestoreSummaryToBackupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBRestoreSummaryToBackupRel(CartographyRelSchema):
    target_node_label: str = "DynamoDBBackup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SourceBackupArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESTORED_FROM_BACKUP"
    properties: DynamoDBRestoreSummaryToBackupRelProperties = (
        DynamoDBRestoreSummaryToBackupRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBRestoreSummaryToSourceTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBRestoreSummaryToSourceTableRel(CartographyRelSchema):
    target_node_label: str = "DynamoDBTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SourceTableArn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESTORED_FROM_TABLE"
    properties: DynamoDBRestoreSummaryToSourceTableRelProperties = (
        DynamoDBRestoreSummaryToSourceTableRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBRestoreSummarySchema(CartographyNodeSchema):
    label: str = "DynamoDBRestoreSummary"
    properties: DynamoDBRestoreSummaryNodeProperties = (
        DynamoDBRestoreSummaryNodeProperties()
    )
    sub_resource_relationship: DynamoDBRestoreSummaryToAWSAccountRel = (
        DynamoDBRestoreSummaryToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DynamoDBRestoreSummaryToTableRel(),
            DynamoDBRestoreSummaryToBackupRel(),
            DynamoDBRestoreSummaryToSourceTableRel(),
        ]
    )
