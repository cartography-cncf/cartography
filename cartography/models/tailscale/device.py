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
    id: PropertyRef = PropertyRef(
        "nodeId", description="The preferred identifier for a device."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="The MagicDNS name of the device. Learn more about MagicDNS at https://tailscale.com/kb/1081/.",
    )
    hostname: PropertyRef = PropertyRef(
        "hostname",
        extra_index=True,
        description="The machine name in the admin console. Learn more about machine names at https://tailscale.com/kb/1098/.",
    )
    client_version: PropertyRef = PropertyRef(
        "clientVersion",
        description="The version of the Tailscale client software; this is empty for external devices.",
    )
    update_available: PropertyRef = PropertyRef(
        "updateAvailable",
        description="'true' if a Tailscale client version upgrade is available. This value is empty for external devices.",
    )
    os: PropertyRef = PropertyRef(
        "os", description="The operating system that the device is running."
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="The date on which the device was added to the tailnet; this is empty for external devices.",
    )
    last_seen: PropertyRef = PropertyRef(
        "lastSeen", description="When device was last active on the tailnet."
    )
    key_expiry_disabled: PropertyRef = PropertyRef(
        "keyExpiryDisabled",
        description="'true' if the keys for the device will not expire. Learn more at https://tailscale.com/kb/1028/.",
    )
    expires: PropertyRef = PropertyRef(
        "expires",
        description="The expiration date of the device's auth key. Learn more about key expiry at https://tailscale.com/kb/1028/.",
    )
    authorized: PropertyRef = PropertyRef(
        "authorized",
        description="'true' if the device has been authorized to join the tailnet; otherwise, 'false'. Learn more about device authorization at https://tailscale.com/kb/1099/.",
    )
    is_external: PropertyRef = PropertyRef(
        "isExternal",
        description="'true', indicates that a device is not a member of the tailnet, but is shared in to the tailnet; if 'false', the device is a member of the tailnet. Learn more about node sharing at https://tailscale.com/kb/1084/.",
    )
    node_key: PropertyRef = PropertyRef(
        "nodeKey",
        description="Mostly for internal use, required for select operations, such as adding a node to a locked tailnet. Learn about tailnet locks at https://tailscale.com/kb/1226/.",
    )
    addresses: PropertyRef = PropertyRef("addresses", description="Addresses.")
    blocks_incoming_connections: PropertyRef = PropertyRef(
        "blocksIncomingConnections",
        description="'true' if the device is not allowed to accept any connections over Tailscale, including pings. Learn more in the \"Allow incoming connections\" section of https://tailscale.com/kb/1072/.",
    )
    client_connectivity_endpoints: PropertyRef = PropertyRef(
        "clientConnectivity.endpoints",
        description="Client's magicsock UDP IP:port endpoints (IPv4 or IPv6).",
    )
    client_connectivity_mapping_varies_by_dest_ip: PropertyRef = PropertyRef(
        "clientConnectivity.mappingVariesByDestIP",
        description="'true' if the host's NAT mappings vary based on the destination IP.",
    )
    tailnet_lock_error: PropertyRef = PropertyRef(
        "tailnetLockError",
        description="Indicates an issue with the tailnet lock node-key signature on this device. This field is only populated when tailnet lock is enabled.",
    )
    tailnet_lock_key: PropertyRef = PropertyRef(
        "tailnetLockKey",
        description="The node's tailnet lock key. Every node generates a tailnet lock key (so the value will be present) even if tailnet lock is not enabled. Learn more about tailnet lock at https://tailscale.com/kb/1226/.",
    )
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        extra_index=True,
        description="The first serial number from posture identity, if available.",
    )
    posture_identity_serial_numbers: PropertyRef = PropertyRef(
        "postureIdentity.serialNumbers",
        description="Posture identification collection.",
    )
    posture_identity_disabled: PropertyRef = PropertyRef(
        "postureIdentity.disabled",
        description="Device posture identification collection enabled.",
    )
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
    posture_node_os: PropertyRef = PropertyRef(
        "posture_node_os", description="Device posture value for `node:os`."
    )
    posture_node_os_version: PropertyRef = PropertyRef(
        "posture_node_os_version",
        description="Device posture value for `node:osVersion`.",
    )
    posture_node_ts_auto_update: PropertyRef = PropertyRef(
        "posture_node_ts_auto_update",
        description="Device posture value for `node:tsAutoUpdate`.",
    )
    posture_node_ts_release_track: PropertyRef = PropertyRef(
        "posture_node_ts_release_track",
        description="Device posture value for `node:tsReleaseTrack`.",
    )
    posture_node_ts_state_encrypted: PropertyRef = PropertyRef(
        "posture_node_ts_state_encrypted",
        description="Device posture value for `node:tsStateEncrypted`.",
    )
    posture_node_ts_version: PropertyRef = PropertyRef(
        "posture_node_ts_version",
        description="Device posture value for `node:tsVersion`.",
    )
    posture_ip_country: PropertyRef = PropertyRef(
        "posture_ip_country", description="Device posture value for `ip:country`."
    )
    posture_falcon_zta_score: PropertyRef = PropertyRef(
        "posture_falcon_zta_score",
        description="Device posture value for `falcon:ztaScore`.",
    )
    posture_sentinelone_operational_state: PropertyRef = PropertyRef(
        "posture_sentinelone_operational_state",
        description="Device posture value for `sentinelOne:operationalState`.",
    )
    posture_sentinelone_active_threats: PropertyRef = PropertyRef(
        "posture_sentinelone_active_threats",
        description="Device posture value for `sentinelOne:activeThreats`.",
    )
    posture_sentinelone_agent_version: PropertyRef = PropertyRef(
        "posture_sentinelone_agent_version",
        description="Device posture value for `sentinelOne:agentVersion`.",
    )
    posture_sentinelone_encrypted_applications: PropertyRef = PropertyRef(
        "posture_sentinelone_encrypted_applications",
        description="Device posture value for `sentinelOne:encryptedApplications`.",
    )
    posture_sentinelone_firewall_enabled: PropertyRef = PropertyRef(
        "posture_sentinelone_firewall_enabled",
        description="Device posture value for `sentinelOne:firewallEnabled`.",
    )
    posture_sentinelone_infected: PropertyRef = PropertyRef(
        "posture_sentinelone_infected",
        description="Device posture value for `sentinelOne:infected`.",
    )
    posture_kolide_auth_state: PropertyRef = PropertyRef(
        "posture_kolide_auth_state",
        description="Device posture value for `kolide:authState`.",
    )
    posture_fleet_present: PropertyRef = PropertyRef(
        "posture_fleet_present", description="Device posture value for `fleet:present`."
    )
    posture_fleet_policies: PropertyRef = PropertyRef(
        "posture_fleet_policies",
        description="List of `fleetPolicy:*` posture keys present on the device.",
    )
    posture_huntress_defender_status: PropertyRef = PropertyRef(
        "posture_huntress_defender_status",
        description="Device posture value for `huntress:defenderStatus`.",
    )
    posture_huntress_defender_policy_status: PropertyRef = PropertyRef(
        "posture_huntress_defender_policy_status",
        description="Device posture value for `huntress:defenderPolicyStatus`.",
    )
    posture_huntress_firewall_status: PropertyRef = PropertyRef(
        "posture_huntress_firewall_status",
        description="Device posture value for `huntress:firewallStatus`.",
    )
    posture_kandji_mdm_enabled: PropertyRef = PropertyRef(
        "posture_kandji_mdm_enabled",
        description="Device posture value for `kandji:mdmEnabled`.",
    )
    posture_kandji_agent_installed: PropertyRef = PropertyRef(
        "posture_kandji_agent_installed",
        description="Device posture value for `kandji:agentInstalled`.",
    )
    posture_jamfpro_remote_managed: PropertyRef = PropertyRef(
        "posture_jamfpro_remote_managed",
        description="Device posture value for `jamfPro:remoteManaged`.",
    )
    posture_jamfpro_supervised: PropertyRef = PropertyRef(
        "posture_jamfpro_supervised",
        description="Device posture value for `jamfPro:supervised`.",
    )
    posture_jamfpro_firewall_enabled: PropertyRef = PropertyRef(
        "posture_jamfpro_firewall_enabled",
        description="Device posture value for `jamfPro:firewallEnabled`.",
    )
    posture_jamfpro_file_vault_status: PropertyRef = PropertyRef(
        "posture_jamfpro_file_vault_status",
        description="Device posture value for `jamfPro:fileVaultStatus`.",
    )
    posture_jamfpro_sip_enabled: PropertyRef = PropertyRef(
        "posture_jamfpro_sip_enabled",
        description="Device posture value for `jamfPro:SIPEnabled`.",
    )
    posture_intune_compliance_state: PropertyRef = PropertyRef(
        "posture_intune_compliance_state",
        description="Device posture value for `intune:complianceState`.",
    )
    posture_intune_azure_ad_registered: PropertyRef = PropertyRef(
        "posture_intune_azure_ad_registered",
        description="Device posture value for `intune:azureADRegistered`.",
    )
    posture_intune_device_registration_state: PropertyRef = PropertyRef(
        "posture_intune_device_registration_state",
        description="Device posture value for `intune:deviceRegistrationState`.",
    )
    posture_intune_is_supervised: PropertyRef = PropertyRef(
        "posture_intune_is_supervised",
        description="Device posture value for `intune:isSupervised`.",
    )
    posture_intune_is_encrypted: PropertyRef = PropertyRef(
        "posture_intune_is_encrypted",
        description="Device posture value for `intune:isEncrypted`.",
    )
    posture_intune_managed_device_owner_type: PropertyRef = PropertyRef(
        "posture_intune_managed_device_owner_type",
        description="Device posture value for `intune:managedDeviceOwnerType`.",
    )


@dataclass(frozen=True)
class TailscaleDeviceToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleTailnet)-[:RESOURCE]->(:TailscaleDevice)
class TailscaleDeviceToTailnetRel(CartographyRelSchema):
    """Defines the RESOURCE relationship to TailscaleTailnet nodes."""

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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
# (:TailscaleUser)-[:OWNS]->(:TailscaleDevice)
class TailscaleDeviceToUserRel(CartographyRelSchema):
    """Defines the OWNS relationship to TailscaleUser nodes."""

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
    """
    A Tailscale device (sometimes referred to as *node* or *machine*), is any computer
    or mobile device that joins a tailnet.
    """

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
