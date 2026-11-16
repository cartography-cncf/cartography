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
class TenableWASFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Tenable Web App Scanning finding ID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    asset_uuid: PropertyRef = PropertyRef(
        "asset_uuid",
        extra_index=True,
        description="UUID of the scanned Tenable asset.",
    )
    asset_fqdn: PropertyRef = PropertyRef(
        "asset_fqdn",
        extra_index=True,
        description=(
            "Lowercase FQDN of the scanned web application, for example "
            "`api.example.com`. Kept on the finding so findings can be grouped by "
            "application without depending on the `AFFECTS` edge."
        ),
    )
    plugin_id: PropertyRef = PropertyRef(
        "plugin_id", description="ID of the plugin that detected the finding."
    )
    scan_uuid: PropertyRef = PropertyRef(
        "scan_uuid", description="UUID of the scan that produced the finding."
    )
    url: PropertyRef = PropertyRef(
        "url", description="URL of the page where the finding was detected."
    )
    output: PropertyRef = PropertyRef("output", description="Raw scanner output.")
    state: PropertyRef = PropertyRef(
        "state", description="Finding state: `OPEN`, `REOPENED` or `FIXED`."
    )
    severity: PropertyRef = PropertyRef(
        "severity", description="Finding severity name, for example `HIGH`."
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
    first_found: PropertyRef = PropertyRef(
        "first_found", description="Timestamp when the finding was first detected."
    )
    last_found: PropertyRef = PropertyRef(
        "last_found",
        description="Timestamp when the finding was most recently detected.",
    )
    indexed_at: PropertyRef = PropertyRef(
        "indexed_at", description="Timestamp when Tenable indexed the finding."
    )
    last_observed: PropertyRef = PropertyRef(
        "last_observed",
        description="Timestamp when the scanner last observed the finding.",
    )
    last_fixed: PropertyRef = PropertyRef(
        "last_fixed",
        description="Timestamp when the finding was last marked fixed, if ever.",
    )
    input_name: PropertyRef = PropertyRef(
        "input_name",
        description=(
            "Name of the page input (parameter) the finding concerns. One URL can have "
            "separate findings for different inputs."
        ),
    )
    http_method: PropertyRef = PropertyRef(
        "http_method",
        description="HTTP method of the request that exposed the finding.",
    )


@dataclass(frozen=True)
class TenableWASFindingToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableWASFinding)
@dataclass(frozen=True)
class TenableWASFindingToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to one of its web application findings."""

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
    """Links a web application finding to the Tenable asset it was found on."""

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
    """Links a web application finding to the plugin that detected it."""

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
    """A web application vulnerability finding from Tenable Web App Scanning."""

    label: str = "TenableWASFinding"
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
