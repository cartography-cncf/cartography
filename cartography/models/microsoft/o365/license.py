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
    id: PropertyRef = PropertyRef(
        "id",
        description="Tenant-scoped identifier for the subscribed Microsoft 365 SKU.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    sku_id: PropertyRef = PropertyRef(
        "sku_id",
        extra_index=True,
        description="Microsoft product SKU GUID.",
    )
    sku_part_number: PropertyRef = PropertyRef(
        "sku_part_number",
        extra_index=True,
        description="Microsoft product SKU part number.",
    )
    capability_status: PropertyRef = PropertyRef(
        "capability_status",
        description="Current capability status of the subscribed SKU.",
    )
    applies_to: PropertyRef = PropertyRef(
        "applies_to",
        description="Resource type to which the subscribed SKU applies.",
    )
    consumed_units: PropertyRef = PropertyRef(
        "consumed_units",
        description="Number of licenses currently assigned.",
    )
    prepaid_enabled: PropertyRef = PropertyRef(
        "prepaid_enabled",
        description="Number of prepaid licenses currently enabled.",
    )
    prepaid_suspended: PropertyRef = PropertyRef(
        "prepaid_suspended",
        description="Number of prepaid licenses currently suspended.",
    )
    prepaid_warning: PropertyRef = PropertyRef(
        "prepaid_warning",
        description="Number of prepaid licenses in warning state.",
    )


@dataclass(frozen=True)
class M365LicenseToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:M365License)<-[:RESOURCE]-(:AzureTenant)
@dataclass(frozen=True)
class M365LicenseToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its Microsoft 365 licenses."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: M365LicenseToTenantRelProperties = M365LicenseToTenantRelProperties()


@dataclass(frozen=True)
class M365LicenseSchema(CartographyNodeSchema):
    """A Microsoft 365 license subscription held by a tenant."""

    label: str = "M365License"
    properties: M365LicenseNodeProperties = M365LicenseNodeProperties()
    sub_resource_relationship: M365LicenseToTenantRel = M365LicenseToTenantRel()
