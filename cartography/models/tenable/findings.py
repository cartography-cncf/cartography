from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TenableFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Tenable finding UUID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    asset_uuid: PropertyRef = PropertyRef(
        "asset_uuid",
        extra_index=True,
        description="UUID of the affected Tenable asset.",
    )
    severity: PropertyRef = PropertyRef(
        "severity", description="Finding severity name."
    )
    severity_id: PropertyRef = PropertyRef(
        "severity_id", description="Numeric finding severity."
    )
    severity_default_id: PropertyRef = PropertyRef(
        "severity_default_id", description="Default numeric finding severity."
    )
    severity_modification_type: PropertyRef = PropertyRef(
        "severity_modification_type",
        description="Type of severity adjustment applied.",
    )
    state: PropertyRef = PropertyRef("state", description="Finding state.")
    first_found: PropertyRef = PropertyRef(
        "first_found", description="Timestamp when the finding was first detected."
    )
    last_found: PropertyRef = PropertyRef(
        "last_found",
        description="Timestamp when the finding was most recently detected.",
    )
    indexed: PropertyRef = PropertyRef(
        "indexed", description="Timestamp when Tenable indexed the finding."
    )
    source: PropertyRef = PropertyRef(
        "source", description="Scanner source that reported the finding."
    )
    output: PropertyRef = PropertyRef("output", description="Raw scanner output.")
    resurfaced_date: PropertyRef = PropertyRef(
        "resurfaced_date", description="Timestamp when the finding resurfaced."
    )
    time_taken_to_fix: PropertyRef = PropertyRef(
        "time_taken_to_fix", description="Time taken to remediate the finding."
    )
    port: PropertyRef = PropertyRef(
        "port", description="Network port associated with the finding."
    )
    protocol: PropertyRef = PropertyRef(
        "protocol", description="Network protocol associated with the finding."
    )
    service: PropertyRef = PropertyRef(
        "service", description="Network service associated with the finding."
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="First CVE ID associated with the finding.",
    )
    cve_list: PropertyRef = PropertyRef(
        "cve_list",
        extra_index=True,
        description="CVE IDs associated with the finding.",
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve", description='Whether the finding has a CVE ID, as "true" or "false".'
    )


@dataclass(frozen=True)
class TenableFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableFinding)
@dataclass(frozen=True)
class TenableFindingToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to one of its findings."""

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
class TenableFindingToAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableFinding)-[:AFFECTS]->(:TenableAsset)
@dataclass(frozen=True)
class TenableFindingToAssetRel(CartographyRelSchema):
    """Links a Tenable finding to the affected asset."""

    target_node_label: str = "TenableAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("asset_uuid")},
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
    """Links a Tenable finding to the plugin that detected it."""

    target_node_label: str = "TenablePlugin"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("plugin_id")},
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
    """Links a Tenable finding to the scan that produced it."""

    target_node_label: str = "TenableScan"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("scan_uuid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SCAN"
    properties: TenableFindingToScanRelProperties = TenableFindingToScanRelProperties()


@dataclass(frozen=True)
class TenableFindingSchema(CartographyNodeSchema):
    """A vulnerability finding detected by Tenable on an asset."""

    label: str = "TenableFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [ConditionalNodeLabel(label="CVE", conditions={"has_cve": "true"})]
    )
    properties: TenableFindingNodeProperties = TenableFindingNodeProperties()
    sub_resource_relationship: TenableFindingToTenantRel = TenableFindingToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TenableFindingToAssetRel(),
            TenableFindingToPluginRel(),
            TenableFindingToScanRel(),
        ]
    )
