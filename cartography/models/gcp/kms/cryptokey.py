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
class GCPCryptoKeyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The full resource name of the Crypto Key."
    )
    name: PropertyRef = PropertyRef(
        "name", description="The short name of the Crypto Key."
    )
    rotation_period: PropertyRef = PropertyRef(
        "rotation_period",
        description="Configured automatic Cloud KMS key rotation interval.",
    )
    purpose: PropertyRef = PropertyRef(
        "purpose", description="The key purpose (e.g., `ENCRYPT_DECRYPT`)."
    )
    state: PropertyRef = PropertyRef(
        "state", description="The state of the primary key version (e.g., `ENABLED`)."
    )
    key_ring_id: PropertyRef = PropertyRef(
        "key_ring_id",
        description="Full resource name of the containing Cloud KMS key ring.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="The timestamp of the last update.",
    )


@dataclass(frozen=True)
class GCPCryptoKeyToGCPKeyRingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPCryptoKeyToGCPKeyRingRel(CartographyRelSchema):
    target_node_label: str = "GCPKeyRing"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("key_ring_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPCryptoKeyToGCPKeyRingRelProperties = (
        GCPCryptoKeyToGCPKeyRingRelProperties()
    )


@dataclass(frozen=True)
class GCPCryptoKeyToGCPProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPCryptoKeyToGCPProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPCryptoKeyToGCPProjectRelProperties = (
        GCPCryptoKeyToGCPProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPCryptoKeySchema(CartographyNodeSchema):
    """Representation of a GCP [Crypto Key](https://cloud.google.com/kms/docs/reference/rest/v1/projects.locations.keyRings.cryptoKeys)."""

    label: str = "GCPCryptoKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EncryptionKey"])
    properties: GCPCryptoKeyProperties = GCPCryptoKeyProperties()
    sub_resource_relationship: GCPCryptoKeyToGCPProjectRel = (
        GCPCryptoKeyToGCPProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPCryptoKeyToGCPKeyRingRel(),
        ],
    )
