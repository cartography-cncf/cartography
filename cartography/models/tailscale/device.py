from dataclasses import dataclass
from datetime import datetime

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
    name: PropertyRef = PropertyRef("name", auto_format=str)
    hostname: PropertyRef = PropertyRef("hostname", auto_format=str)
    client_version: PropertyRef = PropertyRef("clientVersion", auto_format=str)
    update_available: PropertyRef = PropertyRef("updateAvailable", auto_format=bool)
    os: PropertyRef = PropertyRef("os", auto_format=str)
    created: PropertyRef = PropertyRef("created", auto_format=datetime)
    last_seen: PropertyRef = PropertyRef("lastSeen", auto_format=datetime)
    key_expiry_disabled: PropertyRef = PropertyRef("keyExpiryDisabled")
    expires: PropertyRef = PropertyRef("expires", auto_format=datetime)
    authorized: PropertyRef = PropertyRef("authorized", auto_format=bool)
    is_external: PropertyRef = PropertyRef("isExternal", auto_format=bool)
    node_key: PropertyRef = PropertyRef("nodeKey", auto_format=str)
    blocks_incoming_connections: PropertyRef = PropertyRef("blocksIncomingConnections", auto_format=bool)
    client_connectivity_endpoints: PropertyRef = PropertyRef(
        "clientConnectivity.endpoints"
    )
    client_connectivity_mapping_varies_by_dest_ip: PropertyRef = PropertyRef(
        "clientConnectivity.mappingVariesByDestIP"
    )
    tailnet_lock_error: PropertyRef = PropertyRef("tailnetLockError", auto_format=str)
    tailnet_lock_key: PropertyRef = PropertyRef("tailnetLockKey", auto_format=str)
    posture_identity_serial_numbers: PropertyRef = PropertyRef(
        "postureIdentity.serialNumbers",
        auto_format=str
    )
    posture_identity_disabled: PropertyRef = PropertyRef("postureIdentity.disabled", auto_format=bool)


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
