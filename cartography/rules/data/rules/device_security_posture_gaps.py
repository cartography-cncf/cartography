from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class DeviceSecurityPostureGapOutput(Finding):
    device_name: str | None = None
    provider: str | None = None
    device_id: str | None = None
    stable_device_id: str | None = None
    # Tailnet that owns the device; only the Tailscale fact sets it (used in identity).
    tailnet_id: str | None = None
    user: str | None = None
    platform: str | None = None
    issue: str | None = None
    current_value: str | None = None


_duo_endpoint_posture_gaps = Fact(
    id="duo_endpoint_posture_gaps",
    name="Duo endpoints with security posture gaps",
    description=(
        "Detects Duo endpoints with explicit disk encryption, firewall, password, "
        "or trusted-endpoint posture failures."
    ),
    cypher_query="""
    MATCH (endpoint:DuoEndpoint)
    WITH endpoint,
        [
            issue IN [
                CASE
                    WHEN endpoint.disk_encryption_status IS NOT NULL
                     AND NOT (toLower(toString(endpoint.disk_encryption_status)) IN ['encrypted', 'on', 'enabled', 'true'])
                    THEN ['disk_encryption_not_enabled', toString(endpoint.disk_encryption_status)]
                END,
                CASE
                    WHEN endpoint.firewall_status IS NOT NULL
                     AND NOT (toLower(toString(endpoint.firewall_status)) IN ['enabled', 'on', 'true'])
                    THEN ['firewall_not_enabled', toString(endpoint.firewall_status)]
                END,
                CASE
                    WHEN endpoint.password_status IS NOT NULL
                     AND NOT (toLower(toString(endpoint.password_status)) IN ['set', 'enabled', 'true', 'ok'])
                    THEN ['password_not_set_or_noncompliant', toString(endpoint.password_status)]
                END,
                CASE
                    WHEN endpoint.trusted_endpoint IS NOT NULL
                     AND NOT (toLower(toString(endpoint.trusted_endpoint)) IN ['true', 'trusted'])
                    THEN ['not_trusted_endpoint', toString(endpoint.trusted_endpoint)]
                END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'duo' AS provider,
        endpoint.id AS device_id,
        coalesce(endpoint.device_name, endpoint.device_identifier, endpoint.id) AS device_name,
        coalesce(endpoint.email, endpoint.username, endpoint.device_username) AS user,
        endpoint.os_family AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (endpoint:DuoEndpoint)
    WHERE (
        endpoint.disk_encryption_status IS NOT NULL
        AND NOT (toLower(toString(endpoint.disk_encryption_status)) IN ['encrypted', 'on', 'enabled', 'true'])
    ) OR (
        endpoint.firewall_status IS NOT NULL
        AND NOT (toLower(toString(endpoint.firewall_status)) IN ['enabled', 'on', 'true'])
    ) OR (
        endpoint.password_status IS NOT NULL
        AND NOT (toLower(toString(endpoint.password_status)) IN ['set', 'enabled', 'true', 'ok'])
    ) OR (
        endpoint.trusted_endpoint IS NOT NULL
        AND NOT (toLower(toString(endpoint.trusted_endpoint)) IN ['true', 'trusted'])
    )
    RETURN endpoint
    """,
    cypher_count_query="""
    MATCH (endpoint:DuoEndpoint)
    RETURN COUNT(endpoint) AS count
    """,
    asset_label="DuoEndpoint",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.DUO,
    maturity=Maturity.EXPERIMENTAL,
)


_duo_phone_posture_gaps = Fact(
    id="duo_phone_posture_gaps",
    name="Duo phones with data protection gaps",
    description=(
        "Detects Duo phones that are explicitly unencrypted or lack screen lock."
    ),
    cypher_query="""
    MATCH (phone:DuoPhone)
    OPTIONAL MATCH (user:DuoUser)-[:HAS_DUO_PHONE]->(phone)
    WITH phone, user,
        [
            issue IN [
                CASE WHEN phone.encrypted = false THEN ['phone_not_encrypted', toString(phone.encrypted)] END,
                CASE WHEN phone.screenlock = false THEN ['screenlock_disabled', toString(phone.screenlock)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'duo' AS provider,
        phone.id AS device_id,
        coalesce(phone.name, phone.model, phone.id) AS device_name,
        coalesce(user.email, user.username) AS user,
        phone.platform AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (phone:DuoPhone)
    WHERE phone.encrypted = false
       OR phone.screenlock = false
    OPTIONAL MATCH p=(user:DuoUser)-[:HAS_DUO_PHONE]->(phone)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (phone:DuoPhone)
    RETURN COUNT(phone) AS count
    """,
    asset_label="DuoPhone",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.DUO,
    maturity=Maturity.EXPERIMENTAL,
)


