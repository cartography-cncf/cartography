from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AWSBackupBackupPlanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "BackupPlanId", description="The ID of the backup plan"
    )
    arn: PropertyRef = PropertyRef(
        "BackupPlanArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the backup plan",
    )
    name: PropertyRef = PropertyRef(
        "BackupPlanName", description="The display name of the backup plan"
    )
    version_id: PropertyRef = PropertyRef(
        "VersionId", description="The version ID of the backup plan"
    )
    creation_date: PropertyRef = PropertyRef(
        "CreationDate", description="The time the backup plan was created"
    )
    last_execution_date: PropertyRef = PropertyRef(
        "LastExecutionDate",
        description="The last time a backup job ran with this plan",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region of the backup plan",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupBackupPlanToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupBackupPlanToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBackupBackupPlanToAWSAccountRelProperties = (
        AWSBackupBackupPlanToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBackupBackupPlanSchema(CartographyNodeSchema):
    """Representation of an AWS [Backup plan](https://docs.aws.amazon.com/aws-backup/latest/devguide/API_BackupPlansListMember.html)."""

    label: str = "AWSBackupBackupPlan"
    properties: AWSBackupBackupPlanNodeProperties = AWSBackupBackupPlanNodeProperties()
    sub_resource_relationship: AWSBackupBackupPlanToAWSAccountRel = (
        AWSBackupBackupPlanToAWSAccountRel()
    )
