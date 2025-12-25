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
class AWSBackupPlanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("BackupPlanArn")
    name: PropertyRef = PropertyRef("BackupPlanName")
    arn: PropertyRef = PropertyRef("BackupPlanArn")
    backup_plan_id: PropertyRef = PropertyRef("BackupPlanId")
    version_id: PropertyRef = PropertyRef("VersionId")
    creation_date: PropertyRef = PropertyRef("CreationDate")
    deletion_date: PropertyRef = PropertyRef("DeletionDate")
    last_execution_date: PropertyRef = PropertyRef("LastExecutionDate")
    creator_request_id: PropertyRef = PropertyRef("CreatorRequestId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupPlanToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSBackupPlanToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSBackupPlanToAWSAccountRelProperties = (
        AWSBackupPlanToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSBackupPlanSchema(CartographyNodeSchema):
    label: str = "AWSBackupPlan"
    properties: AWSBackupPlanNodeProperties = AWSBackupPlanNodeProperties()
    sub_resource_relationship: AWSBackupPlanToAWSAccountRel = (
        AWSBackupPlanToAWSAccountRel()
    )
