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
class EntraRoleDefinitionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    display_name: PropertyRef = PropertyRef("display_name")
    description: PropertyRef = PropertyRef("description")
    is_built_in: PropertyRef = PropertyRef("is_built_in")
    is_enabled: PropertyRef = PropertyRef("is_enabled")
    template_id: PropertyRef = PropertyRef("template_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraRoleDefinitionToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraRoleDefinition)<-[:RESOURCE]-(:EntraTenant)
class EntraRoleDefinitionToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraRoleDefinitionToTenantRelProperties = (
        EntraRoleDefinitionToTenantRelProperties()
    )


@dataclass(frozen=True)
class EntraRoleDefinitionSchema(CartographyNodeSchema):
    label: str = "EntraRoleDefinition"
    properties: EntraRoleDefinitionNodeProperties = EntraRoleDefinitionNodeProperties()
    sub_resource_relationship: EntraRoleDefinitionToTenantRel = (
        EntraRoleDefinitionToTenantRel()
    )
