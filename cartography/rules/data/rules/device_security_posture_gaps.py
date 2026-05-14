from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class DeviceSecurityPostureGapOutput(Finding):
    provider: str | None = None
    device_id: str | None = None
    device_name: str | None = None
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
    asset_id_field="device_id",
    module=Module.DUO,
    maturity=Maturity.EXPERIMENTAL,
)


_duo_phone_posture_gaps = Fact(
    id="duo_phone_posture_gaps",
    name="Duo phones with security posture gaps",
    description=(
        "Detects Duo phones that are explicitly unencrypted, lack screen lock, "
        "or are marked tampered."
    ),
    cypher_query="""
    MATCH (phone:DuoPhone)
    OPTIONAL MATCH (user:DuoUser)-[:HAS_DUO_PHONE]->(phone)
    WITH phone, user,
        [
            issue IN [
                CASE WHEN phone.encrypted = false THEN ['phone_not_encrypted', toString(phone.encrypted)] END,
                CASE WHEN phone.screenlock = false THEN ['screenlock_disabled', toString(phone.screenlock)] END,
                CASE WHEN phone.tampered = true THEN ['device_tampered', toString(phone.tampered)] END
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
       OR phone.tampered = true
    OPTIONAL MATCH p=(user:DuoUser)-[:HAS_DUO_PHONE]->(phone)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (phone:DuoPhone)
    RETURN COUNT(phone) AS count
    """,
    asset_id_field="device_id",
    module=Module.DUO,
    maturity=Maturity.EXPERIMENTAL,
)


_jamf_computer_posture_gaps = Fact(
    id="jamf_computer_posture_gaps",
    name="Jamf computers with security posture gaps",
    description=(
        "Detects Jamf computers with explicit FileVault, firewall, Gatekeeper, "
        "SIP, supervision, MDM approval, or management gaps."
    ),
    cypher_query="""
    MATCH (computer:JamfComputer)
    WITH computer,
        [
            issue IN [
                CASE WHEN computer.filevault_enabled = false THEN ['filevault_disabled', toString(computer.filevault_enabled)] END,
                CASE WHEN computer.firewall_enabled = false THEN ['firewall_disabled', toString(computer.firewall_enabled)] END,
                CASE WHEN computer.supervised = false THEN ['not_supervised', toString(computer.supervised)] END,
                CASE WHEN computer.user_approved_mdm = false THEN ['user_approved_mdm_missing', toString(computer.user_approved_mdm)] END,
                CASE WHEN computer.remote_management_managed = false THEN ['remote_management_not_managed', toString(computer.remote_management_managed)] END,
                CASE
                    WHEN computer.gatekeeper_status IS NOT NULL
                     AND NOT (toLower(toString(computer.gatekeeper_status)) IN ['enabled', 'true', 'on'])
                    THEN ['gatekeeper_not_enabled', toString(computer.gatekeeper_status)]
                END,
                CASE
                    WHEN computer.sip_status IS NOT NULL
                     AND NOT (toLower(toString(computer.sip_status)) IN ['enabled', 'true', 'on'])
                    THEN ['sip_not_enabled', toString(computer.sip_status)]
                END
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
       OR computer.supervised = false
       OR computer.user_approved_mdm = false
       OR computer.remote_management_managed = false
       OR (
            computer.gatekeeper_status IS NOT NULL
            AND NOT (toLower(toString(computer.gatekeeper_status)) IN ['enabled', 'true', 'on'])
       )
       OR (
            computer.sip_status IS NOT NULL
            AND NOT (toLower(toString(computer.sip_status)) IN ['enabled', 'true', 'on'])
       )
    RETURN computer
    """,
    cypher_count_query="""
    MATCH (computer:JamfComputer)
    RETURN COUNT(computer) AS count
    """,
    asset_id_field="device_id",
    module=Module.JAMF,
    maturity=Maturity.EXPERIMENTAL,
)


_jamf_mobile_device_posture_gaps = Fact(
    id="jamf_mobile_device_posture_gaps",
    name="Jamf mobile devices with security posture gaps",
    description=(
        "Detects Jamf mobile devices with explicit management, supervision, "
        "encryption, passcode, or jailbreak posture failures."
    ),
    cypher_query="""
    MATCH (device:JamfMobileDevice)
    WITH device,
        [
            issue IN [
                CASE WHEN device.managed = false THEN ['not_managed', toString(device.managed)] END,
                CASE WHEN device.supervised = false THEN ['not_supervised', toString(device.supervised)] END,
                CASE WHEN device.data_protected = false THEN ['data_protection_disabled', toString(device.data_protected)] END,
                CASE WHEN device.hardware_encryption = false THEN ['hardware_encryption_disabled', toString(device.hardware_encryption)] END,
                CASE WHEN device.passcode_present = false THEN ['passcode_missing', toString(device.passcode_present)] END,
                CASE WHEN device.passcode_compliant = false THEN ['passcode_noncompliant', toString(device.passcode_compliant)] END,
                CASE WHEN device.jailbreak_detected = true THEN ['jailbreak_detected', toString(device.jailbreak_detected)] END
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
    WHERE device.managed = false
       OR device.supervised = false
       OR device.data_protected = false
       OR device.hardware_encryption = false
       OR device.passcode_present = false
       OR device.passcode_compliant = false
       OR device.jailbreak_detected = true
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:JamfMobileDevice)
    RETURN COUNT(device) AS count
    """,
    asset_id_field="device_id",
    module=Module.JAMF,
    maturity=Maturity.EXPERIMENTAL,
)


