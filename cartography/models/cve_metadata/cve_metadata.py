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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # NVD fields
    description: PropertyRef = PropertyRef("description_en")
    references: PropertyRef = PropertyRef("references_urls")
    problem_types: PropertyRef = PropertyRef("weaknesses")
    cvss_version: PropertyRef = PropertyRef("cvss_version")
    vector_string: PropertyRef = PropertyRef("vectorString")
    attack_vector: PropertyRef = PropertyRef("attackVector")
    attack_complexity: PropertyRef = PropertyRef("attackComplexity")
    privileges_required: PropertyRef = PropertyRef("privilegesRequired")
    user_interaction: PropertyRef = PropertyRef("userInteraction")
    scope: PropertyRef = PropertyRef("scope")
    confidentiality_impact: PropertyRef = PropertyRef("confidentialityImpact")
    integrity_impact: PropertyRef = PropertyRef("integrityImpact")
    availability_impact: PropertyRef = PropertyRef("availabilityImpact")
    base_score: PropertyRef = PropertyRef("baseScore")
    base_severity: PropertyRef = PropertyRef("baseSeverity")
    exploitability_score: PropertyRef = PropertyRef("exploitabilityScore")
    impact_score: PropertyRef = PropertyRef("impactScore")
    published_date: PropertyRef = PropertyRef("published")
    last_modified_date: PropertyRef = PropertyRef("lastModified")
    vuln_status: PropertyRef = PropertyRef("vulnStatus")
    # NVD KEV fields (from CISA data embedded in NVD responses)
    is_kev: PropertyRef = PropertyRef("is_kev", extra_index=True)
    cisa_exploit_add: PropertyRef = PropertyRef("cisaExploitAdd")
    cisa_action_due: PropertyRef = PropertyRef("cisaActionDue")
    cisa_required_action: PropertyRef = PropertyRef("cisaRequiredAction")
    cisa_vulnerability_name: PropertyRef = PropertyRef("cisaVulnerabilityName")
    # EPSS fields
    epss_score: PropertyRef = PropertyRef("epss_score")
    epss_percentile: PropertyRef = PropertyRef("epss_percentile")


# Relationships
@dataclass(frozen=True)
class CVEMetadataToFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CVEMetadata)<-[:RESOURCE]-(:CVEMetadataFeed)
class CVEMetadataToFeedRel(CartographyRelSchema):
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
class CVEMetadataToCVERel(CartographyRelSchema):
    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"cve_id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENRICHES"
    properties: CVEMetadataToCVERelProperties = CVEMetadataToCVERelProperties()


@dataclass(frozen=True)
class CVEMetadataSchema(CartographyNodeSchema):
    label: str = "CVEMetadata"
    properties: CVEMetadataNodeProperties = CVEMetadataNodeProperties()
    sub_resource_relationship: CVEMetadataToFeedRel = CVEMetadataToFeedRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CVEMetadataToCVERel(),
        ],
    )
