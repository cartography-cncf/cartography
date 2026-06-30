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
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    type: PropertyRef = PropertyRef("type_")
    path: PropertyRef = PropertyRef("path")
    tags: PropertyRef = PropertyRef("tags")
    version_count: PropertyRef = PropertyRef("version_count")
    managed: PropertyRef = PropertyRef("managed")
    protected: PropertyRef = PropertyRef("protected")
    description: PropertyRef = PropertyRef("description")
    region: PropertyRef = PropertyRef("region")
    # Optional Key Manager key this secret is encrypted with.
    key_id: PropertyRef = PropertyRef("key_id")
    used_by: PropertyRef = PropertyRef("used_by")
    deletion_requested_at: PropertyRef = PropertyRef("deletion_requested_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewaySecretToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecret)
class ScalewaySecretToProjectRel(CartographyRelSchema):
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
    target_node_label: str = "ScalewayKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("key_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: ScalewaySecretToKeyRelProperties = ScalewaySecretToKeyRelProperties()


@dataclass(frozen=True)
class ScalewaySecretSchema(CartographyNodeSchema):
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
    id: PropertyRef = PropertyRef("id", extra_index=True)
    revision: PropertyRef = PropertyRef("revision")
    status: PropertyRef = PropertyRef("status")
    latest: PropertyRef = PropertyRef("latest")
    description: PropertyRef = PropertyRef("description")
    region: PropertyRef = PropertyRef("region")
    deletion_requested_at: PropertyRef = PropertyRef("deletion_requested_at")
    deleted_at: PropertyRef = PropertyRef("deleted_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewaySecretVersionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySecretVersion)
class ScalewaySecretVersionToProjectRel(CartographyRelSchema):
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
