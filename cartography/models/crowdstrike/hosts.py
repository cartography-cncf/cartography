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
class CrowdstrikeHostNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("device_id", description="CrowdStrike device ID.")
    cid: PropertyRef = PropertyRef("cid", description="CrowdStrike customer ID.")
    email: PropertyRef = PropertyRef(
        "email",
        extra_index=True,
        description="Email address associated with the host.",
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id",
        extra_index=True,
        description="Cloud provider instance ID associated with the host.",
    )
    serial_number: PropertyRef = PropertyRef(
        "serial_number",
        extra_index=True,
        description="Hardware serial number reported for the host.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Containment status of the host.",
    )
    hostname: PropertyRef = PropertyRef(
        "hostname",
        extra_index=True,
        description="Host name reported to CrowdStrike.",
    )
    machine_domain: PropertyRef = PropertyRef(
        "machine_domain",
        description="Directory domain to which the host belongs.",
    )
    crowdstrike_first_seen: PropertyRef = PropertyRef(
        "first_seen",
        description="Timestamp of the host's first connection to CrowdStrike Falcon.",
    )
    crowdstrike_last_seen: PropertyRef = PropertyRef(
        "last_seen",
        description="Timestamp of the host's most recent connection to Falcon.",
    )
    local_ip: PropertyRef = PropertyRef(
        "local_ip",
        description="Local IP address of the host.",
    )
    external_ip: PropertyRef = PropertyRef(
        "external_ip",
        description="External IP address observed by CrowdStrike.",
    )
    cpu_signature: PropertyRef = PropertyRef(
        "cpu_signature",
        description="CPU signature reported by the host.",
    )
    bios_manufacturer: PropertyRef = PropertyRef(
        "bios_manufacturer",
        description="BIOS manufacturer.",
    )
    bios_version: PropertyRef = PropertyRef(
        "bios_version",
        description="BIOS version.",
    )
    mac_address: PropertyRef = PropertyRef(
        "mac_address",
        description="MAC address of the host.",
    )
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Operating system version.",
    )
    os_build: PropertyRef = PropertyRef(
        "os_build",
        description="Operating system build.",
    )
    platform_id: PropertyRef = PropertyRef(
        "platform_id",
        description="CrowdStrike platform identifier.",
    )
    platform_name: PropertyRef = PropertyRef(
        "platform_name",
        description="Operating system platform name.",
    )
    service_provider: PropertyRef = PropertyRef(
        "service_provider",
        description="Service provider associated with the host.",
    )
    service_provider_account_id: PropertyRef = PropertyRef(
        "service_provider_account_id",
        description="Service provider account ID associated with the host.",
    )
    agent_version: PropertyRef = PropertyRef(
        "agent_version",
        description="Version of the CrowdStrike agent.",
    )
    system_manufacturer: PropertyRef = PropertyRef(
        "system_manufacturer",
        description="System manufacturer.",
    )
    system_product_name: PropertyRef = PropertyRef(
        "system_product_name",
        description="System product name.",
    )
    product_type: PropertyRef = PropertyRef(
        "product_type",
        description="CrowdStrike product type identifier.",
    )
    product_type_desc: PropertyRef = PropertyRef(
        "product_type_desc",
        description="Human-readable CrowdStrike product type.",
    )
    provision_status: PropertyRef = PropertyRef(
        "provision_status",
        description="Provisioning status of the host.",
    )
    reduced_functionality_mode: PropertyRef = PropertyRef(
        "reduced_functionality_mode",
        description="Reduced functionality mode status.",
    )
    kernel_version: PropertyRef = PropertyRef(
        "kernel_version",
        description="Host operating system kernel version.",
    )
    major_version: PropertyRef = PropertyRef(
        "major_version",
        description="Major operating system version.",
    )
    minor_version: PropertyRef = PropertyRef(
        "minor_version",
        description="Minor operating system version.",
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Grouping tags assigned to the host.",
    )
    modified_timestamp: PropertyRef = PropertyRef(
        "modified_timestamp",
        description="Timestamp when CrowdStrike last modified the host record.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
class CrowdstrikeHostToCrowdstrikeTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
class CrowdstrikeHostToCrowdstrikeTenantRel(CartographyRelSchema):
    """The CrowdStrike tenant contains this host as a managed resource."""

    target_node_label: str = "CrowdstrikeTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CrowdstrikeHostToCrowdstrikeTenantRelProperties = (
        CrowdstrikeHostToCrowdstrikeTenantRelProperties()
    )


@dataclass(frozen=True)
class CrowdstrikeHostSchema(CartographyNodeSchema):
    """An endpoint device observed by CrowdStrike Falcon."""

    label: str = "CrowdstrikeHost"
    properties: CrowdstrikeHostNodeProperties = CrowdstrikeHostNodeProperties()
    sub_resource_relationship: CrowdstrikeHostToCrowdstrikeTenantRel = (
        CrowdstrikeHostToCrowdstrikeTenantRel()
    )
