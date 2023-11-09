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
class DuoGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('group_id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    desc: PropertyRef = PropertyRef('desc')
    group_id: PropertyRef = PropertyRef('group_id', extra_index=True)
    mobile_otp_enabled: PropertyRef = PropertyRef('mobile_otp_enabled')
    name: PropertyRef = PropertyRef('name', extra_index=True)
    push_enabled: PropertyRef = PropertyRef('push_enabled')
    sms_enabled: PropertyRef = PropertyRef('sms_enabled')
    status: PropertyRef = PropertyRef('status')
    voice_enabled: PropertyRef = PropertyRef('voice_enabled')


@dataclass(frozen=True)
class DuoGroupToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoGroupToDuoApiHostRel(CartographyRelSchema):
    target_node_label: str = 'DuoApiHost'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DUO_API_HOSTNAME', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoGroupToDuoApiHostRelProperties = DuoGroupToDuoApiHostRelProperties()


@dataclass(frozen=True)
class DuoGroupSchema(CartographyNodeSchema):
    label: str = 'DuoGroup'
    properties: DuoGroupNodeProperties = DuoGroupNodeProperties()
    sub_resource_relationship: DuoGroupToDuoApiHostRel = DuoGroupToDuoApiHostRel()
