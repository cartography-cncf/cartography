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
class GitLabProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    url: PropertyRef = PropertyRef("url")
    created_at: PropertyRef = PropertyRef("created_at")
    last_activity_at: PropertyRef = PropertyRef("last_activity_at")


@dataclass(frozen=True)
class GitLabProjectToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitLabRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SOURCE_CODE"
    properties: GitLabProjectToRepositoryRelProperties = GitLabProjectToRepositoryRelProperties()


@dataclass(frozen=True)
class GitLabProjectSchema(CartographyNodeSchema):
    label: str = "GitLabProject"
    properties: GitLabProjectNodeProperties = GitLabProjectNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            GitLabProjectToRepositoryRel(),
        ],
    )
