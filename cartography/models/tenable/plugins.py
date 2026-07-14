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
    id: PropertyRef = PropertyRef("id", description="Tenable plugin ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef("name", description="Plugin name.")
    family: PropertyRef = PropertyRef("family", description="Plugin family name.")
    family_id: PropertyRef = PropertyRef("family_id", description="Plugin family ID.")
    description: PropertyRef = PropertyRef(
        "description", description="Detailed plugin description."
    )
    synopsis: PropertyRef = PropertyRef(
        "synopsis", description="Short summary of the plugin check."
    )
    solution: PropertyRef = PropertyRef(
        "solution", description="Recommended remediation."
    )
    risk_factor: PropertyRef = PropertyRef(
        "risk_factor", description="Qualitative plugin risk factor."
    )
    has_patch: PropertyRef = PropertyRef(
        "has_patch", description="Whether a vendor patch is available."
    )
    has_workaround: PropertyRef = PropertyRef(
        "has_workaround", description="Whether a workaround is available."
    )
    vendor_unpatched: PropertyRef = PropertyRef(
        "vendor_unpatched", description="Whether the vendor has not issued a patch."
    )
    vendor_severity: PropertyRef = PropertyRef(
        "vendor_severity", description="Vendor-assigned severity."
    )
    exploit_available: PropertyRef = PropertyRef(
        "exploit_available", description="Whether a known exploit is available."
    )
    exploitability_ease: PropertyRef = PropertyRef(
        "exploitability_ease", description="Ease of exploitation."
    )
    exploit_framework_metasploit: PropertyRef = PropertyRef(
        "exploit_framework_metasploit",
        description="Whether a Metasploit module is available.",
    )
    patch_publication_date: PropertyRef = PropertyRef(
        "patch_publication_date", description="Date the patch was published."
    )
    publication_date: PropertyRef = PropertyRef(
        "publication_date", description="Date the plugin was published."
    )
    modification_date: PropertyRef = PropertyRef(
        "modification_date", description="Date the plugin was last modified."
    )
    vuln_publication_date: PropertyRef = PropertyRef(
        "vuln_publication_date",
        description="Date the vulnerability was published.",
    )
    cvss_base_score: PropertyRef = PropertyRef(
        "cvss_base_score", description="CVSS v2 base score."
    )
    cvss_temporal_score: PropertyRef = PropertyRef(
        "cvss_temporal_score", description="CVSS v2 temporal score."
    )
    cvss3_base_score: PropertyRef = PropertyRef(
        "cvss3_base_score", description="CVSS v3 base score."
    )
    cvss3_temporal_score: PropertyRef = PropertyRef(
        "cvss3_temporal_score", description="CVSS v3 temporal score."
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
    cve_list: PropertyRef = PropertyRef(
        "cve_list", description="CVE IDs associated with the plugin."
    )
    type: PropertyRef = PropertyRef("type", description="Plugin scan type.")


@dataclass(frozen=True)
class TenablePluginToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:TenableTenant)-[:RESOURCE]->(:TenablePlugin)
@dataclass(frozen=True)
class TenablePluginToTenantRel(CartographyRelSchema):
    """Links a Tenable tenant to one of its vulnerability plugins."""

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
    """A Tenable plugin that detected one or more findings."""

    label: str = "TenablePlugin"
    properties: TenablePluginNodeProperties = TenablePluginNodeProperties()
    sub_resource_relationship: TenablePluginToTenantRel = TenablePluginToTenantRel()
