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
class SubImageModuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("module_name")
    is_configured: PropertyRef = PropertyRef("is_configured")
    last_sync_status: PropertyRef = PropertyRef("last_sync_status")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SubImageModuleToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SubImageTenant)-[:RESOURCE]->(:SubImageModule)
class SubImageModuleToTenantRel(CartographyRelSchema):
    target_node_label: str = "SubImageTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SubImageModuleToTenantRelProperties = (
        SubImageModuleToTenantRelProperties()
    )


@dataclass(frozen=True)
class SubImageModuleSchema(CartographyNodeSchema):
    label: str = "SubImageModule"
    properties: SubImageModuleNodeProperties = SubImageModuleNodeProperties()
    sub_resource_relationship: SubImageModuleToTenantRel = SubImageModuleToTenantRel()
