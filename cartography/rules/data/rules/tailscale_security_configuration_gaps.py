from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class TailscaleSecurityConfigurationGapOutput(Finding):
    tailnet_id: str | None = None
    asset_id: str | None = None
    asset_name: str | None = None
    asset_type: str | None = None
    issue: str | None = None
    current_value: str | None = None


_tailscale_device_approval_disabled = Fact(
    id="tailscale_device_approval_disabled",
    name="Tailscale tailnets with device approval disabled",
    description="Detects Tailscale tailnets where new device approval is disabled.",
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)
    WHERE toLower(toString(tailnet.devices_approval_on)) = 'false'
    RETURN
        tailnet.id AS tailnet_id,
        tailnet.id AS asset_id,
        tailnet.id AS asset_name,
        'tailnet' AS asset_type,
        'device_approval_disabled' AS issue,
        toString(tailnet.devices_approval_on) AS current_value
    """,
    cypher_visual_query="""
    MATCH (tailnet:TailscaleTailnet)
    WHERE toLower(toString(tailnet.devices_approval_on)) = 'false'
    RETURN tailnet
    """,
    cypher_count_query="""
    MATCH (tailnet:TailscaleTailnet)
    RETURN COUNT(tailnet) AS count
    """,
    asset_id_field="asset_id",
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


_tailscale_user_approval_disabled = Fact(
    id="tailscale_user_approval_disabled",
    name="Tailscale tailnets with user approval disabled",
    description="Detects Tailscale tailnets where new user approval is disabled.",
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)
    WHERE toLower(toString(tailnet.users_approval_on)) = 'false'
    RETURN
        tailnet.id AS tailnet_id,
        tailnet.id AS asset_id,
        tailnet.id AS asset_name,
        'tailnet' AS asset_type,
        'user_approval_disabled' AS issue,
        toString(tailnet.users_approval_on) AS current_value
    """,
    cypher_visual_query="""
    MATCH (tailnet:TailscaleTailnet)
    WHERE toLower(toString(tailnet.users_approval_on)) = 'false'
    RETURN tailnet
    """,
    cypher_count_query="""
    MATCH (tailnet:TailscaleTailnet)
    RETURN COUNT(tailnet) AS count
    """,
    asset_id_field="asset_id",
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


_tailscale_network_flow_logging_disabled = Fact(
    id="tailscale_network_flow_logging_disabled",
    name="Tailscale tailnets with network flow logging disabled",
    description="Detects Tailscale tailnets where network flow logging is disabled.",
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)
    WHERE toLower(toString(tailnet.network_flow_logging_on)) = 'false'
    RETURN
        tailnet.id AS tailnet_id,
        tailnet.id AS asset_id,
        tailnet.id AS asset_name,
        'tailnet' AS asset_type,
        'network_flow_logging_disabled' AS issue,
        toString(tailnet.network_flow_logging_on) AS current_value
    """,
    cypher_visual_query="""
    MATCH (tailnet:TailscaleTailnet)
    WHERE toLower(toString(tailnet.network_flow_logging_on)) = 'false'
    RETURN tailnet
    """,
    cypher_count_query="""
    MATCH (tailnet:TailscaleTailnet)
    RETURN COUNT(tailnet) AS count
    """,
    asset_id_field="asset_id",
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


_tailscale_device_auto_updates_disabled = Fact(
    id="tailscale_device_auto_updates_disabled",
    name="Tailscale tailnets with device auto-updates disabled",
    description="Detects Tailscale tailnets where device auto-updates are disabled.",
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)
    WHERE toLower(toString(tailnet.devices_auto_updates_on)) = 'false'
    RETURN
        tailnet.id AS tailnet_id,
        tailnet.id AS asset_id,
        tailnet.id AS asset_name,
        'tailnet' AS asset_type,
        'device_auto_updates_disabled' AS issue,
        toString(tailnet.devices_auto_updates_on) AS current_value
    """,
    cypher_visual_query="""
    MATCH (tailnet:TailscaleTailnet)
    WHERE toLower(toString(tailnet.devices_auto_updates_on)) = 'false'
    RETURN tailnet
    """,
    cypher_count_query="""
    MATCH (tailnet:TailscaleTailnet)
    RETURN COUNT(tailnet) AS count
    """,
    asset_id_field="asset_id",
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


_tailscale_device_key_expiry_disabled = Fact(
    id="tailscale_device_key_expiry_disabled",
    name="Tailscale devices with key expiry disabled",
    description="Detects Tailscale devices where key expiry is disabled.",
    cypher_query="""
    MATCH (tailnet:TailscaleTailnet)-[:RESOURCE]->(device:TailscaleDevice)
    WHERE toLower(toString(device.key_expiry_disabled)) = 'true'
    RETURN
        tailnet.id AS tailnet_id,
        device.id AS asset_id,
        coalesce(device.hostname, device.name, device.id) AS asset_name,
        'device' AS asset_type,
        'device_key_expiry_disabled' AS issue,
        toString(device.key_expiry_disabled) AS current_value
    """,
    cypher_visual_query="""
    MATCH p=(tailnet:TailscaleTailnet)-[:RESOURCE]->(device:TailscaleDevice)
    WHERE toLower(toString(device.key_expiry_disabled)) = 'true'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (device:TailscaleDevice)
    RETURN COUNT(device) AS count
    """,
    asset_id_field="asset_id",
    module=Module.TAILSCALE,
    maturity=Maturity.EXPERIMENTAL,
)


tailscale_tailnet_approval_disabled = Rule(
    id="tailscale_tailnet_approval_disabled",
    name="Tailscale Tailnet Approval Disabled",
    description=(
        "Detects Tailscale tailnet settings that allow new users or devices "
        "without explicit approval."
    ),
    output_model=TailscaleSecurityConfigurationGapOutput,
    facts=(
        _tailscale_device_approval_disabled,
        _tailscale_user_approval_disabled,
    ),
    tags=("network", "device", "compliance", "stride:spoofing"),
    version="0.1.0",
    frameworks=(iso27001_annex_a("5.15"),),
)


tailscale_network_flow_logging_disabled = Rule(
    id="tailscale_network_flow_logging_disabled",
    name="Tailscale Network Flow Logging Disabled",
    description="Detects Tailscale tailnets where network flow logging is disabled.",
    output_model=TailscaleSecurityConfigurationGapOutput,
    facts=(_tailscale_network_flow_logging_disabled,),
    tags=("network", "logging", "compliance"),
    version="0.1.0",
    frameworks=(iso27001_annex_a("8.15"),),
)


tailscale_device_auto_updates_disabled = Rule(
    id="tailscale_device_auto_updates_disabled",
    name="Tailscale Device Auto-Updates Disabled",
    description="Detects Tailscale tailnets where device auto-updates are disabled.",
    output_model=TailscaleSecurityConfigurationGapOutput,
    facts=(_tailscale_device_auto_updates_disabled,),
    tags=("device", "patching", "compliance"),
    version="0.1.0",
    frameworks=(iso27001_annex_a("8.8"),),
)


tailscale_device_key_expiry_disabled = Rule(
    id="tailscale_device_key_expiry_disabled",
    name="Tailscale Device Key Expiry Disabled",
    description="Detects Tailscale devices where key expiry is disabled.",
    output_model=TailscaleSecurityConfigurationGapOutput,
    facts=(_tailscale_device_key_expiry_disabled,),
    tags=("device", "authentication", "compliance", "stride:spoofing"),
    version="0.1.0",
    frameworks=(iso27001_annex_a("5.17"),),
)
