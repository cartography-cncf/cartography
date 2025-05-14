## Tailscale Schema

# CHANGEME: mermaid

# CHANGEME: add Group

### Tailnet

Settings for a tailnet.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| devices_approval_on | Whether [device approval](/kb/1099/device-approval) is enabled for the tailnet. |
| devices_auto_updates_on | Whether [auto updates](/kb/1067/update#auto-updates) are enabled for devices that belong to this tailnet. |
| devices_key_duration_days | The [key expiry](/kb/1028/key-expiry) duration for devices on this tailnet. |
| users_approval_on | Whether [user approval](/kb/1239/user-approval) is enabled for this tailnet. |
| users_role_allowed_to_join_external_tailnets | Which user roles are allowed to [join external tailnets](/kb/1271/invite-any-user). |
| network_flow_logging_on | Whether [network flog logs](/kb/1219/network-flow-logs) are enabled for the tailnet. |
| regional_routing_on | Whether [regional routing](/kb/1115/high-availability#regional-routing) is enabled for the tailnet. |
| posture_identity_collection_on | Whether [identity collection](/kb/1326/device-identity) is enabled for [device posture](/kb/1288/device-posture) integrations for the tailnet. |



### User

Representation of a user within a tailnet.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The unique identifier for the user.<br/>Supply this value wherever {userId} is indicated in an endpoint. |
| display_name | The name of the user. |
| login_name | The emailish login name of the user. |
| profile_pic_url | The profile pic URL for the user. |
| tailnet_id | The tailnet that owns the user. |
| created | The time the user joined their tailnet. |
| type | The type of relation this user has to the tailnet associated with the request. |
| role | The role of the user. Learn more about [user roles](kb/1138/user-roles). |
| status | The status of the user. |
| device_count | Number of devices the user owns. |
| last_seen | The later of either:<br/>- The last time any of the user's nodes were connected to the network.<br/>- The last time the user authenticated to any tailscale service, including the admin panel. |
| currently_connected | `true` when the user has a node currently connected to the control server. |



### Device

A Tailscale device (sometimes referred to as *node* or *machine*), is any computer or mobile device that joins a tailnet.<br/><br/>Each device has a unique ID (`nodeId` in the schema below) that is used to identify the device in API calls.<br/>This ID can be found by going to the [Machines](https://login.tailscale.com/admin/machines) page in the admin console,<br/>selecting the relevant device, then finding the ID in the Machine Details section.<br/>You can also [list all devices](#tag/devices/get/tailnet/{tailnet}/devices) in the tailnet to get their `nodeId` values.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| id | The legacy identifier for a device; you<br/>can supply this value wherever {deviceId} is indicated in the<br/>endpoint. Note that although "id" is still accepted, "nodeId" is<br/>preferred. |
| node_id | The preferred identifier for a device;<br/>supply this value wherever {deviceId} is indicated in the endpoint. |
| user | The user who registered the node. For untagged nodes,<br/> this user is the device owner. |
| name | The MagicDNS name of the device.<br/>Learn more about MagicDNS at https://tailscale.com/kb/1081/. |
| hostname | The machine name in the admin console.<br/>Learn more about machine names at https://tailscale.com/kb/1098/. |
| client_version | The version of the Tailscale client<br/>software; this is empty for external devices. |
| update_available | 'true' if a Tailscale client version<br/>upgrade is available. This value is empty for external devices. |
| os | The operating system that the device is running. |
| created | The date on which the device was added<br/>to the tailnet; this is empty for external devices. |
| last_seen | When device was last active on the tailnet. |
| key_expiry_disabled | 'true' if the keys for the device will not expire.<br/>Learn more at https://tailscale.com/kb/1028/. |
| expires | The expiration date of the device's auth key.<br/>Learn more about key expiry at https://tailscale.com/kb/1028/. |
| authorized | 'true' if the device has been authorized to join the tailnet; otherwise, 'false'.<br/>Learn more about device authorization at https://tailscale.com/kb/1099/. |
| is_external | 'true', indicates that a device is not a member of the tailnet, but is shared in to the tailnet;<br/>if 'false', the device is a member of the tailnet.<br/>Learn more about node sharing at https://tailscale.com/kb/1084/. |
| machine_key | For internal use and is not required for any API operations.<br/>This value is empty for external devices. |
| node_key | Mostly for internal use, required for select operations, such as adding a node to a locked tailnet.<br/>Learn about tailnet locks at https://tailscale.com/kb/1226/. |
| blocks_incoming_connections | 'true' if the device is not allowed to accept any connections over Tailscale, including pings.<br/>Learn more in the "Allow incoming connections" section of https://tailscale.com/kb/1072/. |
| clientConnectivity_endpoints | Client's magicsock UDP IP:port endpoints (IPv4 or IPv6). |
| clientConnectivity_mapping_varies_by_dest_ip | 'true' if the host's NAT mappings vary based on the destination IP. |
| tailnet_lock_error | Indicates an issue with the tailnet lock node-key signature on this device.<br/>This field is only populated when tailnet lock is enabled. |
| tailnet_lock_key | The node's tailnet lock key.<br/>Every node generates a tailnet lock key (so the value will be present) even if tailnet lock is not enabled.<br/>Learn more about tailnet lock at https://tailscale.com/kb/1226/. |
| postureIdentity_serial_numbers |  |
| postureIdentity_disabled |  |



### PostureIntegration

A configured PostureIntegration.

| Field | Description |
|-------|-------------|
| firstseen| Timestamp of when a sync job first created this node  |
| lastupdated |  Timestamp of the last time the node was updated |
| provider | The device posture provider.<br/><br/>Required on POST requests, ignored on PATCH requests. |
| cloud_id | Identifies which of the provider's clouds to integrate with.<br/><br/>- For CrowdStrike Falcon, it will be one of `us-1`, `us-2`, `eu-1` or `us-gov`.<br/>- For Microsoft Intune, it will be one of `global` or `us-gov`. <br/>- For Jamf Pro, Kandji and Sentinel One, it is the FQDN of your subdomain, for example `mydomain.sentinelone.net`.<br/>- For Kolide, this is left blank. |
| client_id | Unique identifier for your client.<br/><br/>- For Microsoft Intune, it will be your application's UUID.<br/>- For CrowdStrike Falcon and Jamf Pro, it will be your client id.<br/>- For Kandji, Kolide and Sentinel One, this is left blank. |
| tenant_id | The Microsoft Intune directory (tenant) ID. For other providers, this is left blank. |
| client_secret | The secret (auth key, token, etc.) used to authenticate with the provider.<br/><br/>Required when creating a new integration, may be omitted when updating an existing integration, in which case we retain the existing password. |
| id | A unique identifier for the integration (generated by the system). |
| config_updated | Timestamp of the last time this configuration was updated, in RFC 3339 format. |
| status_last_sync | Timestamp of the last synchronization with the device posture provider, in RFC 3339 format. |
| status_error | If the last synchronization failed, this shows the error message associated with the failed synchronization. |
| status_provider_host_count | The number of devices known to the provider. |
| status_matched_count | The number of Tailscale nodes that were matched with provider. |
| status_possible_matched_count | The number of Tailscale nodes with identifiers for matching. |
