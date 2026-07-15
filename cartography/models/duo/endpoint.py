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
class DuoEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("epkey", description="Duo endpoint key.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    browsers: PropertyRef = PropertyRef(
        "browsers", description="Detected browser information."
    )
    computer_sid: PropertyRef = PropertyRef(
        "computer_sid", description="Windows machine security identifier."
    )
    cpu_id: PropertyRef = PropertyRef("cpu_id", description="Windows CPU ID.")
    device_id: PropertyRef = PropertyRef(
        "device_id", description="Custom Meraki-managed device identifier."
    )
    device_identifier: PropertyRef = PropertyRef(
        "device_identifier", description="Deprecated unique device attribute value."
    )
    device_identifier_type: PropertyRef = PropertyRef(
        "device_identifier_type",
        description="Deprecated device attribute used to identify the endpoint.",
    )
    device_name: PropertyRef = PropertyRef(
        "device_name", extra_index=True, description="Endpoint hostname."
    )
    device_udid: PropertyRef = PropertyRef(
        "device_udid", description="Managed iOS unique device identifier."
    )
    device_username: PropertyRef = PropertyRef(
        "device_username", description="Associated management-system username."
    )
    device_username_type: PropertyRef = PropertyRef(
        "device_username_type",
        description="Management-system attribute used to identify the user.",
    )
    disk_encryption_status: PropertyRef = PropertyRef(
        "disk_encryption_status", description="Detected disk encryption status."
    )
    domain_sid: PropertyRef = PropertyRef(
        "domain_sid", description="Active Directory domain security identifier."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Associated user email address."
    )
    epkey: PropertyRef = PropertyRef(
        "epkey", extra_index=True, description="Duo endpoint key."
    )
    firewall_status: PropertyRef = PropertyRef(
        "firewall_status", description="Detected local firewall status."
    )
    hardware_uuid: PropertyRef = PropertyRef(
        "hardware_uuid", description="Mac hardware UUID."
    )
    health_app_client_version: PropertyRef = PropertyRef(
        "health_app_client_version", description="Duo Device Health app version."
    )
    health_data_last_collected: PropertyRef = PropertyRef(
        "health_data_last_collected",
        description="Timestamp of the last device health check.",
    )
    last_updated: PropertyRef = PropertyRef(
        "last_updated", description="Timestamp when the endpoint last accessed Duo."
    )
    machine_guid: PropertyRef = PropertyRef(
        "machine_guid", description="Windows machine GUID."
    )
    model: PropertyRef = PropertyRef("model", description="Endpoint device model.")
    os_build: PropertyRef = PropertyRef(
        "os_build", description="Operating system build number."
    )
    os_family: PropertyRef = PropertyRef(
        "os_family", description="Operating system platform."
    )
    os_version: PropertyRef = PropertyRef(
        "os_version", description="Operating system version."
    )
    password_status: PropertyRef = PropertyRef(
        "password_status", description="Detected local administrator password status."
    )
    security_agents: PropertyRef = PropertyRef(
        "security_agents", description="Detected security agent information."
    )
    trusted_endpoint: PropertyRef = PropertyRef(
        "trusted_endpoint", description="Whether Duo manages the endpoint."
    )
    type: PropertyRef = PropertyRef("type", description="Endpoint device class.")
    username: PropertyRef = PropertyRef(
        "username", extra_index=True, description="Associated Duo username."
    )


@dataclass(frozen=True)
class DuoEndpointToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoEndpointToDuoApiHostRel(CartographyRelSchema):
    """The Duo API host contains the endpoint."""

    target_node_label: str = "DuoApiHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DUO_API_HOSTNAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoEndpointToDuoApiHostRelProperties = (
        DuoEndpointToDuoApiHostRelProperties()
    )


class DuoEndpointToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoEndpointToDuoUserRel(CartographyRelSchema):
    """The Duo user has the endpoint, matched by email address."""

    target_node_label: str = "DuoUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DUO_ENDPOINT"
    properties: DuoEndpointToDuoUserRelProperties = DuoEndpointToDuoUserRelProperties()


@dataclass(frozen=True)
class DuoEndpointSchema(CartographyNodeSchema):
    """An endpoint observed by Duo."""

    label: str = "DuoEndpoint"
    properties: DuoEndpointNodeProperties = DuoEndpointNodeProperties()
    sub_resource_relationship: DuoEndpointToDuoApiHostRel = DuoEndpointToDuoApiHostRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DuoEndpointToDuoUserRel(),
        ],
    )
