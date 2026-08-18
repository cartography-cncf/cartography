"""Snowflake user nodes.

``GET /api/v2/users`` returns humans and machine identities in one listing,
distinguished by ``type`` (``PERSON`` versus ``SERVICE`` / ``LEGACY_SERVICE``).
Cartography splits them into two labels rather than one label with a conditional
ontology label, because ontology mappings are keyed by node label: a single
``SnowflakeUser`` entry in both ``useraccounts`` and ``serviceaccounts`` would
project service-account fields onto humans and vice versa. This mirrors
``DatabricksUser`` versus ``DatabricksServicePrincipal``.

Both labels share one property set, since both come from the same payload.
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
from cartography.models.ontology.labels import SERVICE_ACCOUNT
from cartography.models.ontology.labels import USER_ACCOUNT
from cartography.models.snowflake.extra_labels import SNOWFLAKE_PRINCIPAL
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the user."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The user's Snowflake name."
    )
    login_name: PropertyRef = PropertyRef(
        "login_name",
        extra_index=True,
        description="The name the user authenticates with, which may differ from `name`.",
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="The user's email address."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="The user's display name."
    )
    first_name: PropertyRef = PropertyRef(
        "first_name", description="The user's first name."
    )
    last_name: PropertyRef = PropertyRef(
        "last_name", description="The user's last name."
    )
    user_type: PropertyRef = PropertyRef(
        "user_type",
        description=(
            "The Snowflake user type: PERSON for a human, SERVICE or LEGACY_SERVICE "
            "for a machine identity. SERVICE users cannot hold a password."
        ),
    )
    disabled: PropertyRef = PropertyRef(
        "disabled", description="Whether the user is disabled and cannot authenticate."
    )
    has_password: PropertyRef = PropertyRef(
        "has_password", description="Whether the user has a password set."
    )
    has_mfa: PropertyRef = PropertyRef(
        "has_mfa",
        description=(
            "Whether the user has enrolled in multi-factor authentication. Read from "
            "SQL, since the REST API does not expose it; null when unreadable."
        ),
    )
    has_rsa_public_key: PropertyRef = PropertyRef(
        "has_rsa_public_key",
        description="Whether the user has an RSA public key registered for key-pair auth.",
    )
    rsa_public_key_fp: PropertyRef = PropertyRef(
        "rsa_public_key_fp",
        description="Fingerprint of the user's primary registered RSA public key.",
    )
    rsa_public_key_2_fp: PropertyRef = PropertyRef(
        "rsa_public_key_2_fp",
        description="Fingerprint of the user's secondary registered RSA public key, used for rotation.",
    )
    must_change_password: PropertyRef = PropertyRef(
        "must_change_password",
        description="Whether the user must change their password at next login.",
    )
    days_to_expiry: PropertyRef = PropertyRef(
        "days_to_expiry", description="Days until the user account expires."
    )
    mins_to_unlock: PropertyRef = PropertyRef(
        "mins_to_unlock",
        description="Minutes until a locked-out user is unlocked.",
    )
    mins_to_bypass_mfa: PropertyRef = PropertyRef(
        "mins_to_bypass_mfa",
        description=(
            "Minutes remaining in which the user may authenticate without MFA. "
            "A non-null value means MFA is temporarily bypassed."
        ),
    )
    mins_to_bypass_network_policy: PropertyRef = PropertyRef(
        "mins_to_bypass_network_policy",
        description=(
            "Minutes remaining in which the user may authenticate from outside "
            "their network policy."
        ),
    )
    network_policy_name: PropertyRef = PropertyRef(
        "network_policy_name",
        description="Name of the network policy attached directly to this user, if any.",
    )
    default_role: PropertyRef = PropertyRef(
        "default_role",
        description=(
            "The role the user's sessions activate by default. This is also the role "
            "Snowflake's object API endpoints run as."
        ),
    )
    default_secondary_roles: PropertyRef = PropertyRef(
        "default_secondary_roles",
        description=(
            "Secondary roles activated by default: ALL grants the union of every role "
            "granted to the user in a session."
        ),
    )
    default_warehouse: PropertyRef = PropertyRef(
        "default_warehouse", description="The user's default warehouse."
    )
    default_namespace: PropertyRef = PropertyRef(
        "default_namespace", description="The user's default database or schema."
    )
    ext_authn_duo: PropertyRef = PropertyRef(
        "ext_authn_duo", description="Whether Duo external authentication is enabled."
    )
    snowflake_lock: PropertyRef = PropertyRef(
        "snowflake_lock",
        description="Whether Snowflake has locked the account, for example after abuse detection.",
    )
    snowflake_support: PropertyRef = PropertyRef(
        "snowflake_support",
        description="Whether Snowflake Support may use this user for troubleshooting.",
    )
    comment: PropertyRef = PropertyRef("comment", description="User comment.")
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the user."
    )
    password_last_set: PropertyRef = PropertyRef(
        "password_last_set", description="When the user's password was last set."
    )
    last_successful_login: PropertyRef = PropertyRef(
        "last_successful_login",
        description="When the user last authenticated successfully.",
    )
    locked_until: PropertyRef = PropertyRef(
        "locked_until", description="When a lockout on the user expires."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at", description="When the user account expires."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the user was created."
    )


@dataclass(frozen=True)
class SnowflakeUserToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeUser)
class SnowflakeUserToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the user as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeUserToAccountRelProperties = (
        SnowflakeUserToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeUserToNetworkPolicyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeUser)-[:GOVERNED_BY]->(:SnowflakeNetworkPolicy)
class SnowflakeUserToNetworkPolicyRel(CartographyRelSchema):
    """A Snowflake user's connections are restricted by this network policy."""

    target_node_label: str = "SnowflakeNetworkPolicy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_policy_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "GOVERNED_BY"
    properties: SnowflakeUserToNetworkPolicyRelProperties = (
        SnowflakeUserToNetworkPolicyRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeUserSchema(CartographyNodeSchema):
    """Represents a human Snowflake user account."""

    label: str = "SnowflakeUser"
    properties: SnowflakeUserNodeProperties = SnowflakeUserNodeProperties()
    # A user is both a grantee (privileges can be granted to it) and a grantable
    # object (privileges such as MONITOR can be granted on it).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [USER_ACCOUNT, SNOWFLAKE_PRINCIPAL, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeUserToAccountRel = SnowflakeUserToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeUserToNetworkPolicyRel()],
    )


@dataclass(frozen=True)
class SnowflakeServiceUserSchema(CartographyNodeSchema):
    """Represents a Snowflake service user: a machine identity that cannot hold a password."""

    label: str = "SnowflakeServiceUser"
    properties: SnowflakeUserNodeProperties = SnowflakeUserNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [SERVICE_ACCOUNT, SNOWFLAKE_PRINCIPAL, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeUserToAccountRel = SnowflakeUserToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeUserToNetworkPolicyRel()],
    )
