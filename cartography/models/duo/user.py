from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DuoUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("user_id", description="Duo user ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    alias1: PropertyRef = PropertyRef("alias1", description="First username alias.")
    alias2: PropertyRef = PropertyRef("alias2", description="Second username alias.")
    alias3: PropertyRef = PropertyRef("alias3", description="Third username alias.")
    alias4: PropertyRef = PropertyRef("alias4", description="Fourth username alias.")
    aliases: PropertyRef = PropertyRef(
        "aliases", description="Map of username aliases."
    )
    created: PropertyRef = PropertyRef(
        "created", description="User creation timestamp."
    )
    desktoptokens: PropertyRef = PropertyRef(
        "desktoptokens", description="Desktop tokens available to the user."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    firstname: PropertyRef = PropertyRef("firstname", description="User given name.")
    is_enrolled: PropertyRef = PropertyRef(
        "is_enrolled", description="Whether the user has an authentication method."
    )
    last_directory_sync: PropertyRef = PropertyRef(
        "last_directory_sync", description="Timestamp of the last directory sync."
    )
    last_login: PropertyRef = PropertyRef(
        "last_login", description="Timestamp of the last login."
    )
    lastname: PropertyRef = PropertyRef("lastname", description="User surname.")
    notes: PropertyRef = PropertyRef("notes", description="Administrative user notes.")
    realname: PropertyRef = PropertyRef("realname", description="User full name.")
    status: PropertyRef = PropertyRef("status", description="User status.")
    u2ftokens: PropertyRef = PropertyRef(
        "u2ftokens", description="U2F tokens available to the user."
    )
    user_id: PropertyRef = PropertyRef(
        "user_id", extra_index=True, description="Duo user ID."
    )
    username: PropertyRef = PropertyRef(
        "username", extra_index=True, description="Duo username."
    )


@dataclass(frozen=True)
class DuoUserToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoUserToDuoApiHostRel(CartographyRelSchema):
    """The Duo API host contains the user."""

    target_node_label: str = "DuoApiHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DUO_API_HOSTNAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoUserToDuoApiHostRelProperties = DuoUserToDuoApiHostRelProperties()


class DuoWebAuthnCredentialToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoWebAuthnCredentialToDuoUserRel(CartographyRelSchema):
    """The Duo user has the WebAuthn credential."""

    target_node_label: str = "DuoWebAuthnCredential"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"webauthnkey": PropertyRef("webauthnkey")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DUO_WEB_AUTHN_CREDENTIAL"
    properties: DuoWebAuthnCredentialToDuoUserRelProperties = (
        DuoWebAuthnCredentialToDuoUserRelProperties()
    )


class DuoTokenToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoTokenToDuoUserRel(CartographyRelSchema):
    """The Duo user has the hardware token."""

    target_node_label: str = "DuoToken"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"token_id": PropertyRef("token_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DUO_TOKEN"
    properties: DuoTokenToDuoUserRelProperties = DuoTokenToDuoUserRelProperties()


class DuoPhoneToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoPhoneToDuoUserRel(CartographyRelSchema):
    """The Duo user has the phone."""

    target_node_label: str = "DuoPhone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"phone_id": PropertyRef("phone_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DUO_PHONE"
    properties: DuoPhoneToDuoUserRelProperties = DuoPhoneToDuoUserRelProperties()


class DuoEndpointToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoEndpointToDuoUserRel(CartographyRelSchema):
    """The Duo user has the endpoint, matched by email address."""

    target_node_label: str = "DuoEndpoint"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_DUO_ENDPOINT"
    properties: DuoEndpointToDuoUserRelProperties = DuoEndpointToDuoUserRelProperties()


class DuoGroupToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
# edge (DuoGroupToDuoUserMemberOfRel). Kept for backward compatibility, will be
# removed in v1.0.0.
class DuoGroupToDuoUserRel(CartographyRelSchema):
    """Deprecated compatibility edge linking a Duo user to a Duo group."""

    target_node_label: str = "DuoGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"group_id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_DUO_GROUP"
    properties: DuoGroupToDuoUserRelProperties = DuoGroupToDuoUserRelProperties()


@dataclass(frozen=True)
class DuoGroupToDuoUserMemberOfRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:MEMBER_OF]->(:UserGroup)
class DuoGroupToDuoUserMemberOfRel(CartographyRelSchema):
    """The Duo user account is a member of the Duo user group."""

    target_node_label: str = "DuoGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"group_id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: DuoGroupToDuoUserMemberOfRelProperties = (
        DuoGroupToDuoUserMemberOfRelProperties()
    )


@dataclass(frozen=True)
class DuoUserToHumanRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DuoUser)<-[:IDENTITY_DUO]-(:Human)
class DuoUserToHumanRel(CartographyRelSchema):
    """A Human has the Duo user as an identity, matched by email address."""

    target_node_label: str = "Human"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IDENTITY_DUO"
    properties: DuoUserToHumanRelProperties = DuoUserToHumanRelProperties()


@dataclass(frozen=True)
class DuoUserSchema(CartographyNodeSchema):
    """A user account in Duo."""

    label: str = "DuoUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping
    properties: DuoUserNodeProperties = DuoUserNodeProperties()
    sub_resource_relationship: DuoUserToDuoApiHostRel = DuoUserToDuoApiHostRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DuoUserToHumanRel(),
            DuoGroupToDuoUserRel(),
            DuoGroupToDuoUserMemberOfRel(),
            DuoEndpointToDuoUserRel(),
            DuoPhoneToDuoUserRel(),
            DuoTokenToDuoUserRel(),
            DuoWebAuthnCredentialToDuoUserRel(),
        ],
    )
