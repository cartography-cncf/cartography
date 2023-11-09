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
    id: PropertyRef = PropertyRef('epkey')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    browsers: PropertyRef = PropertyRef('browsers')
    computer_sid: PropertyRef = PropertyRef('computer_sid')
    cpu_id: PropertyRef = PropertyRef('cpu_id')
    device_id: PropertyRef = PropertyRef('device_id')
    device_identifier: PropertyRef = PropertyRef('device_identifier')
    device_identifier_type: PropertyRef = PropertyRef('device_identifier_type')
    device_name: PropertyRef = PropertyRef('device_name')
    device_udid: PropertyRef = PropertyRef('device_udid')
    device_username: PropertyRef = PropertyRef('device_username')
    device_username_type: PropertyRef = PropertyRef('device_username_type')
    disk_encryption_status: PropertyRef = PropertyRef('disk_encryption_status')
    domain_sid: PropertyRef = PropertyRef('domain_sid')
    email: PropertyRef = PropertyRef('email', extra_index=True)
    epkey: PropertyRef = PropertyRef('epkey', extra_index=True)
    firewall_status: PropertyRef = PropertyRef('firewall_status')
    hardware_uuid: PropertyRef = PropertyRef('hardware_uuid')
    health_app_client_version: PropertyRef = PropertyRef('health_app_client_version')
    health_data_last_collected: PropertyRef = PropertyRef('health_data_last_collected')
    last_updated: PropertyRef = PropertyRef('last_updated')
    machine_guid: PropertyRef = PropertyRef('machine_guid')
    model: PropertyRef = PropertyRef('model')
    os_build: PropertyRef = PropertyRef('os_build')
    os_family: PropertyRef = PropertyRef('os_family')
    os_version: PropertyRef = PropertyRef('os_version')
    password_status: PropertyRef = PropertyRef('password_status')
    security_agents: PropertyRef = PropertyRef('security_agents')
    trusted_endpoint: PropertyRef = PropertyRef('trusted_endpoint')
    type: PropertyRef = PropertyRef('type')
    username: PropertyRef = PropertyRef('username', extra_index=True)


@dataclass(frozen=True)
class DuoEndpointToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoEndpointToDuoApiHostRel(CartographyRelSchema):
    target_node_label: str = 'DuoApiHost'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DUO_API_HOSTNAME', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoEndpointToDuoApiHostRelProperties = DuoEndpointToDuoApiHostRelProperties()


class DuoEndpointToDuoUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoEndpointToDuoUserRel(CartographyRelSchema):
    target_node_label: str = 'DuoUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'email': PropertyRef('email')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DUO_ENDPOINT"
    properties: DuoEndpointToDuoUserProperties = DuoEndpointToDuoUserProperties()


@dataclass(frozen=True)
class DuoEndpointSchema(CartographyNodeSchema):
    label: str = 'DuoEndpoint'
    properties: DuoEndpointNodeProperties = DuoEndpointNodeProperties()
    sub_resource_relationship: DuoEndpointToDuoApiHostRel = DuoEndpointToDuoApiHostRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DuoEndpointToDuoUserRel(),
        ],
    )
