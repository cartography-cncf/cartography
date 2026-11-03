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
class CVEMetadataNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="CVE identifier.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # NVD fields
    description: PropertyRef = PropertyRef(
        "description_en", description="English description of the vulnerability."
    )
    references: PropertyRef = PropertyRef(
        "references_urls", description="Reference URLs for the vulnerability."
    )
    problem_types: PropertyRef = PropertyRef(
        "weaknesses", description="CWE identifiers associated with the vulnerability."
    )
    # Technical-effect labels derived from CWE (preferred) or CVSS fallback.
    effect_tags: PropertyRef = PropertyRef(
        "effect_tags",
        description=(
            "Controlled technical effects derived from mapped CWEs when available, "
            "otherwise from high CVSS confidentiality, integrity, and availability "
            "impacts plus the network straight-shot rule. Values are execute-code, "
            "gain-privileges, access-credentials, bypass-control, disclose-data, "
            "tamper-data, and deny-service."
        ),
    )
    effect_tags_source: PropertyRef = PropertyRef(
        "effect_tags_source",
        description=(
            "Derivation source for effect_tags: cwe takes strict precedence over "
            "the cvss fallback, and none indicates that no usable effects were found."
        ),
    )
    cvss_version: PropertyRef = PropertyRef(
        "cvss_version", description="CVSS version selected from the NVD metrics."
    )
    vector_string: PropertyRef = PropertyRef(
        "vectorString", description="CVSS vector string."
    )
    attack_vector: PropertyRef = PropertyRef(
        "attackVector", description="CVSS attack vector metric."
    )
    attack_complexity: PropertyRef = PropertyRef(
        "attackComplexity", description="CVSS attack complexity metric."
    )
    privileges_required: PropertyRef = PropertyRef(
        "privilegesRequired", description="CVSS privileges required metric."
    )
    user_interaction: PropertyRef = PropertyRef(
        "userInteraction", description="CVSS user interaction metric."
    )
    scope: PropertyRef = PropertyRef("scope", description="CVSS scope metric.")
    confidentiality_impact: PropertyRef = PropertyRef(
        "confidentialityImpact", description="CVSS confidentiality impact metric."
    )
    integrity_impact: PropertyRef = PropertyRef(
        "integrityImpact", description="CVSS integrity impact metric."
    )
    availability_impact: PropertyRef = PropertyRef(
        "availabilityImpact", description="CVSS availability impact metric."
    )
    base_score: PropertyRef = PropertyRef("baseScore", description="CVSS base score.")
    base_severity: PropertyRef = PropertyRef(
        "baseSeverity", description="CVSS base severity rating."
    )
    exploitability_score: PropertyRef = PropertyRef(
        "exploitabilityScore", description="CVSS exploitability score."
    )
    impact_score: PropertyRef = PropertyRef(
        "impactScore", description="CVSS impact score."
    )
    published_date: PropertyRef = PropertyRef(
        "published", description="Date and time when the CVE was published."
    )
    last_modified_date: PropertyRef = PropertyRef(
        "lastModified", description="Date and time when the CVE was last modified."
    )
    vuln_status: PropertyRef = PropertyRef(
        "vulnStatus", description="NVD vulnerability analysis status."
    )
    is_kev: PropertyRef = PropertyRef(
        "is_kev",
        extra_index=True,
        description=(
            "Whether the CVE appears in the CISA Known Exploited Vulnerabilities "
            "(KEV) catalog. Read from the catalog itself when the kev source is "
            "enabled and the catalog was fetched; otherwise from the KEV fields "
            "that NVD embeds in its records, which can lag the catalog. Unset when "
            "neither source has an answer."
        ),
    )
    is_kev_source: PropertyRef = PropertyRef(
        "is_kev_source",
        description=(
            "Where is_kev came from: kev for the CISA KEV catalog, nvd for the "
            "copy embedded in NVD records. Unset when is_kev is unset."
        ),
    )
    # CISA KEV catalog fields, set only when is_kev_source is kev
    kev_date_added: PropertyRef = PropertyRef(
        "kev_date_added",
        description="Date (YYYY-MM-DD) CISA added the CVE to the KEV catalog.",
    )
    kev_due_date: PropertyRef = PropertyRef(
        "kev_due_date",
        description=(
            "Remediation due date (YYYY-MM-DD) the KEV catalog sets for US "
            "federal civilian agencies."
        ),
    )
    kev_ransomware_use: PropertyRef = PropertyRef(
        "kev_ransomware_use",
        description=(
            "KEV knownRansomwareCampaignUse: Known when the CVE is known to be "
            "used in ransomware campaigns, otherwise Unknown."
        ),
    )
    kev_forensic_triage: PropertyRef = PropertyRef(
        "kev_forensic_triage",
        description=(
            "KEV forensicTriage: true when the catalog entry calls for CISA's "
            "forensics triage requirements on affected systems in addition to "
            "remediation, false when it does not."
        ),
    )
    # NVD KEV fields (from CISA data embedded in NVD responses)
    cisa_exploit_add: PropertyRef = PropertyRef(
        "cisaExploitAdd",
        description=(
            "Date when CISA added the CVE to the KEV catalog, as copied into the "
            "NVD record."
        ),
    )
    cisa_action_due: PropertyRef = PropertyRef(
        "cisaActionDue",
        description="CISA KEV remediation due date, as copied into the NVD record.",
    )
    cisa_required_action: PropertyRef = PropertyRef(
        "cisaRequiredAction", description="Remediation action required by CISA."
    )
    cisa_vulnerability_name: PropertyRef = PropertyRef(
        "cisaVulnerabilityName", description="CISA vulnerability name."
    )
    # EPSS fields
    epss_score: PropertyRef = PropertyRef(
        "epss_score", description="EPSS probability of exploitation from 0.0 to 1.0."
    )
    epss_percentile: PropertyRef = PropertyRef(
        "epss_percentile", description="EPSS percentile ranking from 0.0 to 1.0."
    )
    # CISA Vulnrichment SSVC fields, from CISA's ADP container
    ssvc_exploitation: PropertyRef = PropertyRef(
        "ssvc_exploitation",
        description=(
            "SSVC Exploitation decision point: none, poc (a public proof of "
            "concept exists), or active (evidence of exploitation in the wild)."
        ),
    )
    ssvc_automatable: PropertyRef = PropertyRef(
        "ssvc_automatable",
        description=(
            "SSVC Automatable decision point: yes when an attacker can reliably "
            "automate steps 1 to 4 of the kill chain, otherwise no."
        ),
    )
    ssvc_technical_impact: PropertyRef = PropertyRef(
        "ssvc_technical_impact",
        description=(
            "SSVC Technical Impact decision point: total when exploitation gives "
            "the attacker total control of the affected software or total "
            "disclosure of its information, otherwise partial."
        ),
    )
    ssvc_version: PropertyRef = PropertyRef(
        "ssvc_version", description="Version of the SSVC decision model used."
    )
    ssvc_timestamp: PropertyRef = PropertyRef(
        "ssvc_timestamp", description="When CISA made the SSVC decision."
    )
    vulnrichment_updated_at: PropertyRef = PropertyRef(
        "vulnrichment_updated_at",
        description=(
            "When the CVE record in CISA Vulnrichment was last updated. Set "
            "whenever Vulnrichment has a record for the CVE, even one without an "
            "SSVC decision."
        ),
    )


