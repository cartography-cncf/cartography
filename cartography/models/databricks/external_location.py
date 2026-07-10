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
class DatabricksExternalLocationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    external_location_id: PropertyRef = PropertyRef(
        "external_location_id", extra_index=True
    )
    name: PropertyRef = PropertyRef("name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    url: PropertyRef = PropertyRef("url", extra_index=True)
    credential_id: PropertyRef = PropertyRef("credential_id", extra_index=True)
    credential_name: PropertyRef = PropertyRef("credential_name")
    read_only: PropertyRef = PropertyRef("read_only")
    isolation_mode: PropertyRef = PropertyRef("isolation_mode")
    fallback: PropertyRef = PropertyRef("fallback")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksExternalLocationToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksExternalLocation)
class DatabricksExternalLocationToWorkspaceRel(CartographyRelSchema):
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
# (:DatabricksExternalLocation)-[:BACKED_BY]->(:S3Bucket)
class DatabricksExternalLocationToS3Rel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
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
    label: str = "DatabricksExternalLocation"
    properties: DatabricksExternalLocationNodeProperties = (
        DatabricksExternalLocationNodeProperties()
    )
    # External locations are grantable UC securables.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksSecurable"])
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
