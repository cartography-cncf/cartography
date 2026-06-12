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
class TenableWASPluginNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    risk_factor: PropertyRef = PropertyRef("risk_factor")
    type: PropertyRef = PropertyRef("type")
    synopsis: PropertyRef = PropertyRef("synopsis")
    description: PropertyRef = PropertyRef("description")
    solution: PropertyRef = PropertyRef("solution")
    publication_date: PropertyRef = PropertyRef("publication_date")
    modification_date: PropertyRef = PropertyRef("modification_date")
    patch_publication_date: PropertyRef = PropertyRef("patch_publication_date")
    exploitability_ease: PropertyRef = PropertyRef("exploitability_ease")
    in_the_news: PropertyRef = PropertyRef("in_the_news")
    exploited_by_malware: PropertyRef = PropertyRef("exploited_by_malware")
    cvss2_base_score: PropertyRef = PropertyRef("cvss2_base_score")
    cvss3_base_score: PropertyRef = PropertyRef("cvss3_base_score")
    cvss4_base_score: PropertyRef = PropertyRef("cvss4_base_score")
    vpr_score: PropertyRef = PropertyRef("vpr_score")
    vpr_v2_score: PropertyRef = PropertyRef("vpr_v2_score")
    epss_score: PropertyRef = PropertyRef("epss_score")
    cve_ids: PropertyRef = PropertyRef("cve_ids")
    cwe_ids: PropertyRef = PropertyRef("cwe_ids")


@dataclass(frozen=True)
class TenableWASPluginToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableWASPlugin)
@dataclass(frozen=True)
class TenableWASPluginToTenantRel(CartographyRelSchema):
    target_node_label: str = "TenableTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENABLE_TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TenableWASPluginToTenantRelProperties = (
        TenableWASPluginToTenantRelProperties()
    )


@dataclass(frozen=True)
class TenableWASPluginSchema(CartographyNodeSchema):
    label: str = "TenableWASPlugin"
    properties: TenableWASPluginNodeProperties = TenableWASPluginNodeProperties()
    sub_resource_relationship: TenableWASPluginToTenantRel = (
        TenableWASPluginToTenantRel()
    )
