from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SemgrepDependencyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name')
    ecosystem: PropertyRef = PropertyRef('ecosystem')
    version: PropertyRef = PropertyRef('version')


@dataclass(frozen=True)
class SemgrepDependencyToSemgrepDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:SemgrepDependency)<-[:RESOURCE]-(:SemgrepDeployment)
class SemgrepDependencyToSemgrepDeploymentSchema(CartographyRelSchema):
    target_node_label: str = 'SemgrepDeployment'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DEPLOYMENT_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SemgrepDependencyToSemgrepDeploymentRelProperties = SemgrepDependencyToSemgrepDeploymentRelProperties()


@dataclass(frozen=True)
class SemgrepDependencyToGithubRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    specifier: PropertyRef = PropertyRef('specifier')
    transitivity: PropertyRef = PropertyRef('transitivity')
    url: PropertyRef = PropertyRef('url')


@dataclass(frozen=True)
# (:SemgrepDependency)<-[:REQUIRES]-(:GitHubRepository)
class SemgrepDependencyToGithubRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('repo_url')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REQUIRES"
    properties: SemgrepDependencyToGithubRepoRelProperties = SemgrepDependencyToGithubRepoRelProperties()


@dataclass(frozen=True)
class SemgrepSCAFindngToDependencyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SemgrepGoLibrarySchema(CartographyNodeSchema):
    label: str = 'GoLibrary'
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(['Dependency', 'SemgrepDependency'])
    properties: SemgrepDependencyNodeProperties = SemgrepDependencyNodeProperties()
    sub_resource_relationship: SemgrepDependencyToSemgrepDeploymentSchema = SemgrepDependencyToSemgrepDeploymentSchema()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepDependencyToGithubRepoRel(),
        ],
    )


@dataclass(frozen=True)
class SemgrepNpmLibrarySchema(CartographyNodeSchema):
    label: str = 'NpmLibrary'
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(['Dependency', 'SemgrepDependency'])
    properties: SemgrepDependencyNodeProperties = SemgrepDependencyNodeProperties()
    sub_resource_relationship: SemgrepDependencyToSemgrepDeploymentSchema = SemgrepDependencyToSemgrepDeploymentSchema()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SemgrepDependencyToGithubRepoRel(),
        ],
    )
