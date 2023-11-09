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
class DuoPhoneNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('phone_id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    activated: PropertyRef = PropertyRef('activated')
    capabilities: PropertyRef = PropertyRef('capabilities')
    encrypted: PropertyRef = PropertyRef('encrypted')
    extension: PropertyRef = PropertyRef('extension')
    fingerprint: PropertyRef = PropertyRef('fingerprint')
    last_seen: PropertyRef = PropertyRef('last_seen')
    model: PropertyRef = PropertyRef('model')
    name: PropertyRef = PropertyRef('name')
    phone_id: PropertyRef = PropertyRef('phone_id', extra_index=True)
    platform: PropertyRef = PropertyRef('platform')
    postdelay: PropertyRef = PropertyRef('postdelay')
    predelay: PropertyRef = PropertyRef('predelay')
    screenlock: PropertyRef = PropertyRef('screenlock')
    sms_passcodes_sent: PropertyRef = PropertyRef('sms_passcodes_sent')
    tampered: PropertyRef = PropertyRef('tampered')
    type: PropertyRef = PropertyRef('type')


@dataclass(frozen=True)
class DuoPhoneToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoPhoneToDuoApiHostRel(CartographyRelSchema):
    target_node_label: str = 'DuoApiHost'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DUO_API_HOSTNAME', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoPhoneToDuoApiHostRelProperties = DuoPhoneToDuoApiHostRelProperties()


class DuoPhoneToDuoUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoPhoneToDuoUserRel(CartographyRelSchema):
    target_node_label: str = 'DuoUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'user_id': PropertyRef('user_id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DUO_PHONE"
    properties: DuoPhoneToDuoUserProperties = DuoPhoneToDuoUserProperties()


@dataclass(frozen=True)
class DuoPhoneSchema(CartographyNodeSchema):
    label: str = 'DuoPhone'
    properties: DuoPhoneNodeProperties = DuoPhoneNodeProperties()
    sub_resource_relationship: DuoPhoneToDuoApiHostRel = DuoPhoneToDuoApiHostRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DuoPhoneToDuoUserRel(),
        ],
    )
