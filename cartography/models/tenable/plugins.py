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
class TenablePluginNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    family: PropertyRef = PropertyRef("family")
    family_id: PropertyRef = PropertyRef("family_id")
    description: PropertyRef = PropertyRef("description")
    synopsis: PropertyRef = PropertyRef("synopsis")
    solution: PropertyRef = PropertyRef("solution")
    risk_factor: PropertyRef = PropertyRef("risk_factor")
    has_patch: PropertyRef = PropertyRef("has_patch")
    has_workaround: PropertyRef = PropertyRef("has_workaround")
    vendor_unpatched: PropertyRef = PropertyRef("vendor_unpatched")
    vendor_severity: PropertyRef = PropertyRef("vendor_severity")
    exploit_available: PropertyRef = PropertyRef("exploit_available")
    exploitability_ease: PropertyRef = PropertyRef("exploitability_ease")
    exploit_framework_metasploit: PropertyRef = PropertyRef(
        "exploit_framework_metasploit"
    )
    patch_publication_date: PropertyRef = PropertyRef("patch_publication_date")
    publication_date: PropertyRef = PropertyRef("publication_date")
    modification_date: PropertyRef = PropertyRef("modification_date")
    vuln_publication_date: PropertyRef = PropertyRef("vuln_publication_date")
    cvss_base_score: PropertyRef = PropertyRef("cvss_base_score")
    cvss_temporal_score: PropertyRef = PropertyRef("cvss_temporal_score")
    cvss3_base_score: PropertyRef = PropertyRef("cvss3_base_score")
    cvss3_temporal_score: PropertyRef = PropertyRef("cvss3_temporal_score")
    cvss4_base_score: PropertyRef = PropertyRef("cvss4_base_score")
    vpr_score: PropertyRef = PropertyRef("vpr_score")
    epss_score: PropertyRef = PropertyRef("epss_score")
    cve_list: PropertyRef = PropertyRef("cve_list")
    type: PropertyRef = PropertyRef("type")


@dataclass(frozen=True)
class TenablePluginToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenablePlugin)
@dataclass(frozen=True)
class TenablePluginToTenantRel(CartographyRelSchema):
    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenablePluginToTenantRelProperties = (
        TenablePluginToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenablePluginSchema(CartographyNodeSchema):
    label: str = "TenablePlugin"
    properties: TenablePluginNodeProperties = TenablePluginNodeProperties()
    sub_resource_relationship: TenablePluginToTenantRel = TenablePluginToTenantRel()
