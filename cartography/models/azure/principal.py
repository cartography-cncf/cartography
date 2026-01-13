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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzurePrincipalToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzurePrincipalToTenantRel(CartographyRelSchema):
    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzurePrincipalToTenantRelProperties = (
        AzurePrincipalToTenantRelProperties()
    )


@dataclass(frozen=True)
class AzurePrincipalSchema(CartographyNodeSchema):
    label: str = "AzurePrincipal"
    properties: AzurePrincipalProperties = AzurePrincipalProperties()
    sub_resource_relationship: AzurePrincipalToTenantRel = AzurePrincipalToTenantRel()