_jamf_computer_posture_gaps = Fact(
    id="jamf_computer_posture_gaps",
    name="Jamf computers with data protection gaps",
    description=("Detects Jamf computers with explicit FileVault or firewall gaps."),
    cypher_query="""
    MATCH (computer:JamfComputer)
    WITH computer,
        [
            issue IN [
                CASE WHEN computer.filevault_enabled = false THEN ['filevault_disabled', toString(computer.filevault_enabled)] END,
                CASE WHEN computer.firewall_enabled = false THEN ['firewall_disabled', toString(computer.firewall_enabled)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'jamf' AS provider,
        computer.id AS device_id,
        coalesce(computer.name, computer.serial_number, computer.id) AS device_name,
        coalesce(computer.email, computer.username) AS user,
        coalesce(computer.platform, computer.os_name) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (computer:JamfComputer)
    WHERE computer.filevault_enabled = false
       OR computer.firewall_enabled = false
    RETURN computer
    """,
    cypher_count_query="""
    MATCH (computer:JamfComputer)
    RETURN COUNT(computer) AS count
    """,
    asset_label="JamfComputer",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.JAMF,
    maturity=Maturity.EXPERIMENTAL,
)


_jamf_mobile_device_posture_gaps = Fact(
    id="jamf_mobile_device_posture_gaps",
    name="Jamf mobile devices with data protection gaps",
    description=(
        "Detects Jamf mobile devices with explicit encryption or passcode failures."
    ),
    cypher_query="""
    MATCH (device:JamfMobileDevice)
    WITH device,
        [
            issue IN [
                CASE WHEN device.data_protected = false THEN ['data_protection_disabled', toString(device.data_protected)] END,
                CASE WHEN device.hardware_encryption = false THEN ['hardware_encryption_disabled', toString(device.hardware_encryption)] END,
                CASE WHEN device.passcode_present = false THEN ['passcode_missing', toString(device.passcode_present)] END,
                CASE WHEN device.passcode_compliant = false THEN ['passcode_noncompliant', toString(device.passcode_compliant)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'jamf' AS provider,
        device.id AS device_id,
        coalesce(device.display_name, device.serial_number, device.id) AS device_name,
        coalesce(device.email, device.username) AS user,
        coalesce(device.platform, device.os) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:JamfMobileDevice)
    WHERE device.data_protected = false
       OR device.hardware_encryption = false
       OR device.passcode_present = false
       OR device.passcode_compliant = false
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:JamfMobileDevice)
    RETURN COUNT(device) AS count
    """,
    asset_label="JamfMobileDevice",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.JAMF,
    maturity=Maturity.EXPERIMENTAL,
)


