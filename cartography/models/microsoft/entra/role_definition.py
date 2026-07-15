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
    id: PropertyRef = PropertyRef("id", description="Entra role definition ID.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the directory role."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the permissions granted by the role."
    )
    is_built_in: PropertyRef = PropertyRef(
        "is_built_in", description="Whether this is a Microsoft built-in role."
    )
    is_enabled: PropertyRef = PropertyRef(
        "is_enabled", description="Whether the role definition is enabled."
    )
    template_id: PropertyRef = PropertyRef(
        "template_id", description="Template ID of the directory role."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraRoleDefinitionToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraRoleDefinition)<-[:RESOURCE]-(:AzureTenant)
class EntraRoleDefinitionToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its directory role definitions."""

    target_node_label: str = "AzureTenant"
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
    """A directory role definition in Microsoft Entra ID."""

    label: str = "EntraRoleDefinition"
    properties: EntraRoleDefinitionNodeProperties = EntraRoleDefinitionNodeProperties()
    sub_resource_relationship: EntraRoleDefinitionToTenantRel = (
        EntraRoleDefinitionToTenantRel()
    )
