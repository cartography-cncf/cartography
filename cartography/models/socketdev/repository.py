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
class SocketDevRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique Socket.dev repository identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Repository name.",
    )
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="Repository slug.",
    )
    fullname: PropertyRef = PropertyRef(
        "fullname",
        extra_index=True,
        description="Full repository path including its workspace.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Repository description.",
    )
    visibility: PropertyRef = PropertyRef(
        "visibility",
        description="Repository visibility.",
    )
    archived: PropertyRef = PropertyRef(
        "archived",
        description="Whether the repository is archived.",
    )
    default_branch: PropertyRef = PropertyRef(
        "default_branch",
        description="Default branch name.",
    )
    homepage: PropertyRef = PropertyRef(
        "homepage",
        description="Repository homepage URL.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Repository creation timestamp.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Repository last update timestamp.",
    )


@dataclass(frozen=True)
class SocketDevOrgToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevOrganization)-[:RESOURCE]->(:SocketDevRepository)
class SocketDevOrgToRepositoryRel(CartographyRelSchema):
    """Links a Socket.dev organization to one of its repositories."""

    target_node_label: str = "SocketDevOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SocketDevOrgToRepositoryRelProperties = (
        SocketDevOrgToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class SocketDevRepoToCodeRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevRepository)-[:MONITORS]->(:CodeRepository)
class SocketDevRepoToCodeRepoRel(CartographyRelSchema):
    """Links a Socket.dev repository to the code repository it monitors."""

    target_node_label: str = "CodeRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"_ont_fullname": PropertyRef("fullname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: SocketDevRepoToCodeRepoRelProperties = (
        SocketDevRepoToCodeRepoRelProperties()
    )


@dataclass(frozen=True)
class SocketDevRepositorySchema(CartographyNodeSchema):
    """A source code repository monitored by Socket.dev."""

    label: str = "SocketDevRepository"
    properties: SocketDevRepositoryNodeProperties = SocketDevRepositoryNodeProperties()
    sub_resource_relationship: SocketDevOrgToRepositoryRel = (
        SocketDevOrgToRepositoryRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SocketDevRepoToCodeRepoRel(),
        ],
    )
