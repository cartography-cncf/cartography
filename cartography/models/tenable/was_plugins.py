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
    id: PropertyRef = PropertyRef("id", description="Tenable WAS plugin ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Plugin name.")
    risk_factor: PropertyRef = PropertyRef(
        "risk_factor", description="Qualitative plugin risk factor."
    )
    type: PropertyRef = PropertyRef("type", description="Plugin scan type.")
    synopsis: PropertyRef = PropertyRef(
        "synopsis", description="Short summary of the plugin check."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Detailed plugin description."
    )
    solution: PropertyRef = PropertyRef(
        "solution", description="Recommended remediation."
    )
    publication_date: PropertyRef = PropertyRef(
        "publication_date", description="Date the plugin was published."
    )
    modification_date: PropertyRef = PropertyRef(
        "modification_date", description="Date the plugin was last modified."
    )
    patch_publication_date: PropertyRef = PropertyRef(
        "patch_publication_date", description="Date the patch was published."
    )
    exploitability_ease: PropertyRef = PropertyRef(
        "exploitability_ease", description="Ease of exploitation."
    )
    in_the_news: PropertyRef = PropertyRef(
        "in_the_news", description="Whether the vulnerability is in the news."
    )
    exploited_by_malware: PropertyRef = PropertyRef(
        "exploited_by_malware",
        description="Whether malware is known to exploit the vulnerability.",
    )
    cvss2_base_score: PropertyRef = PropertyRef(
        "cvss2_base_score", description="CVSS v2 base score."
    )
    cvss3_base_score: PropertyRef = PropertyRef(
        "cvss3_base_score", description="CVSS v3 base score."
    )
    cvss4_base_score: PropertyRef = PropertyRef(
        "cvss4_base_score", description="CVSS v4 base score."
    )
    vpr_score: PropertyRef = PropertyRef(
        "vpr_score", description="Tenable Vulnerability Priority Rating score."
    )
    epss_score: PropertyRef = PropertyRef(
        "epss_score", description="Exploit Prediction Scoring System score."
    )
    # Deliberately not indexed, for the same reason as TenablePlugin.cve_list.
    cve_list: PropertyRef = PropertyRef(
        "cve_list",
        description="CVE IDs the plugin checks for. To look up by CVE, use `HAS_CVE`.",
    )
    cwe_ids: PropertyRef = PropertyRef(
        "cwe_ids", description="CWE IDs the plugin checks for."
    )


@dataclass(frozen=True)
class TenableWASPluginToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenableWASPlugin)
@dataclass(frozen=True)
class TenableWASPluginToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to one of its web application scanning plugins."""

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
    """A Tenable Web App Scanning plugin that detected one or more findings."""

    label: str = "TenableWASPlugin"
    properties: TenableWASPluginNodeProperties = TenableWASPluginNodeProperties()
    sub_resource_relationship: TenableWASPluginToTenantRel = (
        TenableWASPluginToTenantRel()
    )
