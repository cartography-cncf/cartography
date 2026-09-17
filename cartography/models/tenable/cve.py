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
from cartography.models.ontology.labels import CVE


@dataclass(frozen=True)
class TenableCveNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="CVE identifier prefixed with `TNB|`, for example `TNB|CVE-2024-1234`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier without the Tenable prefix, for example `CVE-2024-1234`.",
    )


@dataclass(frozen=True)
class TenableCveToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableCve)
@dataclass(frozen=True)
class TenableCveToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to a CVE named by one of its plugins."""

    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableCveToTenantRelProperties = TenableCveToTenantRelProperties()


@dataclass(frozen=True)
class TenableCveToCanonicalCveRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableCve)-[:LINKED_TO]->(:CVE)
@dataclass(frozen=True)
class TenableCveToCanonicalCveRel(CartographyRelSchema):
    """Links Tenable's view of a CVE to the canonical NVD record.

    Tenable's export names CVEs as bare identifiers with no severity or scoring of
    its own, so CVSS data is read from the canonical node over this edge. The edge
    only appears for CVEs the `cve` module has already ingested.
    """

    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LINKED_TO"
    properties: TenableCveToCanonicalCveRelProperties = (
        TenableCveToCanonicalCveRelProperties()
    )


@dataclass(frozen=True)
class TenableCveSchema(CartographyNodeSchema):
    """A CVE named by a Tenable plugin.

    Tenable's vulnerability export reports CVEs as a list of identifier strings on
    each plugin and carries no per-CVE metadata, so this node holds identity only.
    A CVE's own severity comes from the canonical NVD record over :LINKED_TO.
    Tenable's per-detection severity and state stay on :TenableFinding, one hop
    away over :HAS_CVE; Tenable derives a plugin's severity by aggregating across
    every CVE the plugin covers, so it cannot be attributed back to one CVE.

    ``id`` is prefixed so these nodes never merge with the canonical
    (:CVE {id: "CVE-..."}) records: they are separately owned and separately
    cleaned up.

    The node is scoped to its tenant like every other Tenable node: the set of CVE
    identifiers is whatever the tenant's plugins named, so an unscoped cleanup would
    let one tenant's sync delete the CVEs another tenant's sync had just written.
    """

    label: str = "TenableCve"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CVE])
    properties: TenableCveNodeProperties = TenableCveNodeProperties()
    sub_resource_relationship: TenableCveToTenantRel = TenableCveToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TenableCveToCanonicalCveRel(),
        ]
    )
