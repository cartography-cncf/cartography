from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
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
class TenableCveSchema(CartographyNodeSchema):
    """A CVE named by a Tenable plugin.

    Tenable's vulnerability export reports CVEs as a list of identifier strings on
    each plugin and carries no per-CVE metadata, so this node holds identity only.
    Tenable's per-detection severity and state stay on :TenableFinding, one hop
    away over :HAS_CVE; Tenable derives a plugin's severity by aggregating across
    every CVE the plugin covers, so it cannot be attributed back to one CVE.

    The :CVE ontology label gives this node an ``_ont_cve_id``, which is how it
    correlates with other providers' records of the same CVE, including the NVD
    data ingested by the `cve` module. No relationship is needed for that.

    ``id`` is prefixed because the `cve` module MERGEs on ``(:CVE {id})``. With a
    bare id it would match these nodes and adopt them as its own records.
    """

    label: str = "TenableCve"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CVE])
    properties: TenableCveNodeProperties = TenableCveNodeProperties()
    sub_resource_relationship: TenableCveToTenantRel = TenableCveToTenantRel()
