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
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)
    posture_identity_serial_numbers: PropertyRef = PropertyRef(
        "postureIdentity.serialNumbers"
    )
    posture_identity_disabled: PropertyRef = PropertyRef("postureIdentity.disabled")
    # Device posture attributes projected from /device/{deviceId}/attributes.
    # Sources:
    # - https://tailscale.com/docs/integrations/crowdstrike-zta
    # - https://tailscale.com/docs/integrations/sentinelone
    # - https://tailscale.com/docs/integrations/kolide
    # - https://tailscale.com/docs/integrations/fleet
    # - https://tailscale.com/docs/integrations/huntress
    # - https://tailscale.com/docs/integrations/iru
    # - https://tailscale.com/docs/integrations/jamf-pro
    # - https://tailscale.com/docs/integrations/mdm/intune
    posture_node_os: PropertyRef = PropertyRef("posture_node_os")
    posture_node_os_version: PropertyRef = PropertyRef("posture_node_os_version")
    posture_node_ts_auto_update: PropertyRef = PropertyRef(
        "posture_node_ts_auto_update"
    )
    posture_node_ts_release_track: PropertyRef = PropertyRef(
        "posture_node_ts_release_track"
    )
    posture_node_ts_state_encrypted: PropertyRef = PropertyRef(
        "posture_node_ts_state_encrypted"
    )
    posture_node_ts_version: PropertyRef = PropertyRef("posture_node_ts_version")
    posture_ip_country: PropertyRef = PropertyRef("posture_ip_country")
    posture_falcon_zta_score: PropertyRef = PropertyRef("posture_falcon_zta_score")
    posture_sentinelone_operational_state: PropertyRef = PropertyRef(
        "posture_sentinelone_operational_state"
    )
    posture_sentinelone_active_threats: PropertyRef = PropertyRef(
        "posture_sentinelone_active_threats"
    )
    posture_sentinelone_agent_version: PropertyRef = PropertyRef(
        "posture_sentinelone_agent_version"
    )
    posture_sentinelone_encrypted_applications: PropertyRef = PropertyRef(
        "posture_sentinelone_encrypted_applications"
    )
    posture_sentinelone_firewall_enabled: PropertyRef = PropertyRef(
        "posture_sentinelone_firewall_enabled"
    )
    posture_sentinelone_infected: PropertyRef = PropertyRef(
        "posture_sentinelone_infected"
    )
    posture_kolide_auth_state: PropertyRef = PropertyRef("posture_kolide_auth_state")
    posture_fleet_present: PropertyRef = PropertyRef("posture_fleet_present")
    posture_fleet_policies: PropertyRef = PropertyRef("posture_fleet_policies")
    posture_huntress_defender_status: PropertyRef = PropertyRef(
        "posture_huntress_defender_status"
    )
    posture_huntress_defender_policy_status: PropertyRef = PropertyRef(
        "posture_huntress_defender_policy_status"
    )
    posture_huntress_firewall_status: PropertyRef = PropertyRef(
        "posture_huntress_firewall_status"
    )
    posture_kandji_mdm_enabled: PropertyRef = PropertyRef("posture_kandji_mdm_enabled")
    posture_kandji_agent_installed: PropertyRef = PropertyRef(
        "posture_kandji_agent_installed"
    )
    posture_jamfpro_remote_managed: PropertyRef = PropertyRef(
        "posture_jamfpro_remote_managed"
    )
    posture_jamfpro_supervised: PropertyRef = PropertyRef("posture_jamfpro_supervised")
    posture_jamfpro_firewall_enabled: PropertyRef = PropertyRef(
        "posture_jamfpro_firewall_enabled"
    )
    posture_jamfpro_file_vault_status: PropertyRef = PropertyRef(
        "posture_jamfpro_file_vault_status"
    )
    posture_jamfpro_sip_enabled: PropertyRef = PropertyRef(
        "posture_jamfpro_sip_enabled"
    )
    posture_intune_compliance_state: PropertyRef = PropertyRef(
        "posture_intune_compliance_state"
    )
    posture_intune_azure_ad_registered: PropertyRef = PropertyRef(
        "posture_intune_azure_ad_registered"
    )
    posture_intune_device_registration_state: PropertyRef = PropertyRef(
        "posture_intune_device_registration_state"
    )
    posture_intune_is_supervised: PropertyRef = PropertyRef(
        "posture_intune_is_supervised"
    )
    posture_intune_is_encrypted: PropertyRef = PropertyRef(
        "posture_intune_is_encrypted"
    )
    posture_intune_managed_device_owner_type: PropertyRef = PropertyRef(
        "posture_intune_managed_device_owner_type"
    )


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
