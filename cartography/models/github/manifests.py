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
class DependencyGraphManifestNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    blob_path: PropertyRef = PropertyRef("blob_path")
    filename: PropertyRef = PropertyRef("filename")
    dependencies_count: PropertyRef = PropertyRef("dependencies_count")
    repo_url: PropertyRef = PropertyRef("repo_url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DependencyGraphManifestToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DependencyGraphManifestToOrganizationRel(CartographyRelSchema):
    """
    Sub-resource relationship: (GitHubOrganization)-[:RESOURCE]->(DependencyGraphManifest).
    Manifests are scoped to the organization for cleanup purposes so that a single
    GraphJob run cleans up manifests from every repo in the org.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_org_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DependencyGraphManifestToOrganizationRelProperties = (
        DependencyGraphManifestToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class DependencyGraphManifestToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DependencyGraphManifestToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_MANIFEST"
    properties: DependencyGraphManifestToRepositoryRelProperties = (
        DependencyGraphManifestToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class DependencyGraphManifestSchema(CartographyNodeSchema):
    label: str = "DependencyGraphManifest"
    properties: DependencyGraphManifestNodeProperties = (
        DependencyGraphManifestNodeProperties()
    )
    sub_resource_relationship: DependencyGraphManifestToOrganizationRel = (
        DependencyGraphManifestToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DependencyGraphManifestToRepositoryRel()]
    )
