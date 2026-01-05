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
class AWSSageMakerModelPackageGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ModelPackageGroupArn")
    arn: PropertyRef = PropertyRef("ModelPackageGroupArn", extra_index=True)
    model_package_group_name: PropertyRef = PropertyRef("ModelPackageGroupName")
    model_package_group_description: PropertyRef = PropertyRef(
        "ModelPackageGroupDescription"
    )
    creation_time: PropertyRef = PropertyRef("CreationTime")
    model_package_group_status: PropertyRef = PropertyRef("ModelPackageGroupStatus")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelPackageGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelPackageGroupToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerModelPackageGroupToAWSAccountRelProperties = (
        AWSSageMakerModelPackageGroupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerModelPackageGroupSchema(CartographyNodeSchema):
    label: str = "AWSSageMakerModelPackageGroup"
    properties: AWSSageMakerModelPackageGroupNodeProperties = (
        AWSSageMakerModelPackageGroupNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerModelPackageGroupToAWSAccountRel = (
        AWSSageMakerModelPackageGroupToAWSAccountRel()
    )
