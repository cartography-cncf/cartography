from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TenableFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    finding_id: PropertyRef = PropertyRef("finding_id", extra_index=True)
    asset_uuid: PropertyRef = PropertyRef("asset_uuid", extra_index=True)
    severity: PropertyRef = PropertyRef("severity")
    severity_id: PropertyRef = PropertyRef("severity_id")
    severity_default_id: PropertyRef = PropertyRef("severity_default_id")
    severity_modification_type: PropertyRef = PropertyRef("severity_modification_type")
    state: PropertyRef = PropertyRef("state")
    first_found: PropertyRef = PropertyRef("first_found")
    last_found: PropertyRef = PropertyRef("last_found")
    indexed: PropertyRef = PropertyRef("indexed")
    source: PropertyRef = PropertyRef("source")
    output: PropertyRef = PropertyRef("output")
    resurfaced_date: PropertyRef = PropertyRef("resurfaced_date")
    time_taken_to_fix: PropertyRef = PropertyRef("time_taken_to_fix")
    port: PropertyRef = PropertyRef("port")
    protocol: PropertyRef = PropertyRef("protocol")
    service: PropertyRef = PropertyRef("service")


@dataclass(frozen=True)
class TenableCVENodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)


@dataclass(frozen=True)
class TenableFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableFinding)
@dataclass(frozen=True)
class TenableFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableFindingToTenantRelProperties = (
        TenableFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenableCVEToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableCVE)
@dataclass(frozen=True)
class TenableCVEToTenantRel(CartographyRelSchema):
    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableCVEToTenantRelProperties = TenableCVEToTenantRelProperties()


@dataclass(frozen=True)
class TenableFindingToAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableFinding)-[:AFFECTS]->(:TenableAsset)
@dataclass(frozen=True)
class TenableFindingToAssetRel(CartographyRelSchema):
    target_node_label: str = "TenableAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("asset_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: TenableFindingToAssetRelProperties = (
        TenableFindingToAssetRelProperties()
    )


@dataclass(frozen=True)
class TenableFindingToPluginRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableFinding)-[:DETECTED_BY]->(:TenablePlugin)
@dataclass(frozen=True)
class TenableFindingToPluginRel(CartographyRelSchema):
    target_node_label: str = "TenablePlugin"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("plugin_node_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_BY"
    properties: TenableFindingToPluginRelProperties = (
        TenableFindingToPluginRelProperties()
    )


@dataclass(frozen=True)
class TenableFindingToScanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableFinding)-[:PART_OF_SCAN]->(:TenableScan)
@dataclass(frozen=True)
class TenableFindingToScanRel(CartographyRelSchema):
    target_node_label: str = "TenableScan"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("scan_node_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SCAN"
    properties: TenableFindingToScanRelProperties = TenableFindingToScanRelProperties()


@dataclass(frozen=True)
class TenableFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableFinding)-[:HAS_CVE]->(:TenableCVE:CVE)
@dataclass(frozen=True)
class TenableFindingToCVERel(CartographyRelSchema):
    target_node_label: str = "TenableCVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_node_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_CVE"
    properties: TenableFindingToCVERelProperties = TenableFindingToCVERelProperties()


@dataclass(frozen=True)
class TenableCVESchema(CartographyNodeSchema):
    label: str = "TenableCVE"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CVE"])
    properties: TenableCVENodeProperties = TenableCVENodeProperties()
    sub_resource_relationship: TenableCVEToTenantRel = TenableCVEToTenantRel()


@dataclass(frozen=True)
class TenableFindingSchema(CartographyNodeSchema):
    label: str = "TenableFinding"
    properties: TenableFindingNodeProperties = TenableFindingNodeProperties()
    sub_resource_relationship: TenableFindingToTenantRel = TenableFindingToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TenableFindingToAssetRel(),
            TenableFindingToPluginRel(),
            TenableFindingToScanRel(),
            TenableFindingToCVERel(),
        ]
    )