_tailscale_device_posture_gaps = Fact(
    id="tailscale_device_posture_gaps",
    name="Tailscale devices with data protection gaps",
    description=(
        "Detects Tailscale devices with explicit encryption or firewall posture "
        "failures from Tailscale device posture data."
    ),
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)-[:RESOURCE]->(device:TailscaleDevice)
    OPTIONAL MATCH (user:TailscaleUser)-[:OWNS]->(device)
    WITH tailnet, device, user,
        [
            issue IN [
                CASE WHEN device.posture_node_ts_state_encrypted = false THEN ['tailscale_state_not_encrypted', toString(device.posture_node_ts_state_encrypted)] END,
                CASE WHEN device.posture_sentinelone_firewall_enabled = false THEN ['sentinelone_firewall_disabled', toString(device.posture_sentinelone_firewall_enabled)] END,
                CASE WHEN device.posture_jamfpro_firewall_enabled = false THEN ['jamfpro_firewall_disabled', toString(device.posture_jamfpro_firewall_enabled)] END,
                CASE
                    WHEN device.posture_jamfpro_file_vault_status IS NOT NULL
                     AND NOT (toLower(toString(device.posture_jamfpro_file_vault_status)) IN ['enabled', 'true', 'on'])
                    THEN ['jamfpro_filevault_not_enabled', toString(device.posture_jamfpro_file_vault_status)]
                END,
                CASE WHEN device.posture_intune_is_encrypted = false THEN ['intune_not_encrypted', toString(device.posture_intune_is_encrypted)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'tailscale' AS provider,
        tailnet.id AS tailnet_id,
        device.id AS device_id,
        coalesce(device.hostname, device.name, device.id) AS device_name,
        coalesce(user.email, user.login_name) AS user,
        coalesce(device.os, device.posture_node_os) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:TailscaleDevice)
    WHERE device.posture_node_ts_state_encrypted = false
       OR device.posture_sentinelone_firewall_enabled = false
       OR device.posture_jamfpro_firewall_enabled = false
       OR (
            device.posture_jamfpro_file_vault_status IS NOT NULL
            AND NOT (toLower(toString(device.posture_jamfpro_file_vault_status)) IN ['enabled', 'true', 'on'])
       )
       OR device.posture_intune_is_encrypted = false
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:TailscaleDevice)
    RETURN COUNT(device) AS count
    """,
    asset_label="TailscaleDevice",
    asset_id_field="device_id",
    # Key on tailnet + stable hostname, not device.id: Tailscale ephemeral nodes get
    # a fresh device.id on every reconnect, which would re-create the same finding.
    # tailnet_id keeps the identity unique across tailnets that reuse a hostname.
    identity_fields=("tailnet_id", "device_name", "issue"),
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


_duo_phone_malware_protection_gaps = Fact(
    id="duo_phone_malware_protection_gaps",
    name="Duo phones with malware protection gaps",
    description="Detects Duo phones that are explicitly marked as tampered.",
    cypher_query="""
    MATCH (device:DuoPhone)
    WHERE device.tampered = true
    OPTIONAL MATCH (user:DuoUser)-[:HAS_DUO_PHONE]->(device)
    RETURN
        'duo' AS provider,
        device.id AS device_id,
        device.id AS stable_device_id,
        coalesce(device.name, device.model, device.id) AS device_name,
        coalesce(user.email, user.username) AS user,
        device.platform AS platform,
        'device_tampered' AS issue,
        toString(device.tampered) AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:DuoPhone)
    WHERE device.tampered = true
    OPTIONAL MATCH p=(user:DuoUser)-[:HAS_DUO_PHONE]->(device)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (device:DuoPhone)
    RETURN COUNT(device) AS count
    """,
    asset_label="DuoPhone",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.DUO,
    maturity=Maturity.EXPERIMENTAL,
)


_jamf_computer_malware_protection_gaps = Fact(
    id="jamf_computer_malware_protection_gaps",
    name="Jamf computers with malware protection gaps",
    description=(
        "Detects Jamf computers with disabled Gatekeeper or system integrity "
        "protection."
    ),
    cypher_query="""
    MATCH (device:JamfComputer)
    WITH device,
        [
            issue IN [
                CASE
                    WHEN device.gatekeeper_status IS NOT NULL
                     AND NOT (toLower(toString(device.gatekeeper_status)) IN ['enabled', 'true', 'on'])
                    THEN ['gatekeeper_not_enabled', toString(device.gatekeeper_status)]
                END,
                CASE
                    WHEN device.sip_status IS NOT NULL
                     AND NOT (toLower(toString(device.sip_status)) IN ['enabled', 'true', 'on'])
                    THEN ['sip_not_enabled', toString(device.sip_status)]
                END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'jamf' AS provider,
        device.id AS device_id,
        device.id AS stable_device_id,
        coalesce(device.name, device.serial_number, device.id) AS device_name,
        coalesce(device.email, device.username) AS user,
        coalesce(device.platform, device.os_name) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:JamfComputer)
    WHERE (
        device.gatekeeper_status IS NOT NULL
        AND NOT (toLower(toString(device.gatekeeper_status)) IN ['enabled', 'true', 'on'])
    ) OR (
        device.sip_status IS NOT NULL
        AND NOT (toLower(toString(device.sip_status)) IN ['enabled', 'true', 'on'])
    )
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:JamfComputer)
    RETURN COUNT(device) AS count
    """,
    asset_label="JamfComputer",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.JAMF,
    maturity=Maturity.EXPERIMENTAL,
)


_jamf_mobile_device_malware_protection_gaps = Fact(
    id="jamf_mobile_device_malware_protection_gaps",
    name="Jamf mobile devices with malware protection gaps",
    description="Detects Jamf mobile devices with a detected jailbreak.",
    cypher_query="""
    MATCH (device:JamfMobileDevice)
    WHERE device.jailbreak_detected = true
    RETURN
        'jamf' AS provider,
        device.id AS device_id,
        device.id AS stable_device_id,
        coalesce(device.display_name, device.serial_number, device.id) AS device_name,
        coalesce(device.email, device.username) AS user,
        coalesce(device.platform, device.os) AS platform,
        'jailbreak_detected' AS issue,
        toString(device.jailbreak_detected) AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:JamfMobileDevice)
    WHERE device.jailbreak_detected = true
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:JamfMobileDevice)
    RETURN COUNT(device) AS count
    """,
    asset_label="JamfMobileDevice",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.JAMF,
    maturity=Maturity.EXPERIMENTAL,
)


_crowdstrike_host_malware_protection_gaps = Fact(
    id="crowdstrike_host_malware_protection_gaps",
    name="CrowdStrike hosts with malware protection gaps",
    description=("Detects CrowdStrike hosts running in reduced functionality mode."),
    cypher_query="""
    MATCH (device:CrowdstrikeHost)
    WHERE device.reduced_functionality_mode IS NOT NULL
      AND NOT (
          toLower(toString(device.reduced_functionality_mode))
          IN ['no', 'false', 'disabled', 'off']
      )
    RETURN
        'crowdstrike' AS provider,
        device.id AS device_id,
        device.id AS stable_device_id,
        coalesce(device.hostname, device.id) AS device_name,
        device.email AS user,
        device.platform_name AS platform,
        'crowdstrike_reduced_functionality_mode' AS issue,
        toString(device.reduced_functionality_mode) AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:CrowdstrikeHost)
    WHERE device.reduced_functionality_mode IS NOT NULL
      AND NOT (
          toLower(toString(device.reduced_functionality_mode))
          IN ['no', 'false', 'disabled', 'off']
      )
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:CrowdstrikeHost)
    RETURN COUNT(device) AS count
    """,
    asset_label="CrowdstrikeHost",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.CROWDSTRIKE,
    maturity=Maturity.EXPERIMENTAL,
)


_tailscale_device_malware_protection_gaps = Fact(
    id="tailscale_device_malware_protection_gaps",
    name="Tailscale devices with malware protection gaps",
    description=(
        "Detects Tailscale devices with active threats, infections, missing "
        "security agents, or disabled system integrity protection."
    ),
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)-[:RESOURCE]->(device:TailscaleDevice)
    OPTIONAL MATCH (user:TailscaleUser)-[:OWNS]->(device)
    WITH tailnet, device, user,
        [
            issue IN [
                CASE
                    WHEN device.posture_sentinelone_active_threats IS NOT NULL
                     AND toInteger(device.posture_sentinelone_active_threats) > 0
                    THEN ['sentinelone_active_threats', toString(device.posture_sentinelone_active_threats)]
                END,
                CASE WHEN device.posture_sentinelone_infected = true THEN ['sentinelone_infected', toString(device.posture_sentinelone_infected)] END,
                CASE WHEN device.posture_kandji_agent_installed = false THEN ['kandji_agent_missing', toString(device.posture_kandji_agent_installed)] END,
                CASE WHEN device.posture_jamfpro_sip_enabled = false THEN ['jamfpro_sip_disabled', toString(device.posture_jamfpro_sip_enabled)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'tailscale' AS provider,
        tailnet.id AS tailnet_id,
        device.id AS device_id,
        device.id AS stable_device_id,
        coalesce(device.hostname, device.name, device.id) AS device_name,
        coalesce(user.email, user.login_name) AS user,
        coalesce(device.os, device.posture_node_os) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:TailscaleDevice)
    WHERE (
        device.posture_sentinelone_active_threats IS NOT NULL
        AND toInteger(device.posture_sentinelone_active_threats) > 0
    )
       OR device.posture_sentinelone_infected = true
       OR device.posture_kandji_agent_installed = false
       OR device.posture_jamfpro_sip_enabled = false
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:TailscaleDevice)
    RETURN COUNT(device) AS count
    """,
    asset_label="TailscaleDevice",
    asset_id_field="device_id",
    identity_fields=("tailnet_id", "device_id", "issue"),
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


