from dataclasses import dataclass

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
class SocketDevDependencyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique Socket.dev dependency identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Package name.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Package version.",
    )
    ecosystem: PropertyRef = PropertyRef(
        "type",
        description="Package ecosystem.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        description="Package namespace, when applicable.",
    )
    normalized_id: PropertyRef = PropertyRef(
        "normalized_id",
        extra_index=True,
        description="Normalized package identifier used for cross-tool matching.",
    )
    direct: PropertyRef = PropertyRef(
        "direct",
        description="Whether this is a direct dependency.",
    )
    repo_slug: PropertyRef = PropertyRef(
        "repository",
        description="Slug of the repository containing the dependency.",
    )
    repo_fullname: PropertyRef = PropertyRef(
        "repository_fullname",
        description="Full path of the repository containing the dependency.",
    )


@dataclass(frozen=True)
class SocketDevOrgToDependencyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevOrganization)-[:RESOURCE]->(:SocketDevDependency)
class SocketDevOrgToDependencyRel(CartographyRelSchema):
    """Links a Socket.dev organization to one of its dependencies."""

    target_node_label: str = "SocketDevOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SocketDevOrgToDependencyRelProperties = (
        SocketDevOrgToDependencyRelProperties()
    )


@dataclass(frozen=True)
class SocketDevDependencyToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevDependency)-[:FOUND_IN]->(:SocketDevRepository)
class SocketDevDependencyToRepoRel(CartographyRelSchema):
    """Links a dependency to the Socket.dev repository containing it."""

    target_node_label: str = "SocketDevRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("repository_fullname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SocketDevDependencyToRepoRelProperties = (
        SocketDevDependencyToRepoRelProperties()
    )


@dataclass(frozen=True)
class SocketDevDependencySchema(CartographyNodeSchema):
    """An open source dependency tracked by Socket.dev."""

    label: str = "SocketDevDependency"
    properties: SocketDevDependencyNodeProperties = SocketDevDependencyNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Dependency"])
    sub_resource_relationship: SocketDevOrgToDependencyRel = (
        SocketDevOrgToDependencyRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SocketDevDependencyToRepoRel(),
        ],
    )
