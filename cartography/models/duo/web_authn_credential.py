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
    id: PropertyRef = PropertyRef(
        "webauthnkey", description="WebAuthn credential registration ID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    admin: PropertyRef = PropertyRef(
        "admin", description="Administrator associated with the credential."
    )
    credential_name: PropertyRef = PropertyRef(
        "credential_name",
        extra_index=True,
        description="WebAuthn credential label.",
    )
    date_added: PropertyRef = PropertyRef(
        "date_added", description="Credential registration date."
    )
    label: PropertyRef = PropertyRef("label", description="WebAuthn credential type.")
    webauthnkey: PropertyRef = PropertyRef(
        "webauthnkey",
        extra_index=True,
        description="WebAuthn credential registration ID.",
    )


@dataclass(frozen=True)
class DuoWebAuthnCredentialToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoWebAuthnCredentialToDuoApiHostRel(CartographyRelSchema):
    """The Duo API host contains the WebAuthn credential."""

    target_node_label: str = "DuoApiHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DUO_API_HOSTNAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoWebAuthnCredentialToDuoApiHostRelProperties = (
        DuoWebAuthnCredentialToDuoApiHostRelProperties()
    )


class DuoWebAuthnCredentialToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoWebAuthnCredentialToDuoUserRel(CartographyRelSchema):
    """The Duo user has the WebAuthn credential."""

    target_node_label: str = "DuoUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"user_id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DUO_WEB_AUTHN_CREDENTIAL"
    properties: DuoWebAuthnCredentialToDuoUserRelProperties = (
        DuoWebAuthnCredentialToDuoUserRelProperties()
    )


@dataclass(frozen=True)
class DuoWebAuthnCredentialSchema(CartographyNodeSchema):
    """A WebAuthn credential registered in Duo."""

    label: str = "DuoWebAuthnCredential"
    properties: DuoWebAuthnCredentialNodeProperties = (
        DuoWebAuthnCredentialNodeProperties()
    )
    sub_resource_relationship: DuoWebAuthnCredentialToDuoApiHostRel = (
        DuoWebAuthnCredentialToDuoApiHostRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DuoWebAuthnCredentialToDuoUserRel(),
        ],
    )
