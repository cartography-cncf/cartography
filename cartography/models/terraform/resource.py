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
class TerraformResourceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    resource_type: PropertyRef = PropertyRef("resource_type")
    resource_name: PropertyRef = PropertyRef("resource_name")
    module_path: PropertyRef = PropertyRef("module_path")
    mode: PropertyRef = PropertyRef("mode")
    provider: PropertyRef = PropertyRef("provider")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TerraformResourceToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TerraformResourceToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "TerraformWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: TerraformResourceToWorkspaceRelProperties = (
        TerraformResourceToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class TerraformResourceSchema(CartographyNodeSchema):
    label: str = "TerraformResource"
    properties: TerraformResourceProperties = TerraformResourceProperties()
    sub_resource_relationship: TerraformResourceToWorkspaceRel = (
        TerraformResourceToWorkspaceRel()
    )


@dataclass(frozen=True)
class TerraformResourceInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    index_key: PropertyRef = PropertyRef("index_key")
    attributes_id: PropertyRef = PropertyRef("attributes_id", extra_index=True)
    resource_type: PropertyRef = PropertyRef("resource_type")
    tags_json: PropertyRef = PropertyRef("tags_json")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TerraformInstanceToResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TerraformInstanceToResourceRel(CartographyRelSchema):
    target_node_label: str = "TerraformResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_INSTANCE"
    properties: TerraformInstanceToResourceRelProperties = (
        TerraformInstanceToResourceRelProperties()
    )


@dataclass(frozen=True)
class TerraformResourceInstanceSchema(CartographyNodeSchema):
    label: str = "TerraformResourceInstance"
    properties: TerraformResourceInstanceProperties = (
        TerraformResourceInstanceProperties()
    )
    sub_resource_relationship: TerraformInstanceToResourceRel = (
        TerraformInstanceToResourceRel()
    )
