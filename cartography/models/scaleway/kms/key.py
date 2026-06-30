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
class ScalewayKeyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    state: PropertyRef = PropertyRef("state")
    # `usage` is flattened from the SDK's one-of holder; see transform.
    usage_type: PropertyRef = PropertyRef("usage_type")
    usage_algorithm: PropertyRef = PropertyRef("usage_algorithm")
    origin: PropertyRef = PropertyRef("origin")
    region: PropertyRef = PropertyRef("region")
    tags: PropertyRef = PropertyRef("tags")
    rotation_count: PropertyRef = PropertyRef("rotation_count")
    protected: PropertyRef = PropertyRef("protected")
    locked: PropertyRef = PropertyRef("locked")
    rotation_period: PropertyRef = PropertyRef("rotation_period")
    rotation_next_at: PropertyRef = PropertyRef("rotation_next_at")
    rotated_at: PropertyRef = PropertyRef("rotated_at")
    deletion_requested_at: PropertyRef = PropertyRef("deletion_requested_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayKey)
class ScalewayKeyToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayKeyToProjectRelProperties = ScalewayKeyToProjectRelProperties()


@dataclass(frozen=True)
class ScalewayKeySchema(CartographyNodeSchema):
    label: str = "ScalewayKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EncryptionKey"])
    properties: ScalewayKeyProperties = ScalewayKeyProperties()
    sub_resource_relationship: ScalewayKeyToProjectRel = ScalewayKeyToProjectRel()
