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
class TenableWASFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    asset_uuid: PropertyRef = PropertyRef("asset_uuid", extra_index=True)
    plugin_id: PropertyRef = PropertyRef("plugin_id")
    scan_uuid: PropertyRef = PropertyRef("scan_uuid")
    url: PropertyRef = PropertyRef("url")
    output: PropertyRef = PropertyRef("output")
    state: PropertyRef = PropertyRef("state")
    severity: PropertyRef = PropertyRef("severity")
    severity_id: PropertyRef = PropertyRef("severity_id")
    severity_default_id: PropertyRef = PropertyRef("severity_default_id")
    severity_modification_type: PropertyRef = PropertyRef("severity_modification_type")
    first_found: PropertyRef = PropertyRef("first_found")
    last_found: PropertyRef = PropertyRef("last_found")
    indexed_at: PropertyRef = PropertyRef("indexed_at")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    cve_list: PropertyRef = PropertyRef("cve_list")
    has_cve: PropertyRef = PropertyRef("has_cve")


@dataclass(frozen=True)
class TenableWASFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableWASFinding)
@dataclass(frozen=True)
class TenableWASFindingToTenantRel(CartographyRelSchema):
    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableWASFindingToTenantRelProperties = (
        TenableWASFindingToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenableWASFindingToAssetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableWASFinding)-[:AFFECTS]->(:TenableAsset)
@dataclass(frozen=True)
class TenableWASFindingToAssetRel(CartographyRelSchema):
    target_node_label: str = "TenableAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("asset_uuid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: TenableWASFindingToAssetRelProperties = (
        TenableWASFindingToAssetRelProperties()
    )


@dataclass(frozen=True)
class TenableWASFindingToPluginRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableWASFinding)-[:DETECTED_BY]->(:TenableWASPlugin)
@dataclass(frozen=True)
class TenableWASFindingToPluginRel(CartographyRelSchema):
    target_node_label: str = "TenableWASPlugin"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("plugin_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_BY"
    properties: TenableWASFindingToPluginRelProperties = (
        TenableWASFindingToPluginRelProperties()
    )


@dataclass(frozen=True)
class TenableWASFindingSchema(CartographyNodeSchema):
    label: str = "TenableWASFinding"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [ConditionalNodeLabel(label="CVE", conditions={"has_cve": "true"})]
    )
    properties: TenableWASFindingNodeProperties = TenableWASFindingNodeProperties()
    sub_resource_relationship: TenableWASFindingToTenantRel = (
        TenableWASFindingToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TenableWASFindingToAssetRel(),
            TenableWASFindingToPluginRel(),
        ]
    )
