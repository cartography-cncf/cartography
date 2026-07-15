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
class LaunchTemplateNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "LaunchTemplateId",
        description="The ID of the launch template (same as launch_template_id)",
    )
    launch_template_id: PropertyRef = PropertyRef(
        "LaunchTemplateId", description="The ID of the launch template"
    )
    name: PropertyRef = PropertyRef(
        "LaunchTemplateName", description="The name of the launch template."
    )
    create_time: PropertyRef = PropertyRef(
        "CreateTime", description="The time launch template was created."
    )
    created_by: PropertyRef = PropertyRef(
        "CreatedBy", description="The principal that created the launch template."
    )
    default_version_number: PropertyRef = PropertyRef(
        "DefaultVersionNumber",
        description="The version number of the default version of the launch template.",
    )
    latest_version_number: PropertyRef = PropertyRef(
        "LatestVersionNumber",
        description="The version number of the latest version of the launch template.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the launch template."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class LaunchTemplateToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LaunchTemplateToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSLaunchTemplate`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LaunchTemplateToAWSAccountRelRelProperties = (
        LaunchTemplateToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class LaunchTemplateSchema(CartographyNodeSchema):
    "Represents an `AWSLaunchTemplate` node in the AWS graph."

    label: str = "AWSLaunchTemplate"
    # DEPRECATED: legacy LaunchTemplate node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["LaunchTemplate"])
    properties: LaunchTemplateNodeProperties = LaunchTemplateNodeProperties()
    sub_resource_relationship: LaunchTemplateToAWSAccountRel = (
        LaunchTemplateToAWSAccountRel()
    )
