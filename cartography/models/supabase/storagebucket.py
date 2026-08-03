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
from cartography.models.ontology.labels import OBJECT_STORAGE


@dataclass(frozen=True)
class SupabaseStorageBucketNodeProperties(CartographyNodeProperties):
    # Synthesised as "<project ref>/<bucket id>": bucket ids are only unique
    # within a project.
    id: PropertyRef = PropertyRef(
        "id", description="Synthesised as `<project ref>/<bucket id>`"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    bucket_id: PropertyRef = PropertyRef(
        "bucket_id",
        extra_index=True,
        description="The bucket id, unique within the project",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the bucket"
    )
    # True means every object in the bucket is readable without authentication.
    public: PropertyRef = PropertyRef(
        "public",
        description="Whether every object in the bucket is readable without authentication",
    )
    owner: PropertyRef = PropertyRef("owner", description="Owner of the bucket")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the bucket was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the bucket was last changed"
    )


@dataclass(frozen=True)
class SupabaseStorageBucketToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseStorageBucket)
class SupabaseStorageBucketToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseStorageBucketToProjectRelProperties = (
        SupabaseStorageBucketToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseStorageBucketSchema(CartographyNodeSchema):
    """Represents a Supabase Storage bucket."""

    label: str = "SupabaseStorageBucket"
    properties: SupabaseStorageBucketNodeProperties = (
        SupabaseStorageBucketNodeProperties()
    )
    sub_resource_relationship: SupabaseStorageBucketToProjectRel = (
        SupabaseStorageBucketToProjectRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([OBJECT_STORAGE])
