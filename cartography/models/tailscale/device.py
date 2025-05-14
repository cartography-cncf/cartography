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
class TailscaleDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    node_id: PropertyRef = PropertyRef("nodeId")
    user: PropertyRef = PropertyRef("user")
    name: PropertyRef = PropertyRef("name")
    hostname: PropertyRef = PropertyRef("hostname")
    client_version: PropertyRef = PropertyRef("clientVersion")
    update_available: PropertyRef = PropertyRef("updateAvailable")
    os: PropertyRef = PropertyRef("os")
    created: PropertyRef = PropertyRef("created")
    last_seen: PropertyRef = PropertyRef("lastSeen")
    key_expiry_disabled: PropertyRef = PropertyRef("keyExpiryDisabled")
    expires: PropertyRef = PropertyRef("expires")
    authorized: PropertyRef = PropertyRef("authorized")
    is_external: PropertyRef = PropertyRef("isExternal")
    machine_key: PropertyRef = PropertyRef("machineKey")
    node_key: PropertyRef = PropertyRef("nodeKey")
    blocks_incoming_connections: PropertyRef = PropertyRef("blocksIncomingConnections")
    clientConnectivity_endpoints: PropertyRef = PropertyRef(
        "clientConnectivity.endpoints"
    )
    clientConnectivity_mapping_varies_by_dest_ip: PropertyRef = PropertyRef(
        "clientConnectivity.mappingVariesByDestIP"
    )
    tailnet_lock_error: PropertyRef = PropertyRef("tailnetLockError")
    tailnet_lock_key: PropertyRef = PropertyRef("tailnetLockKey")
    postureIdentity_serial_numbers: PropertyRef = PropertyRef(
        "postureIdentity.serialNumbers"
    )
    postureIdentity_disabled: PropertyRef = PropertyRef("postureIdentity.disabled")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TailscaleDeviceSchema(CartographyNodeSchema):
    label: str = "TailscaleDevice"
    properties: TailscaleDeviceNodeProperties = TailscaleDeviceNodeProperties()
