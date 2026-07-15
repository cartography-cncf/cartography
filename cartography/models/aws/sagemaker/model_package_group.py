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
    id: PropertyRef = PropertyRef(
        "ModelPackageGroupArn", description="The ARN of the Model Package Group"
    )
    arn: PropertyRef = PropertyRef(
        "ModelPackageGroupArn",
        extra_index=True,
        description="The ARN of the Model Package Group",
    )
    model_package_group_name: PropertyRef = PropertyRef(
        "ModelPackageGroupName", description="The name of the Model Package Group"
    )
    model_package_group_description: PropertyRef = PropertyRef(
        "ModelPackageGroupDescription",
        description="Human-readable description of the model package group.",
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the Model Package Group was created"
    )
    model_package_group_status: PropertyRef = PropertyRef(
        "ModelPackageGroupStatus", description="The status of the Model Package Group"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Model Package Group exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerModelPackageGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerModelPackageGroupToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerModelPackageGroup`."

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
    "Represents an `AWSSageMakerModelPackageGroup` node in the AWS graph."

    label: str = "AWSSageMakerModelPackageGroup"
    properties: AWSSageMakerModelPackageGroupNodeProperties = (
        AWSSageMakerModelPackageGroupNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerModelPackageGroupToAWSAccountRel = (
        AWSSageMakerModelPackageGroupToAWSAccountRel()
    )
