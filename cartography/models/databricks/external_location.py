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
from cartography.models.databricks.extra_labels import DATABRICKS_SECURABLE
from cartography.models.ontology.labels import OBJECT_STORAGE


@dataclass(frozen=True)
class DatabricksExternalLocationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Identifier for the external location."
    )
    external_location_id: PropertyRef = PropertyRef(
        "external_location_id",
        extra_index=True,
        description="Databricks identifier for the external location.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the external location."
    )
    metastore_id: PropertyRef = PropertyRef(
        "metastore_id",
        extra_index=True,
        description="Identifier of the metastore that contains the external location.",
    )
    url: PropertyRef = PropertyRef(
        "url",
        extra_index=True,
        description="Cloud storage URL of the external location.",
    )
    credential_id: PropertyRef = PropertyRef(
        "credential_id",
        extra_index=True,
        description="Identifier of the storage credential used by the location.",
    )
    credential_name: PropertyRef = PropertyRef(
        "credential_name",
        description="Name of the storage credential used by the location.",
    )
    read_only: PropertyRef = PropertyRef(
        "read_only", description="Whether the external location is read-only."
    )
    isolation_mode: PropertyRef = PropertyRef(
        "isolation_mode",
        description="Workspace isolation mode of the external location.",
    )
    fallback: PropertyRef = PropertyRef(
        "fallback",
        description="Whether fallback mode is enabled for the external location.",
    )
    owner: PropertyRef = PropertyRef(
        "owner",
        extra_index=True,
        description="Principal that owns the external location.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="User-provided description of the external location."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the external location was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the external location was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksExternalLocationToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksExternalLocation)
class DatabricksExternalLocationToWorkspaceRel(CartographyRelSchema):
    """A Databricks external location is a resource within a workspace."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksExternalLocationToWorkspaceRelProperties = (
        DatabricksExternalLocationToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksExternalLocationToMetastoreRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksMetastore)-[:CONTAINS]->(:DatabricksExternalLocation)
class DatabricksExternalLocationToMetastoreRel(CartographyRelSchema):
    """A Databricks metastore contains an external location."""

    target_node_label: str = "DatabricksMetastore"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("metastore_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksExternalLocationToMetastoreRelProperties = (
        DatabricksExternalLocationToMetastoreRelProperties()
    )


@dataclass(frozen=True)
class DatabricksExternalLocationToCredentialRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksExternalLocation)-[:USES_CREDENTIAL]->(:DatabricksStorageCredential)
class DatabricksExternalLocationToCredentialRel(CartographyRelSchema):
    """A Databricks external location uses a storage credential."""

    target_node_label: str = "DatabricksStorageCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"credential_id": PropertyRef("credential_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CREDENTIAL"
    properties: DatabricksExternalLocationToCredentialRelProperties = (
        DatabricksExternalLocationToCredentialRelProperties()
    )


@dataclass(frozen=True)
class DatabricksExternalLocationToS3RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksExternalLocation)-[:BACKED_BY]->(:AWSS3Bucket)
class DatabricksExternalLocationToS3Rel(CartographyRelSchema):
    """A Databricks external location is backed by an Amazon S3 bucket."""

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("s3_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksExternalLocationToS3RelProperties = (
        DatabricksExternalLocationToS3RelProperties()
    )


@dataclass(frozen=True)
class DatabricksExternalLocationToGCSRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksExternalLocation)-[:BACKED_BY]->(:GCPBucket)
class DatabricksExternalLocationToGCSRel(CartographyRelSchema):
    """A Databricks external location is backed by a Google Cloud Storage bucket."""

    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcs_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksExternalLocationToGCSRelProperties = (
        DatabricksExternalLocationToGCSRelProperties()
    )


@dataclass(frozen=True)
class DatabricksExternalLocationSchema(CartographyNodeSchema):
    """A Unity Catalog external location that governs a cloud storage path."""

    label: str = "DatabricksExternalLocation"
    properties: DatabricksExternalLocationNodeProperties = (
        DatabricksExternalLocationNodeProperties()
    )
    # DatabricksSecurable: grantable UC securable. ObjectStorage: ontology label;
    # an external location points at a cloud storage path.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [DATABRICKS_SECURABLE, OBJECT_STORAGE]
    )
    sub_resource_relationship: DatabricksExternalLocationToWorkspaceRel = (
        DatabricksExternalLocationToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksExternalLocationToMetastoreRel(),
            DatabricksExternalLocationToCredentialRel(),
            DatabricksExternalLocationToS3Rel(),
            DatabricksExternalLocationToGCSRel(),
        ],
    )
