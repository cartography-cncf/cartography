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
class DuoWebAuthnCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('webauthnkey')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    admin: PropertyRef = PropertyRef('admin')
    credential_name: PropertyRef = PropertyRef('credential_name', extra_index=True)
    date_added: PropertyRef = PropertyRef('date_added')
    label: PropertyRef = PropertyRef('label')
    webauthnkey: PropertyRef = PropertyRef('webauthnkey', extra_index=True)


@dataclass(frozen=True)
class DuoWebAuthnCredentialToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoWebAuthnCredentialToDuoApiHostRel(CartographyRelSchema):
    target_node_label: str = 'DuoApiHost'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('DUO_API_HOSTNAME', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoWebAuthnCredentialToDuoApiHostRelProperties = DuoWebAuthnCredentialToDuoApiHostRelProperties()


class DuoWebAuthnCredentialToDuoUserProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class DuoWebAuthnCredentialToDuoUserRel(CartographyRelSchema):
    target_node_label: str = 'DuoUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'user_id': PropertyRef('user_id')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DUO_WEB_AUTHN_CREDENTIAL"
    properties: DuoWebAuthnCredentialToDuoUserProperties = DuoWebAuthnCredentialToDuoUserProperties()


@dataclass(frozen=True)
class DuoWebAuthnCredentialSchema(CartographyNodeSchema):
    label: str = 'DuoWebAuthnCredential'
    properties: DuoWebAuthnCredentialNodeProperties = DuoWebAuthnCredentialNodeProperties()
    sub_resource_relationship: DuoWebAuthnCredentialToDuoApiHostRel = DuoWebAuthnCredentialToDuoApiHostRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DuoWebAuthnCredentialToDuoUserRel(),
        ],
    )
