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
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Key unique ID.")
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Key name.")
    description: PropertyRef = PropertyRef(
        "description", description="Key description."
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Key state (`enabled`, `disabled`, `pending_deletion`, ...).",
    )
    # `usage` is flattened from the SDK's one-of holder; see transform.
    usage_type: PropertyRef = PropertyRef(
        "usage_type",
        description="Active key usage category (`symmetric_encryption`, `asymmetric_encryption`, `asymmetric_signing`).",
    )
    usage_algorithm: PropertyRef = PropertyRef(
        "usage_algorithm",
        description="Algorithm corresponding to `usage_type` (e.g. `aes_256_gcm`).",
    )
    origin: PropertyRef = PropertyRef(
        "origin", description="Key material origin (`scaleway_kms`, `external`)."
    )
    region: PropertyRef = PropertyRef("region", description="Region the key lives in.")
    tags: PropertyRef = PropertyRef("tags", description="Key tags.")
    rotation_count: PropertyRef = PropertyRef(
        "rotation_count", description="Number of times the key has been rotated."
    )
    protected: PropertyRef = PropertyRef(
        "protected", description="True if the key is protected against deletion."
    )
    locked: PropertyRef = PropertyRef(
        "locked", description="True if the key is locked."
    )
    rotation_period: PropertyRef = PropertyRef(
        "rotation_period", description="Automatic rotation period (ISO 8601 duration)."
    )
    rotation_next_at: PropertyRef = PropertyRef(
        "rotation_next_at", description="Next scheduled rotation timestamp."
    )
    rotated_at: PropertyRef = PropertyRef(
        "rotated_at", description="Last rotation date."
    )
    deletion_requested_at: PropertyRef = PropertyRef(
        "deletion_requested_at", description="Timestamp when deletion was requested."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Key creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Key last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayKeyToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayKey)
class ScalewayKeyToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayKey` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayKeyToProjectRelProperties = ScalewayKeyToProjectRelProperties()


@dataclass(frozen=True)
class ScalewayKeySchema(CartographyNodeSchema):
    """Represents a Scaleway Key Manager key."""

    label: str = "ScalewayKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EncryptionKey"])
    properties: ScalewayKeyProperties = ScalewayKeyProperties()
    sub_resource_relationship: ScalewayKeyToProjectRel = ScalewayKeyToProjectRel()
