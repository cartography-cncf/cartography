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
class TerraformOutputProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    output_name: PropertyRef = PropertyRef("output_name")
    value_type: PropertyRef = PropertyRef("value_type")
    sensitive: PropertyRef = PropertyRef("sensitive")
    value_json: PropertyRef = PropertyRef("value_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TerraformOutputToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TerraformOutputToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "TerraformWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_OUTPUT"
    properties: TerraformOutputToWorkspaceRelProperties = (
        TerraformOutputToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class TerraformOutputSchema(CartographyNodeSchema):
    label: str = "TerraformOutput"
    properties: TerraformOutputProperties = TerraformOutputProperties()
    sub_resource_relationship: TerraformOutputToWorkspaceRel = (
        TerraformOutputToWorkspaceRel()
    )
