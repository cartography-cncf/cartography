from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_DYNAMO_DB_BACKUP
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
class DynamoDBBackupNodeProperties(CartographyNodeProperties):
    """
    Stub entity for DynamoDB Backup. Will be enriched when dedicated backup sync is added.
    """

    id: PropertyRef = PropertyRef("Arn", description="The ARN of the backup")
    arn: PropertyRef = PropertyRef("Arn", description="The ARN of the backup")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBBackupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamoDBBackupToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DynamoDBBackupToAWSAccountRelProperties = (
        DynamoDBBackupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class DynamoDBBackupSchema(CartographyNodeSchema):
    """Representation of a DynamoDB [Backup](https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_BackupDetails.html). Currently a stub entity referenced by archival and restore summaries."""

    label: str = "AWSDynamoDBBackup"
    # DEPRECATED: legacy DynamoDBBackup node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_DYNAMO_DB_BACKUP])
    properties: DynamoDBBackupNodeProperties = DynamoDBBackupNodeProperties()
    sub_resource_relationship: DynamoDBBackupToAWSAccountRel = (
        DynamoDBBackupToAWSAccountRel()
    )
