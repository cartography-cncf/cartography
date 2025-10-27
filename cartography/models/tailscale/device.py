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
class TailscaleDeviceNodeProperties(CartographyNodeProperties):
    # We use nodeId because the old property `id` is deprecated
    id: PropertyRef = PropertyRef("nodeId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    client_version: PropertyRef = PropertyRef("clientVersion")
    update_available: PropertyRef = PropertyRef("updateAvailable")
    os: PropertyRef = PropertyRef("os")
    created: PropertyRef = PropertyRef("created")
    last_seen: PropertyRef = PropertyRef("lastSeen")
    key_expiry_disabled: PropertyRef = PropertyRef("keyExpiryDisabled")
    expires: PropertyRef = PropertyRef("expires")
    authorized: PropertyRef = PropertyRef("authorized")
    is_external: PropertyRef = PropertyRef("isExternal")
    node_key: PropertyRef = PropertyRef("nodeKey")
    addresses: PropertyRef = PropertyRef("addresses")
    blocks_incoming_connections: PropertyRef = PropertyRef("blocksIncomingConnections")
    client_connectivity_endpoints: PropertyRef = PropertyRef(
        "clientConnectivity.endpoints"
    )
    client_connectivity_mapping_varies_by_dest_ip: PropertyRef = PropertyRef(
        "clientConnectivity.mappingVariesByDestIP"
    )
    tailnet_lock_error: PropertyRef = PropertyRef("tailnetLockError")
    tailnet_lock_key: PropertyRef = PropertyRef("tailnetLockKey")
    posture_identity_serial_numbers: PropertyRef = PropertyRef(
        "postureIdentity.serialNumbers"
    )
    posture_identity_disabled: PropertyRef = PropertyRef("postureIdentity.disabled")


@dataclass(frozen=True)
class TailscaleDeviceToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleDevice)
class TailscaleDeviceToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: TailscaleDeviceToTailnetRelProperties = (
        TailscaleDeviceToTailnetRelProperties()
    )


@dataclass(frozen=True)
class TailscaleDeviceToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:TailscaleUser)-[:OWNS]->(:TailscaleDevice)
class TailscaleDeviceToUserRel(CartographyRelSchema):
    target_node_label: str = "TailscaleUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"login_name": PropertyRef("user")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: TailscaleDeviceToUserRelProperties = (
        TailscaleDeviceToUserRelProperties()
    )


@dataclass(frozen=True)
class TailscaleDeviceSchema(CartographyNodeSchema):
    label: str = "TailscaleDevice"
    properties: TailscaleDeviceNodeProperties = TailscaleDeviceNodeProperties()
    sub_resource_relationship: TailscaleDeviceToTailnetRel = (
        TailscaleDeviceToTailnetRel()
    )
    other_relationships = OtherRelationships(
        [
            TailscaleDeviceToUserRel(),
        ]
    )
