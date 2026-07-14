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


# TODO: CVE should be an ontology node so that it can be used as an extra label
# by other modules (e.g. SemgrepSCAFinding, UbuntuCVE, SentinelOneFinding, TrivyFinding).
# Those nodes define their own cve_id property with extra_index=True; this node
# mirrors that field so that queries on CVE.cve_id are indexed consistently.
@dataclass(frozen=True)
class CVENodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="CVE identifier.")
    cve_id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description="CVE identifier indexed for cross-module correlation.",
    )
    assigner: PropertyRef = PropertyRef(
        "sourceIdentifier",
        description="Organization or authority that assigned the CVE.",
    )
    description: PropertyRef = PropertyRef(
        "descriptions_en",
        description="English description of the vulnerability.",
    )
    references: PropertyRef = PropertyRef(
        "references_urls",
        description="Reference URLs for the vulnerability.",
    )
    problem_types: PropertyRef = PropertyRef(
        "weaknesses",
        description="CWE identifiers associated with the vulnerability.",
    )
    vector_string: PropertyRef = PropertyRef(
        "vectorString",
        description="CVSS vector string.",
    )
    attack_vector: PropertyRef = PropertyRef(
        "attackVector",
        description="CVSS attack vector.",
    )
    attack_complexity: PropertyRef = PropertyRef(
        "attackComplexity",
        description="CVSS attack complexity.",
    )
    privileges_required: PropertyRef = PropertyRef(
        "privilegesRequired",
        description="CVSS privileges required.",
    )
    user_interaction: PropertyRef = PropertyRef(
        "userInteraction",
        description="CVSS user interaction requirement.",
    )
    scope: PropertyRef = PropertyRef("scope", description="CVSS scope.")
    confidentiality_impact: PropertyRef = PropertyRef(
        "confidentialityImpact",
        description="CVSS confidentiality impact.",
    )
    integrity_impact: PropertyRef = PropertyRef(
        "integrityImpact",
        description="CVSS integrity impact.",
    )
    availability_impact: PropertyRef = PropertyRef(
        "availabilityImpact",
        description="CVSS availability impact.",
    )
    base_score: PropertyRef = PropertyRef(
        "baseScore",
        description="CVSS base score.",
    )
    base_severity: PropertyRef = PropertyRef(
        "baseSeverity",
        description="CVSS base severity.",
    )
    exploitability_score: PropertyRef = PropertyRef(
        "exploitabilityScore",
        description="CVSS exploitability score.",
    )
    impact_score: PropertyRef = PropertyRef(
        "impactScore",
        description="CVSS impact score.",
    )
    published_date: PropertyRef = PropertyRef(
        "published",
        description="Timestamp when the CVE was published.",
    )
    last_modified_date: PropertyRef = PropertyRef(
        "lastModified",
        description="Timestamp when the CVE was last modified.",
    )
    vuln_status: PropertyRef = PropertyRef(
        "vulnStatus",
        description="Current status assigned to the vulnerability.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
class CVEtoCVEFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:CVE)<-[:RESOURCE]-(:CVEFeed)
class CVEtoCVEFeedRel(CartographyRelSchema):
    """A CVE feed contains the CVEs imported from that feed."""

    target_node_label: str = "CVEFeed"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FEED_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CVEtoCVEFeedRelProperties = CVEtoCVEFeedRelProperties()


@dataclass(frozen=True)
class CVEToSpotlightVulnerabilityRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:CVE)<-[:HAS_CVE]-(:SpotlightVulnerability)
class CVEToSpotlightVulnerabilityRel(CartographyRelSchema):
    """A CrowdStrike Spotlight vulnerability references this CVE."""

    target_node_label: str = "SpotlightVulnerability"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CVE"
    properties: CVEToSpotlightVulnerabilityRelProperties = (
        CVEToSpotlightVulnerabilityRelProperties()
    )


@dataclass(frozen=True)
class CVESchema(CartographyNodeSchema):
    """A published Common Vulnerabilities and Exposures record."""

    label: str = "CVE"
    properties: CVENodeProperties = CVENodeProperties()
    sub_resource_relationship: CVEtoCVEFeedRel = CVEtoCVEFeedRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CVEToSpotlightVulnerabilityRel(),
        ],
    )
