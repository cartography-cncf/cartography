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
class DatabricksSecretScopeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    backend_type: PropertyRef = PropertyRef("backend_type")
    keyvault_resource_id: PropertyRef = PropertyRef(
        "keyvault_resource_id", extra_index=True
    )
    keyvault_dns_name: PropertyRef = PropertyRef("keyvault_dns_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksSecretScopeToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksSecretScope)
class DatabricksSecretScopeToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksSecretScopeToWorkspaceRelProperties = (
        DatabricksSecretScopeToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksSecretScopeSchema(CartographyNodeSchema):
    label: str = "DatabricksSecretScope"
    properties: DatabricksSecretScopeNodeProperties = (
        DatabricksSecretScopeNodeProperties()
    )
    sub_resource_relationship: DatabricksSecretScopeToWorkspaceRel = (
        DatabricksSecretScopeToWorkspaceRel()
    )
