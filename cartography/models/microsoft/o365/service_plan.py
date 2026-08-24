from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class M365ServicePlanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Tenant-scoped Microsoft 365 service plan identifier.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    service_plan_id: PropertyRef = PropertyRef(
        "service_plan_id",
        extra_index=True,
        description="Microsoft service plan GUID.",
    )
    service_plan_name: PropertyRef = PropertyRef(
        "service_plan_name",
        extra_index=True,
        description="Microsoft service plan name.",
    )
    provisioning_status: PropertyRef = PropertyRef(
        "provisioning_status",
        description="Current provisioning status of the service plan.",
    )
    applies_to: PropertyRef = PropertyRef(
        "applies_to",
        description="Resource type to which the service plan applies.",
    )


@dataclass(frozen=True)
class M365ServicePlanToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:M365ServicePlan)<-[:RESOURCE]-(:AzureTenant)
@dataclass(frozen=True)
class M365ServicePlanToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its Microsoft 365 service plans."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: M365ServicePlanToTenantRelProperties = (
        M365ServicePlanToTenantRelProperties()
    )


@dataclass(frozen=True)
class M365ServicePlanToLicenseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:M365ServicePlan)<-[:HAS_SERVICE_PLAN]-(:M365License)
@dataclass(frozen=True)
class M365ServicePlanToLicenseRel(CartographyRelSchema):
    """Links a Microsoft 365 license to one of its included service plans."""

    target_node_label: str = "M365License"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("license_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SERVICE_PLAN"
    properties: M365ServicePlanToLicenseRelProperties = (
        M365ServicePlanToLicenseRelProperties()
    )


@dataclass(frozen=True)
class M365ServicePlanSchema(CartographyNodeSchema):
    """A service entitlement included in a Microsoft 365 license."""

    label: str = "M365ServicePlan"
    properties: M365ServicePlanNodeProperties = M365ServicePlanNodeProperties()
    sub_resource_relationship: M365ServicePlanToTenantRel = M365ServicePlanToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            M365ServicePlanToLicenseRel(),
        ],
    )
