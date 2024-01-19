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
class CVENodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    assigner: PropertyRef = PropertyRef('sourceIdentifier')
    description: PropertyRef = PropertyRef('descriptions_en')
    references: PropertyRef = PropertyRef('references_urls')
    problem_types: PropertyRef = PropertyRef('weaknesses')
    vector_string: PropertyRef = PropertyRef('vectorString')
    attack_vector: PropertyRef = PropertyRef('attackVector')
    attack_complexity: PropertyRef = PropertyRef('attackComplexity')
    privileges_required: PropertyRef = PropertyRef('privilegesRequired')
    user_interaction: PropertyRef = PropertyRef('userInteraction')
    scope: PropertyRef = PropertyRef('scope')
    confidentiality_impact: PropertyRef = PropertyRef('confidentialityImpact')
    integrity_impact: PropertyRef = PropertyRef('integrityImpact')
    availability_impact: PropertyRef = PropertyRef('availabilityImpact')
    base_score: PropertyRef = PropertyRef('baseScore')
    base_severity: PropertyRef = PropertyRef('baseSeverity')
    exploitability_score: PropertyRef = PropertyRef('exploitabilityScore')
    impact_score: PropertyRef = PropertyRef('impactScore')
    published_date: PropertyRef = PropertyRef('published')
    last_modified_date: PropertyRef = PropertyRef('lastModified')
    vuln_status: PropertyRef = PropertyRef('vulnStatus')
    lastupdated: PropertyRef = PropertyRef('lastupdated')


@dataclass(frozen=True)
class CVEtoCVEFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CVE)<-[:RESOURCE]-(:CVEFeed)
class CVEtoCVEFeedRelSchema(CartographyRelSchema):
    target_node_label: str = 'CVEFeed'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('FEED_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CVEtoCVEFeedRelProperties = CVEtoCVEFeedRelProperties()


@dataclass(frozen=True)
class CVEToSpotlightVulnerabilityRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:CVE)<-[:HAS_CVE]-(:SpotlightVulnerability)
class CVEToSpotlightVulnerabilityRel(CartographyRelSchema):
    target_node_label: str = 'SpotlightVulnerability'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CVE"
    properties: CVEToSpotlightVulnerabilityRelProperties = CVEToSpotlightVulnerabilityRelProperties()


@dataclass(frozen=True)
class CVESchema(CartographyNodeSchema):
    label: str = 'CVE'
    properties: CVENodeProperties = CVENodeProperties()
    sub_resource_relationship: CVEtoCVEFeedRelSchema = CVEtoCVEFeedRelSchema()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CVEToSpotlightVulnerabilityRel(),
        ],
    )
