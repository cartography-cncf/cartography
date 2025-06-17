from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class CrowdstrikeHostNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("device_id")
    cid: PropertyRef = PropertyRef("cid")
    instance_id: PropertyRef = PropertyRef("instance_id", extra_index=True)
    serial_number: PropertyRef = PropertyRef("serial_number", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    hostname: PropertyRef = PropertyRef("hostname", extra_index=True)
    machine_domain: PropertyRef = PropertyRef("machine_domain")
    crowdstrike_first_seen: PropertyRef = PropertyRef("first_seen")
    crowdstrike_last_seen: PropertyRef = PropertyRef("last_seen")
    local_ip: PropertyRef = PropertyRef("local_ip")
    external_ip: PropertyRef = PropertyRef("external_ip")
    cpu_signature: PropertyRef = PropertyRef("cpu_signature")
    bios_manufacturer: PropertyRef = PropertyRef("bios_manufacturer")
    bios_version: PropertyRef = PropertyRef("bios_version")
    mac_address: PropertyRef = PropertyRef("mac_address")
    os_version: PropertyRef = PropertyRef("os_version")
    os_build: PropertyRef = PropertyRef("os_build")
    platform_id: PropertyRef = PropertyRef("platform_id")
    platform_name: PropertyRef = PropertyRef("platform_name")
    service_provider: PropertyRef = PropertyRef("service_provider")
    service_provider_account_id: PropertyRef = PropertyRef(
        "service_provider_account_id"
    )
    agent_version: PropertyRef = PropertyRef("agent_version")
    system_manufacturer: PropertyRef = PropertyRef("system_manufacturer")
    system_product_name: PropertyRef = PropertyRef("system_product_name")
    product_type: PropertyRef = PropertyRef("product_type")
    product_type_desc: PropertyRef = PropertyRef("product_type_desc")
    provision_status: PropertyRef = PropertyRef("provision_status")
    reduced_functionality_mode: PropertyRef = PropertyRef("reduced_functionality_mode")
    kernel_version: PropertyRef = PropertyRef("kernel_version")
    major_version: PropertyRef = PropertyRef("major_version")
    minor_version: PropertyRef = PropertyRef("minor_version")
    tags: PropertyRef = PropertyRef("tags")
    modified_timestamp: PropertyRef = PropertyRef("modified_timestamp")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CrowdstrikeHostSchema(CartographyNodeSchema):
    label: str = "CrowdstrikeHost"
    properties: CrowdstrikeHostNodeProperties = CrowdstrikeHostNodeProperties()
