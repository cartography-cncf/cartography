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
class ScalewaySecretProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Secret unique ID."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Secret name."
    )
    status: PropertyRef = PropertyRef(
        "status", description="Secret status (`ready`, `locked`, ...)."
    )
    type: PropertyRef = PropertyRef(
        "type_",
        description="Secret type (`opaque`, `basic_credentials`, `ssh_key`, ...).",
    )
    path: PropertyRef = PropertyRef("path", description="Folder path of the secret.")
    tags: PropertyRef = PropertyRef("tags", description="Secret tags.")
    version_count: PropertyRef = PropertyRef(
        "version_count", description="Number of versions on this secret."
    )
    managed: PropertyRef = PropertyRef(
        "managed",
        description="True if the secret is managed by another Scaleway product.",
    )
    protected: PropertyRef = PropertyRef(
        "protected", description="True if the secret is protected against deletion."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Secret description."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the secret lives in."
    )
    # Optional Key Manager key this secret is encrypted with.
    key_id: PropertyRef = PropertyRef(
        "key_id",
        description="ID of the Key Manager key encrypting this secret (if any).",
    )
    used_by: PropertyRef = PropertyRef(
        "used_by", description="Scaleway products using this secret."
    )
    deletion_requested_at: PropertyRef = PropertyRef(
        "deletion_requested_at", description="Timestamp when deletion was requested."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Secret creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Secret last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewaySecretToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecret)
class ScalewaySecretToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewaySecret` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewaySecretToProjectRelProperties = (
        ScalewaySecretToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySecretToKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewaySecret)-[:ENCRYPTED_BY]->(:ScalewayKey)
class ScalewaySecretToKeyRel(CartographyRelSchema):
    """Connects `ScalewaySecret` to `ScalewayKey` through `ENCRYPTED_BY`."""

    target_node_label: str = "ScalewayKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("key_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: ScalewaySecretToKeyRelProperties = ScalewaySecretToKeyRelProperties()


@dataclass(frozen=True)
class ScalewaySecretSchema(CartographyNodeSchema):
    """Represents a secret managed by Scaleway Secret Manager."""

    label: str = "ScalewaySecret"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Secret"])
    properties: ScalewaySecretProperties = ScalewaySecretProperties()
    sub_resource_relationship: ScalewaySecretToProjectRel = ScalewaySecretToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewaySecretToKeyRel(),
        ]
    )


@dataclass(frozen=True)
class ScalewaySecretVersionProperties(CartographyNodeProperties):
    # Versions don't have a provider-side ID either; compose
    # "<secret_id>/<revision>" so we don't collide across secrets.
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="`{secret_id}/{revision}`."
    )
    revision: PropertyRef = PropertyRef(
        "revision", description="Monotonic revision number."
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Version status (`enabled`, `disabled`, `destroyed`, ...).",
    )
    latest: PropertyRef = PropertyRef(
        "latest", description="True if this version is the latest for its secret."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Version description."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the version lives in."
    )
    deletion_requested_at: PropertyRef = PropertyRef(
        "deletion_requested_at", description="Timestamp when deletion was requested."
    )
    deleted_at: PropertyRef = PropertyRef(
        "deleted_at", description="Deletion date (when the version is destroyed)."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Version creation date."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Version last update date."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewaySecretVersionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecretVersion)
class ScalewaySecretVersionToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewaySecretVersion` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewaySecretVersionToProjectRelProperties = (
        ScalewaySecretVersionToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySecretVersionToSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewaySecret)-[:HAS]->(:ScalewaySecretVersion)
class ScalewaySecretVersionToSecretRel(CartographyRelSchema):
    """Connects `ScalewaySecret` to `ScalewaySecretVersion` through `HAS`."""

    target_node_label: str = "ScalewaySecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secret_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewaySecretVersionToSecretRelProperties = (
        ScalewaySecretVersionToSecretRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySecretVersionSchema(CartographyNodeSchema):
    """Represents a version of a `ScalewaySecret`. The version's ID is composed as
    `{secret_id}/{revision}` since Scaleway does not expose a provider-side version ID.
    """

    label: str = "ScalewaySecretVersion"
    properties: ScalewaySecretVersionProperties = ScalewaySecretVersionProperties()
    sub_resource_relationship: ScalewaySecretVersionToProjectRel = (
        ScalewaySecretVersionToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewaySecretVersionToSecretRel(),
        ]
    )