_tailscale_device_posture_gaps = Fact(
    id="tailscale_device_posture_gaps",
    name="Tailscale devices with security posture gaps",
    description=(
        "Detects Tailscale devices with explicit update, encryption, firewall, "
        "EDR, MDM, or compliance posture failures from Tailscale device posture data."
    ),
    cypher_query="""
    MATCH (device:TailscaleDevice)
    OPTIONAL MATCH (user:TailscaleUser)-[:OWNS]->(device)
    WITH device, user,
        [
            issue IN [
                CASE WHEN device.update_available = true THEN ['tailscale_update_available', toString(device.update_available)] END,
                CASE WHEN device.posture_node_ts_state_encrypted = false THEN ['tailscale_state_not_encrypted', toString(device.posture_node_ts_state_encrypted)] END,
                CASE WHEN device.posture_sentinelone_active_threats IS NOT NULL AND toInteger(device.posture_sentinelone_active_threats) > 0 THEN ['sentinelone_active_threats', toString(device.posture_sentinelone_active_threats)] END,
                CASE WHEN device.posture_sentinelone_infected = true THEN ['sentinelone_infected', toString(device.posture_sentinelone_infected)] END,
                CASE WHEN device.posture_sentinelone_firewall_enabled = false THEN ['sentinelone_firewall_disabled', toString(device.posture_sentinelone_firewall_enabled)] END,
                CASE WHEN device.posture_kandji_mdm_enabled = false THEN ['kandji_mdm_disabled', toString(device.posture_kandji_mdm_enabled)] END,
                CASE WHEN device.posture_kandji_agent_installed = false THEN ['kandji_agent_missing', toString(device.posture_kandji_agent_installed)] END,
                CASE WHEN device.posture_jamfpro_remote_managed = false THEN ['jamfpro_not_remote_managed', toString(device.posture_jamfpro_remote_managed)] END,
                CASE WHEN device.posture_jamfpro_supervised = false THEN ['jamfpro_not_supervised', toString(device.posture_jamfpro_supervised)] END,
                CASE WHEN device.posture_jamfpro_firewall_enabled = false THEN ['jamfpro_firewall_disabled', toString(device.posture_jamfpro_firewall_enabled)] END,
                CASE
                    WHEN device.posture_jamfpro_file_vault_status IS NOT NULL
                     AND NOT (toLower(toString(device.posture_jamfpro_file_vault_status)) IN ['enabled', 'true', 'on'])
                    THEN ['jamfpro_filevault_not_enabled', toString(device.posture_jamfpro_file_vault_status)]
                END,
                CASE WHEN device.posture_jamfpro_sip_enabled = false THEN ['jamfpro_sip_disabled', toString(device.posture_jamfpro_sip_enabled)] END,
                CASE
                    WHEN device.posture_intune_compliance_state IS NOT NULL
                     AND NOT (toLower(toString(device.posture_intune_compliance_state)) IN ['compliant'])
                    THEN ['intune_noncompliant', toString(device.posture_intune_compliance_state)]
                END,
                CASE WHEN device.posture_intune_is_encrypted = false THEN ['intune_not_encrypted', toString(device.posture_intune_is_encrypted)] END,
                CASE WHEN device.posture_intune_is_supervised = false THEN ['intune_not_supervised', toString(device.posture_intune_is_supervised)] END
            ]
            WHERE issue IS NOT NULL
        ] AS issues
    UNWIND issues AS issue
    RETURN
        'tailscale' AS provider,
        device.id AS device_id,
        coalesce(device.hostname, device.name, device.id) AS device_name,
        coalesce(user.email, user.login_name) AS user,
        coalesce(device.os, device.posture_node_os) AS platform,
        issue[0] AS issue,
        issue[1] AS current_value
    """,
    cypher_visual_query="""
    MATCH (device:TailscaleDevice)
    WHERE device.update_available = true
       OR device.posture_node_ts_state_encrypted = false
       OR (device.posture_sentinelone_active_threats IS NOT NULL AND toInteger(device.posture_sentinelone_active_threats) > 0)
       OR device.posture_sentinelone_infected = true
       OR device.posture_sentinelone_firewall_enabled = false
       OR device.posture_kandji_mdm_enabled = false
       OR device.posture_kandji_agent_installed = false
       OR device.posture_jamfpro_remote_managed = false
       OR device.posture_jamfpro_supervised = false
       OR device.posture_jamfpro_firewall_enabled = false
       OR (
            device.posture_jamfpro_file_vault_status IS NOT NULL
            AND NOT (toLower(toString(device.posture_jamfpro_file_vault_status)) IN ['enabled', 'true', 'on'])
       )
       OR device.posture_jamfpro_sip_enabled = false
       OR (
            device.posture_intune_compliance_state IS NOT NULL
            AND NOT (toLower(toString(device.posture_intune_compliance_state)) IN ['compliant'])
       )
       OR device.posture_intune_is_encrypted = false
       OR device.posture_intune_is_supervised = false
    RETURN device
    """,
    cypher_count_query="""
    MATCH (device:TailscaleDevice)
    RETURN COUNT(device) AS count
    """,
    asset_id_field="device_id",
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


device_security_posture_gaps = Rule(
    id="device_security_posture_gaps",
    name="Device Security Posture Gaps",
    description=(
        "Detects explicit encryption, compliance, endpoint protection, update, "
        "and management posture gaps on devices already ingested from Duo, "
        "Jamf, and Tailscale."
    ),
    output_model=DeviceSecurityPostureGapOutput,
    facts=(
        _duo_endpoint_posture_gaps,
        _duo_phone_posture_gaps,
        _jamf_computer_posture_gaps,
        _jamf_mobile_device_posture_gaps,
        _tailscale_device_posture_gaps,
    ),
    tags=("device", "endpoint", "compliance", "vulnerability", "stride:tampering"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.1"),
        iso27001_annex_a("8.8"),
        iso27001_annex_a("8.9"),
    ),
)
