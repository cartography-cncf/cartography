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
class AzurePrincipalProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("current_user")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("current_user", extra_index=True)


@dataclass(frozen=True)
class AzurePrincipalToTenantProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureTenant)-[:RESOURCE]->(:AzurePrincipal)
class AzurePrincipalToTenantRel(CartographyRelSchema):
    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzurePrincipalToTenantProperties = AzurePrincipalToTenantProperties()


@dataclass(frozen=True)
class AzurePrincipalSchema(CartographyNodeSchema):
    label: str = "AzurePrincipal"
    properties: AzurePrincipalProperties = AzurePrincipalProperties()
    sub_resource_relationship: AzurePrincipalToTenantRel = AzurePrincipalToTenantRel()
