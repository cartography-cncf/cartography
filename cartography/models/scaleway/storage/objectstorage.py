from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayObjectStorageBucketNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    region: PropertyRef = PropertyRef("region")
    endpoint: PropertyRef = PropertyRef("endpoint")
    creation_date: PropertyRef = PropertyRef("creation_date")
    tags: PropertyRef = PropertyRef("tags")
    versioning_status: PropertyRef = PropertyRef("versioning_status")
    # Public-exposure signals (mirrors AWS S3 anonymous_access / GCP acl_public).
    # `public` is the combined tri-state (null = unknown, both sources unreadable).
    acl_public: PropertyRef = PropertyRef("acl_public")
    anonymous_access: PropertyRef = PropertyRef("anonymous_access", extra_index=True)
    anonymous_actions: PropertyRef = PropertyRef("anonymous_actions")
    public: PropertyRef = PropertyRef("public", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayObjectStorageBucketToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayObjectStorageBucket)
class ScalewayObjectStorageBucketToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayObjectStorageBucketToProjectRelProperties = (
        ScalewayObjectStorageBucketToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayObjectStorageBucketSchema(CartographyNodeSchema):
    label: str = "ScalewayObjectStorageBucket"
    properties: ScalewayObjectStorageBucketNodeProperties = (
        ScalewayObjectStorageBucketNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ObjectStorage"])
    sub_resource_relationship: ScalewayObjectStorageBucketToProjectRel = (
        ScalewayObjectStorageBucketToProjectRel()
    )
