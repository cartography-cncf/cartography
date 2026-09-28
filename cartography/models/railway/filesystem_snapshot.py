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
from cartography.models.ontology.labels import FILESYSTEM_SNAPSHOT


@dataclass(frozen=True)
class RailwayFilesystemSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Cartography ID for this Railway filesystem snapshot."
    )
    deployment_id: PropertyRef = PropertyRef(
        "deployment_id",
        description="ID of the Railway deployment represented by this snapshot.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    kind: PropertyRef = PropertyRef(
        "kind",
        extra_index=True,
        description="Snapshot type. Currently always `source`.",
    )
    source_revision: PropertyRef = PropertyRef(
        "source_revision",
        extra_index=True,
        description="Full source commit SHA represented by this snapshot.",
    )
    source_repo: PropertyRef = PropertyRef(
        "source_repo",
        extra_index=True,
        description="Source repository in owner/name form.",
    )
    root_directory: PropertyRef = PropertyRef(
        "root_directory",
        description="Repository subdirectory represented by this snapshot.",
    )


@dataclass(frozen=True)
class RailwayFilesystemSnapshotToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RailwayFilesystemSnapshotToProjectRel(CartographyRelSchema):
    """Connects a Railway project to a filesystem snapshot that it contains."""

    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayFilesystemSnapshotToProjectRelProperties = (
        RailwayFilesystemSnapshotToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayFilesystemSnapshotToDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RailwayFilesystemSnapshotToDeploymentRel(CartographyRelSchema):
    """Identifies the filesystem snapshot used to assess a Railway deployment."""

    target_node_label: str = "RailwayDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("deployment_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SCANNED_AS"
    properties: RailwayFilesystemSnapshotToDeploymentRelProperties = (
        RailwayFilesystemSnapshotToDeploymentRelProperties()
    )


@dataclass(frozen=True)
class RailwayFilesystemSnapshotToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RailwayFilesystemSnapshotToRepositoryRel(CartographyRelSchema):
    """Identifies the repository revision represented by a source snapshot."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("source_repo")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SNAPSHOT_OF"
    properties: RailwayFilesystemSnapshotToRepositoryRelProperties = (
        RailwayFilesystemSnapshotToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class RailwayFilesystemSnapshotSchema(CartographyNodeSchema):
    """An immutable source filesystem used to assess a Railway deployment."""

    label: str = "RailwayFilesystemSnapshot"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([FILESYSTEM_SNAPSHOT])
    properties: RailwayFilesystemSnapshotNodeProperties = (
        RailwayFilesystemSnapshotNodeProperties()
    )
    sub_resource_relationship: RailwayFilesystemSnapshotToProjectRel = (
        RailwayFilesystemSnapshotToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayFilesystemSnapshotToDeploymentRel(),
            RailwayFilesystemSnapshotToRepositoryRel(),
        ],
    )
