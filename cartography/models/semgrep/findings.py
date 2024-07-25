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
class SemgrepSCAFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    rule_id: PropertyRef = PropertyRef('ruleId', extra_index=True)
    repository: PropertyRef = PropertyRef('repositoryName', extra_index=True)
    branch: PropertyRef = PropertyRef('branch')
    summary: PropertyRef = PropertyRef('title', extra_index=True)
    description: PropertyRef = PropertyRef('description')
    package_manager: PropertyRef = PropertyRef('ecosystem')
    severity: PropertyRef = PropertyRef('severity')
    cve_id: PropertyRef = PropertyRef('cveId', extra_index=True)
    reachability_check: PropertyRef = PropertyRef('reachability')
    reachability_condition: PropertyRef = PropertyRef('reachableIf')
    reachability: PropertyRef = PropertyRef('exposureType')
    transitivity: PropertyRef = PropertyRef('transitivity')
    dependency: PropertyRef = PropertyRef('matchedDependency')
    dependency_fix: PropertyRef = PropertyRef('closestSafeDependency')
    ref_urls: PropertyRef = PropertyRef('ref_urls')
    dependency_file: PropertyRef = PropertyRef('dependencyFileLocation_path', extra_index=True)
    dependency_file_url: PropertyRef = PropertyRef('dependencyFileLocation_url', extra_index=True)
    scan_time: PropertyRef = PropertyRef('openedAt')
    fix_status: PropertyRef = PropertyRef('fixStatus')
    triage_status: PropertyRef = PropertyRef('triageStatus')
    confidence: PropertyRef = PropertyRef('confidence')


@dataclass(frozen=True)
class SemgrepSCAFindingToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepSCAFindingToSemgrepDeploymentSchema(CartographyRelSchema):
    target_node_label: str = 'SemgrepDeployment'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DEPLOYMENT_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepSCAFindingToSemgrepDeploymentRelProperties = SemgrepSCAFindingToSemgrepDeploymentRelProperties()


@dataclass(frozen=True)
class SemgrepSCAFindingToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)-[:FOUND_IN]->(:GitHubRepository)
class SemgrepSCAFindingToGithubRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'fullname': PropertyRef('repositoryName')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SemgrepSCAFindingToGithubRepoRelProperties = SemgrepSCAFindingToGithubRepoRelProperties()


@dataclass(frozen=True)
class SemgrepSCAFindngToDependencyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)-[:AFFECTS]->(:Dependency)
class SemgrepSCAFindingToDependencyRel(CartographyRelSchema):
    target_node_label: str = 'Dependency'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('matchedDependency')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AFFECTS"
    properties: SemgrepSCAFindngToDependencyRelProperties = SemgrepSCAFindngToDependencyRelProperties()


@dataclass(frozen=True)
class SemgrepSCAFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepSCAFinding)<-[:LINKED_TO]-(:CVE)
class SemgrepSCAFindingToCVERel(CartographyRelSchema):
    target_node_label: str = 'CVE'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('cveId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LINKED_TO"
    properties: SemgrepSCAFindingToCVERelProperties = SemgrepSCAFindingToCVERelProperties()


@dataclass(frozen=True)
class SemgrepSCAFindingSchema(CartographyNodeSchema):
    label: str = 'SemgrepSCAFinding'
    properties: SemgrepSCAFindingNodeProperties = SemgrepSCAFindingNodeProperties()
    sub_resource_relationship: SemgrepSCAFindingToSemgrepDeploymentSchema = SemgrepSCAFindingToSemgrepDeploymentSchema()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepSCAFindingToGithubRepoRel(),
            SemgrepSCAFindingToDependencyRel(),
            SemgrepSCAFindingToCVERel(),
        ],
    )
