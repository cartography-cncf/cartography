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
class HuntressAgentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Huntress-unique identifier for the agent.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Identity
    hostname: PropertyRef = PropertyRef(
        "hostname",
        extra_index=True,
        description="Hostname of the host machine the agent is installed on.",
    )
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        extra_index=True,
        description="Serial number of the host machine as reported to the operating system.",
    )
    domain_name: PropertyRef = PropertyRef(
        "domain_name",
        description="Domain the host machine belongs to.",
    )
    external_ip: PropertyRef = PropertyRef(
        "external_ip",
        extra_index=True,
        description="External IP the host machine was last seen from.",
    )
    ipv4_address: PropertyRef = PropertyRef(
        "ipv4_address",
        description="Primary internal IPv4 address of the host machine.",
    )
    ipv4_addresses: PropertyRef = PropertyRef(
        "ipv4_addresses",
        description="Every internal IPv4 address the host reports, one per network interface.",
    )
    mac_addresses: PropertyRef = PropertyRef(
        "mac_addresses",
        description="MAC addresses of the host machine's network interfaces.",
    )

    # Hardware and operating system
    platform: PropertyRef = PropertyRef(
        "platform",
        description="Platform of the host machine: `windows`, `darwin` or `linux`.",
    )
    os: PropertyRef = PropertyRef(
        "os",
        description="Operating system of the host machine.",
    )
    os_build_version: PropertyRef = PropertyRef(
        "os_build_version",
        description="Operating system build number of the host machine.",
    )
    os_major: PropertyRef = PropertyRef(
        "os_major",
        description="Major operating system version of the host machine.",
    )
    os_minor: PropertyRef = PropertyRef(
        "os_minor",
        description="Minor operating system version of the host machine.",
    )
    os_patch: PropertyRef = PropertyRef(
        "os_patch",
        description="Patch version of the operating system update installed on the host machine.",
    )
    arch: PropertyRef = PropertyRef(
        "arch",
        description="Architecture of the host machine.",
    )
    service_pack_major: PropertyRef = PropertyRef(
        "service_pack_major",
        description="Major version of the Windows service pack installed on the host machine.",
    )
    service_pack_minor: PropertyRef = PropertyRef(
        "service_pack_minor",
        description="Minor version of the Windows service pack installed on the host machine.",
    )
    win_build_number: PropertyRef = PropertyRef(
        "win_build_number",
        description="Windows build number of the host machine.",
    )

    # Agent software
    version: PropertyRef = PropertyRef(
        "version",
        description="Version of the Huntress agent installed on the host machine.",
    )
    edr_version: PropertyRef = PropertyRef(
        "edr_version",
        description="Version of the Huntress EDR software installed on the host machine.",
    )

    # Security posture
    firewall_status: PropertyRef = PropertyRef(
        "firewall_status",
        description=(
            "Agent firewall status: `Disabled`, `Enabled`, `Pending Isolation`, "
            "`Isolated` or `Pending Release`."
        ),
    )
    defender_status: PropertyRef = PropertyRef(
        "defender_status",
        description="Managed Antivirus status of Microsoft Defender AV.",
    )
    defender_substatus: PropertyRef = PropertyRef(
        "defender_substatus",
        description="Managed Antivirus sub-status of Microsoft Defender AV.",
    )
    defender_policy_status: PropertyRef = PropertyRef(
        "defender_policy_status",
        description="Managed Antivirus policy status of Microsoft Defender AV.",
    )
    tamper_protection_configured: PropertyRef = PropertyRef(
        "tamper_protection_configured",
        description="Desired EDR tamper protection state for the agent.",
    )
    tamper_protection_actual: PropertyRef = PropertyRef(
        "tamper_protection_actual",
        description=(
            "Tamper protection state most recently reported by the host, which may lag "
            "the desired state."
        ),
    )

    # Lifecycle
    tags: PropertyRef = PropertyRef(
        "tags",
        description="User classifications applied to the host machine.",
    )
    last_callback_at: PropertyRef = PropertyRef(
        "last_callback_at",
        description="Timestamp Huntress last reached the host machine.",
    )
    last_survey_at: PropertyRef = PropertyRef(
        "last_survey_at",
        description="Timestamp Huntress last received a survey from the host machine.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when the agent was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Timestamp when the agent was last updated.",
    )


@dataclass(frozen=True)
class HuntressAgentToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:HuntressAccount)-[:RESOURCE]->(:HuntressAgent)
@dataclass(frozen=True)
class HuntressAgentToAccountRel(CartographyRelSchema):
    """Links a Huntress account to one of its agents."""

    target_node_label: str = "HuntressAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: HuntressAgentToAccountRelProperties = (
        HuntressAgentToAccountRelProperties()
    )


@dataclass(frozen=True)
class HuntressAgentToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:HuntressAgent)-[:MEMBER_OF]->(:HuntressOrganization)
@dataclass(frozen=True)
class HuntressAgentToOrganizationRel(CartographyRelSchema):
    """Links a Huntress agent to the organization it protects."""

    target_node_label: str = "HuntressOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: HuntressAgentToOrganizationRelProperties = (
        HuntressAgentToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class HuntressAgentSchema(CartographyNodeSchema):
    """A Huntress agent installed on an endpoint."""

    label: str = "HuntressAgent"
    properties: HuntressAgentNodeProperties = HuntressAgentNodeProperties()
    sub_resource_relationship: HuntressAgentToAccountRel = HuntressAgentToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [HuntressAgentToOrganizationRel()],
    )