# Relationships
@dataclass(frozen=True)
class CVEMetadataToFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CVEMetadata)<-[:RESOURCE]-(:CVEMetadataFeed)
class CVEMetadataToFeedRel(CartographyRelSchema):
    """A CVE metadata feed contains CVE metadata as a managed resource."""

    target_node_label: str = "CVEMetadataFeed"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FEED_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CVEMetadataToFeedRelProperties = CVEMetadataToFeedRelProperties()


@dataclass(frozen=True)
class CVEMetadataToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CVEMetadata)-[:ENRICHES]->(:CVE)
# Matches every node carrying the :CVE label with a matching cve_id: the deprecated
# CVE node plus all finding nodes that now carry the :CVE semantic label (e.g.
# AWSInspectorFinding, SemgrepSCAFinding, TrivyImageFinding). Findings that load
# after cve_metadata in a given sync are enriched on the next run; stale edges are
# pruned by lastupdated cleanup.
class CVEMetadataToCVERel(CartographyRelSchema):
    """CVE metadata enriches its corresponding CVE."""

    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"cve_id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENRICHES"
    properties: CVEMetadataToCVERelProperties = CVEMetadataToCVERelProperties()


@dataclass(frozen=True)
class CVEMetadataSchema(CartographyNodeSchema):
    """
    Enrichment metadata for a CVE, sourced from NVD, EPSS, the CISA KEV catalog,
    and CISA Vulnrichment.
    """

    label: str = "CVEMetadata"
    properties: CVEMetadataNodeProperties = CVEMetadataNodeProperties()
    sub_resource_relationship: CVEMetadataToFeedRel = CVEMetadataToFeedRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CVEMetadataToCVERel(),
        ],
    )
