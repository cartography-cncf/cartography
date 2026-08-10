"""Snowflake programmatic access token (PAT) nodes.

A PAT is a long-lived bearer secret that authenticates as a Snowflake user, so it
is an ``APIKey`` in Cartography's ontology and the credential's blast radius is
whatever its owning user can reach. Only the token's metadata is recorded: the
secret itself is shown once at creation and is never read back.

There is no REST endpoint for tokens, so they come from
``SHOW USER PROGRAMMATIC ACCESS TOKENS``.

Ownership is declared twice, once per possible owner label, because a Snowflake
identity is modelled either as ``SnowflakeUser`` or as ``SnowflakeServiceUser``
and the ontology constraint that forces ``OWNED_BY`` is checked per concrete
label pair. Routing both through the shared ``SnowflakePrincipal`` label would
make the check resolve to that Snowflake-only label and silently pass.
"""

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
from cartography.models.ontology.labels import API_KEY


@dataclass(frozen=True)
class SnowflakeProgrammaticAccessTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the access token."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The token name."
    )
    user_name: PropertyRef = PropertyRef(
        "user_name",
        extra_index=True,
        description="Name of the Snowflake user the token authenticates as.",
    )
    role_restriction: PropertyRef = PropertyRef(
        "role_restriction",
        description=(
            "The single role the token is limited to. Null when the token is "
            "unrestricted, in which case it can activate every role its user holds."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Token status; only an ACTIVE token can authenticate.",
    )
    mins_to_bypass_required_network_policy: PropertyRef = PropertyRef(
        "mins_to_bypass_required_network_policy",
        description=(
            "Minutes remaining in which this token may be used from outside the "
            "network policy that would otherwise gate it. A non-null value is an "
            "active exemption from network restrictions, so the token can be "
            "replayed from anywhere on the internet until it lapses."
        ),
    )
    rotated_to: PropertyRef = PropertyRef(
        "rotated_to",
        description=(
            "Name of the token this one was rotated to. A rotated token stays usable "
            "for its grace period, so both it and its successor are live secrets."
        ),
    )
    comment: PropertyRef = PropertyRef("comment", description="Token comment.")
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Name of the user that created the token."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at", description="When the token stops being accepted."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the token was created."
    )


@dataclass(frozen=True)
class SnowflakeAccessTokenToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeProgrammaticAccessToken)
class SnowflakeAccessTokenToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the access token as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeAccessTokenToAccountRelProperties = (
        SnowflakeAccessTokenToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAccessTokenToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeProgrammaticAccessToken)-[:OWNED_BY]->(:SnowflakeUser)
class SnowflakeAccessTokenToUserRel(CartographyRelSchema):
    """The access token authenticates as this human Snowflake user."""

    target_node_label: str = "SnowflakeUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: SnowflakeAccessTokenToUserRelProperties = (
        SnowflakeAccessTokenToUserRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAccessTokenToServiceUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeProgrammaticAccessToken)-[:OWNED_BY]->(:SnowflakeServiceUser)
class SnowflakeAccessTokenToServiceUserRel(CartographyRelSchema):
    """The access token authenticates as this Snowflake service user."""

    target_node_label: str = "SnowflakeServiceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: SnowflakeAccessTokenToServiceUserRelProperties = (
        SnowflakeAccessTokenToServiceUserRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAccessTokenToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeProgrammaticAccessToken)-[:RESTRICTED_TO]->(:SnowflakeRole)
class SnowflakeAccessTokenToRoleRel(CartographyRelSchema):
    """The access token may only activate this role, whatever else its user holds.

    Absent when the token is unrestricted, which means it inherits every role
    granted to its user.
    """

    target_node_label: str = "SnowflakeRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_restriction_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESTRICTED_TO"
    properties: SnowflakeAccessTokenToRoleRelProperties = (
        SnowflakeAccessTokenToRoleRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeProgrammaticAccessTokenSchema(CartographyNodeSchema):
    """Represents a Snowflake programmatic access token: a bearer secret that authenticates as a user."""

    label: str = "SnowflakeProgrammaticAccessToken"
    properties: SnowflakeProgrammaticAccessTokenNodeProperties = (
        SnowflakeProgrammaticAccessTokenNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([API_KEY])
    sub_resource_relationship: SnowflakeAccessTokenToAccountRel = (
        SnowflakeAccessTokenToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeAccessTokenToUserRel(),
            SnowflakeAccessTokenToServiceUserRel(),
            SnowflakeAccessTokenToRoleRel(),
        ],
    )
