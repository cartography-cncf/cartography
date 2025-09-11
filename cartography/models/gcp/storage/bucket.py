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
class GCPBucketNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    # Preserve legacy field for compatibility with existing queries
    bucket_id: PropertyRef = PropertyRef("bucket_id")
    project_number: PropertyRef = PropertyRef("project_number")
    self_link: PropertyRef = PropertyRef("self_link")
    kind: PropertyRef = PropertyRef("kind")
    location: PropertyRef = PropertyRef("location")
    location_type: PropertyRef = PropertyRef("location_type")
    meta_generation: PropertyRef = PropertyRef("meta_generation")
    storage_class: PropertyRef = PropertyRef("storage_class")
    time_created: PropertyRef = PropertyRef("time_created")
    retention_period: PropertyRef = PropertyRef("retention_period")
    iam_config_bucket_policy_only: PropertyRef = PropertyRef(
        "iam_config_bucket_policy_only"
    )
    owner_entity: PropertyRef = PropertyRef("owner_entity")
    owner_entity_id: PropertyRef = PropertyRef("owner_entity_id")
    versioning_enabled: PropertyRef = PropertyRef("versioning_enabled")
    log_bucket: PropertyRef = PropertyRef("log_bucket")
    requester_pays: PropertyRef = PropertyRef("requester_pays")
    default_kms_key_name: PropertyRef = PropertyRef("default_kms_key_name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPBucketToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    label: str = "GCPBucket"
    properties: GCPBucketNodeProperties = GCPBucketNodeProperties()
    sub_resource_relationship: GCPBucketToProjectRel = GCPBucketToProjectRel()


@dataclass(frozen=True)
class GCPBucketLabelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    key: PropertyRef = PropertyRef("key", extra_index=True)
    value: PropertyRef = PropertyRef("value")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPBucketLabelToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    label: str = "GCPBucketLabel"
    properties: GCPBucketLabelNodeProperties = GCPBucketLabelNodeProperties()
    sub_resource_relationship: GCPBucketLabelToProjectRel = GCPBucketLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPBucketLabelToBucketRel(),
        ]
    )
