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
class CircleCIProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    slug: PropertyRef = PropertyRef("slug", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    organization_name: PropertyRef = PropertyRef("organization_name")
    organization_slug: PropertyRef = PropertyRef("organization_slug")
    organization_id: PropertyRef = PropertyRef("organization_id")
    vcs_url: PropertyRef = PropertyRef("vcs_url")
    vcs_provider: PropertyRef = PropertyRef("vcs_provider")
    default_branch: PropertyRef = PropertyRef("default_branch")


@dataclass(frozen=True)
class CircleCIProjectToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:RESOURCE]->(:CircleCIProject)
class CircleCIProjectToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "CircleCIOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIProjectToOrganizationRelProperties = (
        CircleCIProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class CircleCIProjectToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:BUILDS]->(:GitHubRepository), joined on the repo URL.
# Best-effort: only created if the GitHub repo was ingested (OPTIONAL MATCH).
class CircleCIProjectToGitHubRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"url": PropertyRef("vcs_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILDS"
    properties: CircleCIProjectToRepoRelProperties = (
        CircleCIProjectToRepoRelProperties()
    )


@dataclass(frozen=True)
# (:CircleCIProject)-[:BUILDS]->(:GitLabProject), joined on the repo URL.
class CircleCIProjectToGitLabProjectRel(CartographyRelSchema):
    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"web_url": PropertyRef("vcs_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILDS"
    properties: CircleCIProjectToRepoRelProperties = (
        CircleCIProjectToRepoRelProperties()
    )


@dataclass(frozen=True)
class CircleCIProjectSchema(CartographyNodeSchema):
    label: str = "CircleCIProject"
    properties: CircleCIProjectNodeProperties = CircleCIProjectNodeProperties()
    sub_resource_relationship: CircleCIProjectToOrganizationRel = (
        CircleCIProjectToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CircleCIProjectToGitHubRepoRel(),
            CircleCIProjectToGitLabProjectRel(),
        ],
    )
