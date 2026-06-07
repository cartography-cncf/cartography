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
class SubImageFrameworkNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    short_name: PropertyRef = PropertyRef("short_name")
    scope: PropertyRef = PropertyRef("scope")
    revision: PropertyRef = PropertyRef("revision")
    enabled: PropertyRef = PropertyRef("enabled")
    enabled_at: PropertyRef = PropertyRef("enabled_at")
    disabled_at: PropertyRef = PropertyRef("disabled_at")
    rule_count: PropertyRef = PropertyRef("rule_count")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SubImageFrameworkToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SubImageTenant)-[:RESOURCE]->(:SubImageFramework)
class SubImageFrameworkToTenantRel(CartographyRelSchema):
    target_node_label: str = "SubImageTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SubImageFrameworkToTenantRelProperties = (
        SubImageFrameworkToTenantRelProperties()
    )


@dataclass(frozen=True)
class SubImageFrameworkSchema(CartographyNodeSchema):
    label: str = "SubImageFramework"
    properties: SubImageFrameworkNodeProperties = SubImageFrameworkNodeProperties()
    sub_resource_relationship: SubImageFrameworkToTenantRel = (
        SubImageFrameworkToTenantRel()
    )
