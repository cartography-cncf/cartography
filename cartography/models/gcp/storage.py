import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema, ExtraNodeLabels
from cartography.models.core.relationships import (
    CartographyRelProperties, CartographyRelSchema, LinkDirection,
    make_target_node_matcher, TargetNodeMatcher, OtherRelationships,
)

logger = logging.getLogger(__name__)


# ### Node Properties ###
@dataclass(frozen=True)
class GCPStorageBucketProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    project_number: PropertyRef = PropertyRef("project_number", set_in_kwargs=True)
    kind: PropertyRef = PropertyRef("kind")
    location: PropertyRef = PropertyRef("location")
    location_type: PropertyRef = PropertyRef("location_type")
    meta_generation: PropertyRef = PropertyRef("meta_generation")
    storage_class: PropertyRef = PropertyRef("storage_class")
    time_created: PropertyRef = PropertyRef("time_created")
    updated: PropertyRef = PropertyRef("updated")
    self_link: PropertyRef = PropertyRef("self_link")
    etag: PropertyRef = PropertyRef("etag")
    owner_entity: PropertyRef = PropertyRef("owner_entity")
    owner_entity_id: PropertyRef = PropertyRef("owner_entity_id")
    iam_config_bucket_policy_only: PropertyRef = PropertyRef("iam_config_bucket_policy_only")
    versioning_enabled: PropertyRef = PropertyRef("versioning_enabled")
    retention_period: PropertyRef = PropertyRef("retention_period")
    default_event_based_hold: PropertyRef = PropertyRef("default_event_based_hold")
    log_bucket: PropertyRef = PropertyRef("log_bucket")
    requester_pays: PropertyRef = PropertyRef("requester_pays")
    default_kms_key_name: PropertyRef = PropertyRef("default_kms_key_name")


@dataclass(frozen=True)
class GCPBucketLabelProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key")
    value: PropertyRef = PropertyRef("value")


# ### Relationships ###
@dataclass(frozen=True)
class GCPStorageBucketToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPStorageBucketToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_number", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPStorageBucketToGCPProjectRelProperties = GCPStorageBucketToGCPProjectRelProperties()


@dataclass(frozen=True)
class GCPStorageBucketToGCPBucketLabelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPStorageBucketToGCPBucketLabelRel(CartographyRelSchema):
    target_node_label: str = "GCPBucketLabel"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("label_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LABELED"
    properties: GCPStorageBucketToGCPBucketLabelRelProperties = GCPStorageBucketToGCPBucketLabelRelProperties()


@dataclass(frozen=True)
class GCPBucketLabelToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPBucketLabelToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_number", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPBucketLabelToGCPProjectRelProperties = GCPBucketLabelToGCPProjectRelProperties()


# ### Main Schema ###
@dataclass(frozen=True)
class GCPBucketLabelSchema(CartographyNodeSchema):
    label: str = "GCPBucketLabel"
    properties: GCPBucketLabelProperties = GCPBucketLabelProperties()
    sub_resource_relationship: GCPBucketLabelToGCPProjectRel = GCPBucketLabelToGCPProjectRel()


@dataclass(frozen=True)
class GCPStorageBucketSchema(CartographyNodeSchema):
    label: str = "GCPBucket"
    properties: GCPStorageBucketProperties = GCPStorageBucketProperties()
    sub_resource_relationship: GCPStorageBucketToGCPProjectRel = GCPStorageBucketToGCPProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPStorageBucketToGCPBucketLabelRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["GCPResource"])