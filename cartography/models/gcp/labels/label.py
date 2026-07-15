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

# --- Shared properties ---


@dataclass(frozen=True)
class GCPLabelNodeProperties(CartographyNodeProperties):
    """
    Properties for GCPLabel nodes.

    The id is computed as "{resource_id}:{key}:{value}" during ingestion.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="The ID of the label. Takes the form `{resource_id}:{key}:{value}`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    key: PropertyRef = PropertyRef(
        "key", extra_index=True, description="The key of the label."
    )
    value: PropertyRef = PropertyRef("value", description="The value of the label.")
    resource_type: PropertyRef = PropertyRef(
        "resource_type",
        description="The Cartography node label of the resource this label is attached to (e.g. `GCPBucket`, `GCPInstance`).",
    )


@dataclass(frozen=True)
class GCPLabelToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToProjectRel(CartographyRelSchema):
    """Indicates that a GCP project contains this label as a resource."""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPLabelToProjectRelProperties = GCPLabelToProjectRelProperties()


@dataclass(frozen=True)
class GCPLabelToBucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToBucketRel(CartographyRelSchema):
    """Indicates that a GCP bucket has this legacy label."""

    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToBucketRelProperties = GCPLabelToBucketRelProperties()


@dataclass(frozen=True)
class GCPLabelToBucketTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToBucketTaggedRel(CartographyRelSchema):
    """Indicates that a GCP bucket is tagged with this label."""

    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToBucketTaggedRelProperties = (
        GCPLabelToBucketTaggedRelProperties()
    )


# --- GCPBucket label schema ---


@dataclass(frozen=True)
class GCPBucketGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Label", "GCPBucketLabel", "Tag"]
    )
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToBucketRel(), GCPLabelToBucketTaggedRel()],
    )


# --- GCPInstance label schema ---


@dataclass(frozen=True)
class GCPLabelToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToInstanceRel(CartographyRelSchema):
    """Indicates that a GCP instance has this legacy label."""

    target_node_label: str = "GCPInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToInstanceRelProperties = GCPLabelToInstanceRelProperties()


@dataclass(frozen=True)
class GCPLabelToInstanceTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToInstanceTaggedRel(CartographyRelSchema):
    """Indicates that a GCP instance is tagged with this label."""

    target_node_label: str = "GCPInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToInstanceTaggedRelProperties = (
        GCPLabelToInstanceTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPInstanceGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToInstanceRel(), GCPLabelToInstanceTaggedRel()],
    )


# --- GKECluster label schema ---


@dataclass(frozen=True)
class GCPLabelToGKEClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToGKEClusterRel(CartographyRelSchema):
    """Indicates that a GKE cluster has this legacy label."""

    target_node_label: str = "GKECluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToGKEClusterRelProperties = GCPLabelToGKEClusterRelProperties()


@dataclass(frozen=True)
class GCPLabelToGKEClusterTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToGKEClusterTaggedRel(CartographyRelSchema):
    """Indicates that a GKE cluster is tagged with this label."""

    target_node_label: str = "GKECluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToGKEClusterTaggedRelProperties = (
        GCPLabelToGKEClusterTaggedRelProperties()
    )


@dataclass(frozen=True)
class GKEClusterGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToGKEClusterRel(), GCPLabelToGKEClusterTaggedRel()],
    )


# --- GCPCloudSQLInstance label schema ---


@dataclass(frozen=True)
class GCPLabelToCloudSQLInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToCloudSQLInstanceRel(CartographyRelSchema):
    """Indicates that a GCP Cloud SQL instance has this legacy label."""

    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToCloudSQLInstanceRelProperties = (
        GCPLabelToCloudSQLInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToCloudSQLInstanceTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToCloudSQLInstanceTaggedRel(CartographyRelSchema):
    """Indicates that a GCP Cloud SQL instance is tagged with this label."""

    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToCloudSQLInstanceTaggedRelProperties = (
        GCPLabelToCloudSQLInstanceTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudSQLInstanceGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToCloudSQLInstanceRel(), GCPLabelToCloudSQLInstanceTaggedRel()],
    )


# --- GCPBigtableInstance label schema ---


@dataclass(frozen=True)
class GCPLabelToBigtableInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToBigtableInstanceRel(CartographyRelSchema):
    """Indicates that a GCP Bigtable instance has this legacy label."""

    target_node_label: str = "GCPBigtableInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToBigtableInstanceRelProperties = (
        GCPLabelToBigtableInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToBigtableInstanceTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToBigtableInstanceTaggedRel(CartographyRelSchema):
    """Indicates that a GCP Bigtable instance is tagged with this label."""

    target_node_label: str = "GCPBigtableInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToBigtableInstanceTaggedRelProperties = (
        GCPLabelToBigtableInstanceTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPBigtableInstanceGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToBigtableInstanceRel(), GCPLabelToBigtableInstanceTaggedRel()],
    )


# --- GCPDNSZone label schema ---


@dataclass(frozen=True)
class GCPLabelToDNSZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToDNSZoneRel(CartographyRelSchema):
    """Indicates that a GCP DNS zone has this legacy label."""

    target_node_label: str = "GCPDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToDNSZoneRelProperties = GCPLabelToDNSZoneRelProperties()


@dataclass(frozen=True)
class GCPLabelToDNSZoneTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToDNSZoneTaggedRel(CartographyRelSchema):
    """Indicates that a GCP DNS zone is tagged with this label."""

    target_node_label: str = "GCPDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToDNSZoneTaggedRelProperties = (
        GCPLabelToDNSZoneTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPDNSZoneGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToDNSZoneRel(), GCPLabelToDNSZoneTaggedRel()],
    )


# --- GCPSecretManagerSecret label schema ---


@dataclass(frozen=True)
class GCPLabelToSecretManagerSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToSecretManagerSecretRel(CartographyRelSchema):
    """Indicates that a GCP Secret Manager secret has this legacy label."""

    target_node_label: str = "GCPSecretManagerSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToSecretManagerSecretRelProperties = (
        GCPLabelToSecretManagerSecretRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToSecretManagerSecretTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToSecretManagerSecretTaggedRel(CartographyRelSchema):
    """Indicates that a GCP Secret Manager secret is tagged with this label."""

    target_node_label: str = "GCPSecretManagerSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToSecretManagerSecretTaggedRelProperties = (
        GCPLabelToSecretManagerSecretTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToSecretManagerSecretRel(), GCPLabelToSecretManagerSecretTaggedRel()],
    )


# --- GCPCloudRunService label schema ---


@dataclass(frozen=True)
class GCPLabelToCloudRunServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToCloudRunServiceRel(CartographyRelSchema):
    """Indicates that a GCP Cloud Run service has this legacy label."""

    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToCloudRunServiceRelProperties = (
        GCPLabelToCloudRunServiceRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToCloudRunServiceTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToCloudRunServiceTaggedRel(CartographyRelSchema):
    """Indicates that a GCP Cloud Run service is tagged with this label."""

    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToCloudRunServiceTaggedRelProperties = (
        GCPLabelToCloudRunServiceTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunServiceGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToCloudRunServiceRel(), GCPLabelToCloudRunServiceTaggedRel()],
    )


# --- GCPCloudRunJob label schema ---


@dataclass(frozen=True)
class GCPLabelToCloudRunJobRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToCloudRunJobRel(CartographyRelSchema):
    """Indicates that a GCP Cloud Run job has this legacy label."""

    target_node_label: str = "GCPCloudRunJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToCloudRunJobRelProperties = (
        GCPLabelToCloudRunJobRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToCloudRunJobTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToCloudRunJobTaggedRel(CartographyRelSchema):
    """Indicates that a GCP Cloud Run job is tagged with this label."""

    target_node_label: str = "GCPCloudRunJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToCloudRunJobTaggedRelProperties = (
        GCPLabelToCloudRunJobTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunJobGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToCloudRunJobRel(), GCPLabelToCloudRunJobTaggedRel()],
    )


# --- GCPCloudFunction label schema ---


@dataclass(frozen=True)
class GCPLabelToCloudFunctionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPLabelToCloudFunctionRel(CartographyRelSchema):
    """Indicates that a GCP Cloud Function has this legacy label."""

    target_node_label: str = "GCPCloudFunction"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToCloudFunctionRelProperties = (
        GCPLabelToCloudFunctionRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudFunctionGCPLabelSchema(CartographyNodeSchema):
    """A key-value label attached to a supported Google Cloud resource."""

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToCloudFunctionRel()],
    )
