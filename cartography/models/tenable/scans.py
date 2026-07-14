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
class TenableScanNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Tenable scan UUID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    schedule_uuid: PropertyRef = PropertyRef(
        "schedule_uuid", description="UUID of the scan schedule."
    )
    started_at: PropertyRef = PropertyRef(
        "started_at", description="Timestamp when the scan started."
    )
    last_scan_target: PropertyRef = PropertyRef(
        "last_scan_target", description="Most recently scanned target."
    )


@dataclass(frozen=True)
class TenableScanToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableScan)
@dataclass(frozen=True)
class TenableScanToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to one of its scans."""

    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableScanToTenantRelProperties = TenableScanToTenantRelProperties()


@dataclass(frozen=True)
class TenableScanSchema(CartographyNodeSchema):
    """A Tenable scan that produced vulnerability findings."""

    label: str = "TenableScan"
    properties: TenableScanNodeProperties = TenableScanNodeProperties()
    sub_resource_relationship: TenableScanToTenantRel = TenableScanToTenantRel()
