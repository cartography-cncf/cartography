from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SupabaseSigningKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The signing key id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # The JWT signing key used to mint project access tokens. Only the public
    # metadata is stored: algorithm, rotation status and timestamps.
    algorithm: PropertyRef = PropertyRef(
        "algorithm", description="Signing algorithm (`ES256`, `RS256`, `HS256`, ...)"
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Rotation status of the key (`in_use`, `standby`, `revoked`, ...)",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the key was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the key was last changed"
    )


@dataclass(frozen=True)
class SupabaseSigningKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SupabaseProject)-[:RESOURCE]->(:SupabaseSigningKey)
class SupabaseSigningKeyToProjectRel(CartographyRelSchema):
    target_node_label: str = "SupabaseProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_REF", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SupabaseSigningKeyToProjectRelProperties = (
        SupabaseSigningKeyToProjectRelProperties()
    )


@dataclass(frozen=True)
class SupabaseSigningKeySchema(CartographyNodeSchema):
    """Represents a JWT signing key used to mint the project's access tokens. Only public metadata is stored."""

    label: str = "SupabaseSigningKey"
    properties: SupabaseSigningKeyNodeProperties = SupabaseSigningKeyNodeProperties()
    sub_resource_relationship: SupabaseSigningKeyToProjectRel = (
        SupabaseSigningKeyToProjectRel()
    )
