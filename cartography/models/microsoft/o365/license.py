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
class M365LicenseNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    sku_id: PropertyRef = PropertyRef("sku_id", extra_index=True)
    sku_part_number: PropertyRef = PropertyRef("sku_part_number", extra_index=True)
    capability_status: PropertyRef = PropertyRef("capability_status")
    applies_to: PropertyRef = PropertyRef("applies_to")
    consumed_units: PropertyRef = PropertyRef("consumed_units")
    prepaid_enabled: PropertyRef = PropertyRef("prepaid_enabled")
    prepaid_suspended: PropertyRef = PropertyRef("prepaid_suspended")
    prepaid_warning: PropertyRef = PropertyRef("prepaid_warning")


@dataclass(frozen=True)
class M365LicenseToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:M365License)<-[:RESOURCE]-(:EntraTenant)
class M365LicenseToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: M365LicenseToTenantRelProperties = M365LicenseToTenantRelProperties()


@dataclass(frozen=True)
class M365LicenseSchema(CartographyNodeSchema):
    label: str = "M365License"
    properties: M365LicenseNodeProperties = M365LicenseNodeProperties()
    sub_resource_relationship: M365LicenseToTenantRel = M365LicenseToTenantRel()
