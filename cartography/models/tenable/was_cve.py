from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import CVE
from cartography.models.tenable.cve import TenableCveNodeProperties
from cartography.models.tenable.cve import TenableCveToTenantRel


@dataclass(frozen=True)
class TenableCveToWASPluginRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableWASPlugin)-[:HAS_CVE]->(:TenableCve)
@dataclass(frozen=True)
class TenableCveToWASPluginRel(CartographyRelSchema):
    """Links a Tenable Web App Scanning plugin to a CVE it checks for."""

    target_node_label: str = "TenableWASPlugin"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("plugin_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CVE"
    properties: TenableCveToWASPluginRelProperties = (
        TenableCveToWASPluginRelProperties()
    )


# Same `TenableCve` node the vulnerability management sync writes: both syncs MERGE on
# `TNB|<tenant id>|<CVE ID>`, so a CVE named by plugins of both kinds is one node. This
# schema only adds the edges from WAS plugins; findings reach the CVE through the plugin.
@dataclass(frozen=True)
class TenableWASCveSchema(CartographyNodeSchema):
    """A CVE named by a Tenable Web App Scanning plugin."""

    label: str = "TenableCve"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CVE])
    properties: TenableCveNodeProperties = TenableCveNodeProperties()
    sub_resource_relationship: TenableCveToTenantRel = TenableCveToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [TenableCveToWASPluginRel()],
    )
