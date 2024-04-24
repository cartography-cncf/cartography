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
class KandjiDeviceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)

    device_id: PropertyRef = PropertyRef('device_id')
    device_name: PropertyRef = PropertyRef('device_name')
    last_check_in: PropertyRef = PropertyRef('last_check_in')
    model: PropertyRef = PropertyRef('model')
    os_version: PropertyRef = PropertyRef('os_version')
    platform: PropertyRef = PropertyRef('platform')
    serial_number: PropertyRef = PropertyRef('serial_number', extra_index=True)


@dataclass(frozen=True)
class KandjiTenantToKandjiDeviceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
# (:KandjiDevice)-[:ENROLLED_TO]->(:KandjiTenant)
class KandjiTenantToKandjiDeviceRel(CartographyRelSchema):
    target_node_label: str = 'KandjiTenant'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('TENANT_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENROLLED_TO"
    properties: KandjiTenantToKandjiDeviceRelProperties = KandjiTenantToKandjiDeviceRelProperties()


@dataclass(frozen=True)
class KandjiDeviceSchema(CartographyNodeSchema):
    label: str = 'KandjiDevice'  # The label of the node
    properties: KandjiDeviceNodeProperties = KandjiDeviceNodeProperties()  # An object representing all properties
    sub_resource_relationship: KandjiTenantToKandjiDeviceRel = KandjiTenantToKandjiDeviceRel()
