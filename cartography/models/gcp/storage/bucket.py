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
class GCPBucketNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description='The ID of the storage bucket, e.g. "bucket-12345".',
    )
    # Preserve legacy field for compatibility with existing queries
    bucket_id: PropertyRef = PropertyRef(
        "bucket_id",
        description="Cloud Storage bucket name.",
    )
    project_number: PropertyRef = PropertyRef(
        "project_number",
        description="Numeric identifier of the owning Google Cloud project.",
    )
    self_link: PropertyRef = PropertyRef(
        "self_link", description="The URI of the storage bucket."
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description="The kind of item this is. For storage buckets, this is always storage#bucket.",
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="The location of the bucket. Object data for objects in the bucket resides in physical storage within this region. Defaults to US. See [Cloud Storage bucket locations](https://cloud.google.com/storage/docs/locations) for the authoritative list.",
    )
    location_type: PropertyRef = PropertyRef(
        "location_type",
        description="The type of location that the bucket resides in, as determined by the `location` property.",
    )
    meta_generation: PropertyRef = PropertyRef(
        "meta_generation", description="The metadata generation of this bucket."
    )
    storage_class: PropertyRef = PropertyRef(
        "storage_class",
        description="The bucket's default storage class, used whenever no `storageClass` is specified for a newly-created object. For more information, see [storage classes](https://cloud.google.com/storage/docs/storage-classes).",
    )
    time_created: PropertyRef = PropertyRef(
        "time_created",
        description="The creation time of the bucket in RFC 3339 format.",
    )
    retention_period: PropertyRef = PropertyRef(
        "retention_period",
        description="The period of time, in seconds, that objects in the bucket must be retained and cannot be deleted, overwritten, or archived.",
    )
    iam_config_bucket_policy_only: PropertyRef = PropertyRef(
        "iam_config_bucket_policy_only",
        description="The bucket's [Bucket Policy Only](https://cloud.google.com/storage/docs/bucket-policy-only) configuration.",
    )
    iam_config_public_access_prevention: PropertyRef = PropertyRef(
        "iam_config_public_access_prevention",
        description="The bucket's [Public Access Prevention](https://cloud.google.com/storage/docs/public-access-prevention) setting (`enforced` blocks all public access regardless of bindings; `inherited` defers to the project / org default).",
    )
    owner_entity: PropertyRef = PropertyRef(
        "owner_entity", description="The entity, in the form `project-owner-projectId`."
    )
    owner_entity_id: PropertyRef = PropertyRef(
        "owner_entity_id", description="The ID for the entity."
    )
    versioning_enabled: PropertyRef = PropertyRef(
        "versioning_enabled",
        description="The bucket's versioning configuration (if set to `True`, versioning is fully enabled for this bucket).",
    )
    log_bucket: PropertyRef = PropertyRef(
        "log_bucket",
        description="The destination bucket where the current bucket's logs should be placed.",
    )
    requester_pays: PropertyRef = PropertyRef(
        "requester_pays",
        description="The bucket's billing configuration (if set to true, Requester Pays is enabled for this bucket).",
    )
    default_kms_key_name: PropertyRef = PropertyRef(
        "default_kms_key_name",
        description="A Cloud KMS key that will be used to encrypt objects inserted into this bucket, if no encryption method is specified.",
    )
    # True when the legacy ACL or default object ACL grants access to `allUsers`
    # or `allAuthenticatedUsers`. Consumed by the bucket `_ont_public` analysis job.
    acl_public: PropertyRef = PropertyRef(
        "acl_public",
        description="`true` if the bucket's legacy ACL or default object ACL grants access to `allUsers` or `allAuthenticatedUsers`. Consumed by the `_ont_public` projection job.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GCPBucketToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPBucket)
class GCPBucketToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPBucketToProjectRelProperties = GCPBucketToProjectRelProperties()


@dataclass(frozen=True)
class GCPBucketSchema(CartographyNodeSchema):
    """Representation of a GCP [Storage Bucket](https://cloud.google.com/storage/docs/json_api/v1/buckets)."""

    label: str = "GCPBucket"
    properties: GCPBucketNodeProperties = GCPBucketNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ObjectStorage"])
    sub_resource_relationship: GCPBucketToProjectRel = GCPBucketToProjectRel()


@dataclass(frozen=True)
class GCPBucketLabelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    key: PropertyRef = PropertyRef("key", extra_index=True, description="Label key.")
    value: PropertyRef = PropertyRef("value", description="Label value.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPBucketLabelToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPBucketLabel)
class GCPBucketLabelToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPBucketLabelToProjectRelProperties = (
        GCPBucketLabelToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPBucketLabelToBucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPBucket)-[:LABELED]->(:GCPBucketLabel)
class GCPBucketLabelToBucketRel(CartographyRelSchema):
    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("bucket_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPBucketLabelToBucketRelProperties = (
        GCPBucketLabelToBucketRelProperties()
    )


@dataclass(frozen=True)
class GCPBucketLabelSchema(CartographyNodeSchema):
    """Representation of a GCP [Storage Bucket Label](https://cloud.google.com/storage/docs/key-terms#bucket-labels).  This node contains a key-value pair."""

    label: str = "GCPBucketLabel"
    properties: GCPBucketLabelNodeProperties = GCPBucketLabelNodeProperties()
    sub_resource_relationship: GCPBucketLabelToProjectRel = GCPBucketLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPBucketLabelToBucketRel(),
        ]
    )
