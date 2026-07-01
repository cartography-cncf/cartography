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
class DatabricksVolumeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    volume_id: PropertyRef = PropertyRef("volume_id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    full_name: PropertyRef = PropertyRef("full_name", extra_index=True)
    catalog_name: PropertyRef = PropertyRef("catalog_name", extra_index=True)
    schema_name: PropertyRef = PropertyRef("schema_name", extra_index=True)
    metastore_id: PropertyRef = PropertyRef("metastore_id", extra_index=True)
    volume_type: PropertyRef = PropertyRef("volume_type")
    owner: PropertyRef = PropertyRef("owner", extra_index=True)
    comment: PropertyRef = PropertyRef("comment")
    storage_location: PropertyRef = PropertyRef("storage_location")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    created_by: PropertyRef = PropertyRef("created_by")
    updated_by: PropertyRef = PropertyRef("updated_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksVolumeToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksVolume)
class DatabricksVolumeToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksVolumeToWorkspaceRelProperties = (
        DatabricksVolumeToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVolumeToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksSchema)-[:CONTAINS]->(:DatabricksVolume)
class DatabricksVolumeToSchemaRel(CartographyRelSchema):
    target_node_label: str = "DatabricksSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: DatabricksVolumeToSchemaRelProperties = (
        DatabricksVolumeToSchemaRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVolumeToS3RelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksVolume)-[:BACKED_BY]->(:S3Bucket)
class DatabricksVolumeToS3Rel(CartographyRelSchema):
    target_node_label: str = "S3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("s3_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksVolumeToS3RelProperties = DatabricksVolumeToS3RelProperties()


@dataclass(frozen=True)
class DatabricksVolumeToGCSRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksVolume)-[:BACKED_BY]->(:GCPBucket)
class DatabricksVolumeToGCSRel(CartographyRelSchema):
    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("gcs_bucket")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKED_BY"
    properties: DatabricksVolumeToGCSRelProperties = (
        DatabricksVolumeToGCSRelProperties()
    )


@dataclass(frozen=True)
class DatabricksVolumeSchema(CartographyNodeSchema):
    label: str = "DatabricksVolume"
    properties: DatabricksVolumeNodeProperties = DatabricksVolumeNodeProperties()
    # Shared label so UC grants can target any grantable securable by one label.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["DatabricksSecurable"])
    sub_resource_relationship: DatabricksVolumeToWorkspaceRel = (
        DatabricksVolumeToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatabricksVolumeToSchemaRel(),
            DatabricksVolumeToS3Rel(),
            DatabricksVolumeToGCSRel(),
        ],
    )