_device_update_gaps = Fact(
    id="device_update_gaps",
    name="Devices with available security updates",
    description="Detects Tailscale devices with an explicitly available update.",
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)-[:RESOURCE]->(device:TailscaleDevice)
    WHERE device.update_available = true
    OPTIONAL MATCH (user:TailscaleUser)-[:OWNS]->(device)
    RETURN
        'tailscale' AS provider,
        tailnet.id AS tailnet_id,
        device.id AS device_id,
        coalesce(device.hostname, device.name, device.id) AS device_name,
        coalesce(user.email, user.login_name) AS user,
        coalesce(device.os, device.posture_node_os) AS platform,
        'tailscale_update_available' AS issue,
        toString(device.update_available) AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:TailscaleDevice)
    WHERE device.update_available = true
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:TailscaleDevice)
    RETURN COUNT(device) AS count
    """,
    asset_label="TailscaleDevice",
    asset_id_field="device_id",
    identity_fields=("tailnet_id", "device_name", "issue"),
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


_jamf_computer_management_gaps = Fact(
    id="jamf_computer_management_gaps",
    name="Jamf computers with management gaps",
    description=(
        "Detects Jamf computers that are not supervised, MDM-approved, or "
        "remotely managed."
    ),
    cypher_query="""
    MATCH (device:JamfComputer)
    WITH device,
        [
            issue IN [
                CASE WHEN device.supervised = false THEN ['not_supervised', toString(device.supervised)] END,
                CASE WHEN device.user_approved_mdm = false THEN ['user_approved_mdm_missing', toString(device.user_approved_mdm)] END,
                CASE WHEN device.remote_management_managed = false THEN ['remote_management_not_managed', toString(device.remote_management_managed)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'jamf' AS provider,
        device.id AS device_id,
        device.id AS stable_device_id,
        coalesce(device.name, device.serial_number, device.id) AS device_name,
        coalesce(device.email, device.username) AS user,
        coalesce(device.platform, device.os_name) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:JamfComputer)
    WHERE device.supervised = false
       OR device.user_approved_mdm = false
       OR device.remote_management_managed = false
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:JamfComputer)
    RETURN COUNT(device) AS count
    """,
    asset_label="JamfComputer",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.JAMF,
    maturity=Maturity.EXPERIMENTAL,
)


_jamf_mobile_device_management_gaps = Fact(
    id="jamf_mobile_device_management_gaps",
    name="Jamf mobile devices with management gaps",
    description="Detects unmanaged or unsupervised Jamf mobile devices.",
    cypher_query="""
    MATCH (device:JamfMobileDevice)
    WITH device,
        [
            issue IN [
                CASE WHEN device.managed = false THEN ['not_managed', toString(device.managed)] END,
                CASE WHEN device.supervised = false THEN ['not_supervised', toString(device.supervised)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'jamf' AS provider,
        device.id AS device_id,
        device.id AS stable_device_id,
        coalesce(device.display_name, device.serial_number, device.id) AS device_name,
        coalesce(device.email, device.username) AS user,
        coalesce(device.platform, device.os) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:JamfMobileDevice)
    WHERE device.managed = false OR device.supervised = false
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:JamfMobileDevice)
    RETURN COUNT(device) AS count
    """,
    asset_label="JamfMobileDevice",
    asset_id_field="device_id",
    identity_fields=("device_id", "issue"),
    module=Module.JAMF,
    maturity=Maturity.EXPERIMENTAL,
)


_tailscale_device_management_gaps = Fact(
    id="tailscale_device_management_gaps",
    name="Tailscale devices with management gaps",
    description=(
        "Detects Tailscale devices that are not managed, supervised, or "
        "compliant according to device posture data."
    ),
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)-[:RESOURCE]->(device:TailscaleDevice)
    OPTIONAL MATCH (user:TailscaleUser)-[:OWNS]->(device)
    WITH tailnet, device, user,
        [
            issue IN [
                CASE WHEN device.posture_kandji_mdm_enabled = false THEN ['kandji_mdm_disabled', toString(device.posture_kandji_mdm_enabled)] END,
                CASE WHEN device.posture_jamfpro_remote_managed = false THEN ['jamfpro_not_remote_managed', toString(device.posture_jamfpro_remote_managed)] END,
                CASE WHEN device.posture_jamfpro_supervised = false THEN ['jamfpro_not_supervised', toString(device.posture_jamfpro_supervised)] END,
                CASE
                    WHEN device.posture_intune_compliance_state IS NOT NULL
                     AND NOT (toLower(toString(device.posture_intune_compliance_state)) IN ['compliant'])
                    THEN ['intune_noncompliant', toString(device.posture_intune_compliance_state)]
                END,
                CASE WHEN device.posture_intune_is_supervised = false THEN ['intune_not_supervised', toString(device.posture_intune_is_supervised)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'tailscale' AS provider,
        tailnet.id AS tailnet_id,
        device.id AS device_id,
        device.id AS stable_device_id,
        coalesce(device.hostname, device.name, device.id) AS device_name,
        coalesce(user.email, user.login_name) AS user,
        coalesce(device.os, device.posture_node_os) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:TailscaleDevice)
    WHERE device.posture_kandji_mdm_enabled = false
       OR device.posture_jamfpro_remote_managed = false
       OR device.posture_jamfpro_supervised = false
       OR (
            device.posture_intune_compliance_state IS NOT NULL
            AND NOT (toLower(toString(device.posture_intune_compliance_state)) IN ['compliant'])
       )
       OR device.posture_intune_is_supervised = false
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:TailscaleDevice)
    RETURN COUNT(device) AS count
    """,
    asset_label="TailscaleDevice",
    asset_id_field="device_id",
    identity_fields=("tailnet_id", "device_id", "issue"),
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


device_security_posture_gaps = Rule(
    id="device_security_posture_gaps",
    name="Device Data Protection Gaps",
    description=(
        "Detects explicit encryption, firewall, screen-lock, passcode, password, "
        "and trusted-endpoint posture gaps on devices ingested from Duo, Jamf, "
        "and Tailscale."
    ),
    output_model=DeviceSecurityPostureGapOutput,
    facts=(
        _duo_endpoint_posture_gaps,
        _duo_phone_posture_gaps,
        _jamf_computer_posture_gaps,
        _jamf_mobile_device_posture_gaps,
        _tailscale_device_posture_gaps,
    ),
    tags=("device", "endpoint", "encryption", "compliance", "stride:tampering"),
    version="0.3.0",
    frameworks=(
        iso27001_annex_a("8.1"),
        iso27001_annex_a("8.9"),
        soc2_tsc("CC6.1"),
    ),
)


device_malware_protection_gaps = Rule(
    id="device_malware_protection_gaps",
    name="Device Malware Protection Gaps",
    description=(
        "Detects explicit tampering, malware infections, active endpoint threats, "
        "missing security agents, reduced endpoint-protection functionality, and "
        "disabled platform integrity protections."
    ),
    output_model=DeviceSecurityPostureGapOutput,
    facts=(
        _duo_phone_malware_protection_gaps,
        _jamf_computer_malware_protection_gaps,
        _jamf_mobile_device_malware_protection_gaps,
        _crowdstrike_host_malware_protection_gaps,
        _tailscale_device_malware_protection_gaps,
    ),
    tags=("device", "endpoint", "malware", "edr", "stride:tampering"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.1"),
        iso27001_annex_a("8.8"),
        soc2_tsc("CC6.8"),
    ),
)

# =============================================================================
# TODO: SOC 2 CC6.8: Endpoint scan freshness
# SentinelOne last_successful_scan and scan_status are available, but a stale-scan
# finding requires an organization-defined maximum age. A provider-wide fixed
# threshold would encode policy that Cartography does not know.
# =============================================================================


device_update_gaps = Rule(
    id="device_update_gaps",
    name="Device Update Gaps",
    description="Detects devices with explicitly available security updates.",
    output_model=DeviceSecurityPostureGapOutput,
    facts=(_device_update_gaps,),
    tags=("device", "endpoint", "patching", "vulnerability"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.1"),
        iso27001_annex_a("8.8"),
        soc2_tsc("CC7.1"),
    ),
)


device_management_gaps = Rule(
    id="device_management_gaps",
    name="Device Management Gaps",
    description=(
        "Detects devices that are explicitly unmanaged, unsupervised, lack MDM "
        "approval, or are noncompliant according to their management provider."
    ),
    output_model=DeviceSecurityPostureGapOutput,
    facts=(
        _jamf_computer_management_gaps,
        _jamf_mobile_device_management_gaps,
        _tailscale_device_management_gaps,
    ),
    tags=("device", "endpoint", "mdm", "compliance"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.1"),
        iso27001_annex_a("8.9"),
        soc2_tsc("CC6.1"),
    ),
)


# =============================================================================
# TODO: SOC 2 CC6.5: Secure disposal of physical information assets
# Missing datamodel or evidence: device retirement and decommission state,
# remote-wipe or cryptographic-erasure requests, sanitization completion status,
# and storage-media disposal evidence from MDM and endpoint providers.
# =============================================================================
