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
class DatabricksArtifactAllowlistNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Identifier for the artifact allowlist."
    )
    artifact_type: PropertyRef = PropertyRef(
        "artifact_type",
        extra_index=True,
        description="Type of artifact governed by the allowlist.",
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore governed by the allowlist.",
    )
    artifacts: PropertyRef = PropertyRef(
        "artifacts",
        description="Allowed artifact patterns prefixed by their match types.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the allowlist was created."
    )
    created_by: PropertyRef = PropertyRef(
        "created_by",
        extra_index=True,
        description="Principal that created the allowlist.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksArtifactAllowlistToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksArtifactAllowlist)
class DatabricksArtifactAllowlistToWorkspaceRel(CartographyRelSchema):
    """A Databricks artifact allowlist is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksArtifactAllowlistToWorkspaceRelProperties = (
        DatabricksArtifactAllowlistToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksArtifactAllowlistToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksArtifactAllowlist)
class DatabricksArtifactAllowlistToMetastoreRel(CartographyRelSchema):
    """A Databricks metastore contains an artifact allowlist."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksArtifactAllowlistToMetastoreRelProperties = (
        DatabricksArtifactAllowlistToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksArtifactAllowlistSchema(CartographyNodeSchema):
    """A Unity Catalog allowlist for libraries and initialization scripts."""

    label: str = "DatabricksArtifactAllowlist"
    properties: DatabricksArtifactAllowlistNodeProperties = (
        DatabricksArtifactAllowlistNodeProperties()
    )
    sub_resource_relationship: DatabricksArtifactAllowlistToWorkspaceRel = (
        DatabricksArtifactAllowlistToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DatabricksArtifactAllowlistToMetastoreRel()],
    )
