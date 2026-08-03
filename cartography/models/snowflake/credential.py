"""Snowflake credential nodes.

``SNOWFLAKE.ACCOUNT_USAGE.CREDENTIALS`` is the only place that enumerates every
authentication factor registered in an account: passwords, key pairs, passkeys,
TOTP enrollments, programmatic access tokens and the cloud or OIDC identities
used for workload identity federation. It is therefore the authoritative source
for MFA posture, and it answers questions ``SHOW USERS`` cannot, such as which
service identity still authenticates with a password.

Two caveats are inherent to the source and cannot be worked around:

- The view lags reality by up to two hours, so a credential created or dropped in
  the last couple of hours may be missing or stale.
- Reading it requires ``IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE``, so an
  under-privileged collector simply has no credential nodes.

Only metadata is stored. No secret, private key or token value is read back from
Snowflake, and none is recorded here.

Ownership is declared twice, once per possible owner label, because a Snowflake
identity is modelled either as ``SnowflakeUser`` or as ``SnowflakeServiceUser``
and the ontology constraint that forces ``OWNED_BY`` is checked per concrete
label pair.
"""

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
class SnowflakeCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the credential."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The credential name."
    )
    credential_id: PropertyRef = PropertyRef(
        "credential_id",
        extra_index=True,
        description="Snowflake's internal identifier for the credential.",
    )
    credential_type: PropertyRef = PropertyRef(
        "credential_type",
        description=(
            "The factor kind: PASSWORD, KEYPAIR, PAT, PASSKEY, TOTP, OIDC, or AWS / "
            "AZURE / GCP for workload identity federation. PASSWORD on a service "
            "identity, or a user whose only factor is PASSWORD, means no MFA."
        ),
    )
    user_name: PropertyRef = PropertyRef(
        "user_name",
        extra_index=True,
        description="Name of the Snowflake user the credential authenticates as.",
    )
    domain: PropertyRef = PropertyRef(
        "domain",
        description="The object domain the credential belongs to, normally USER.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Credential status; only an active credential can authenticate.",
    )
    additional_details: PropertyRef = PropertyRef(
        "additional_details",
        description=(
            "Snowflake's per-type detail blob, such as a key-pair fingerprint or a "
            "federated issuer. Never contains the secret itself."
        ),
    )
    comment: PropertyRef = PropertyRef("comment", description="Credential comment.")
    created_by: PropertyRef = PropertyRef(
        "created_by", description="Name of the user that created the credential."
    )
    last_altered_by: PropertyRef = PropertyRef(
        "last_altered_by",
        description="Name of the user that last changed the credential.",
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the credential was created."
    )
    last_used_on: PropertyRef = PropertyRef(
        "last_used_on",
        description=(
            "When the credential last authenticated. Null means it has never been "
            "used, which makes it a candidate for removal."
        ),
    )
    last_altered: PropertyRef = PropertyRef(
        "last_altered", description="When the credential was last changed."
    )
    expiration_date: PropertyRef = PropertyRef(
        "expiration_date",
        description=(
            "When the credential expires. Null means it never expires, so it stays "
            "valid until it is explicitly revoked."
        ),
    )


@dataclass(frozen=True)
class SnowflakeCredentialToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeCredential)
class SnowflakeCredentialToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the credential as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeCredentialToAccountRelProperties = (
        SnowflakeCredentialToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCredentialToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeCredential)-[:OWNED_BY]->(:SnowflakeUser)
class SnowflakeCredentialToUserRel(CartographyRelSchema):
    """The credential authenticates as this human Snowflake user."""

    target_node_label: str = "SnowflakeUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: SnowflakeCredentialToUserRelProperties = (
        SnowflakeCredentialToUserRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCredentialToServiceUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeCredential)-[:OWNED_BY]->(:SnowflakeServiceUser)
class SnowflakeCredentialToServiceUserRel(CartographyRelSchema):
    """The credential authenticates as this Snowflake service user."""

    target_node_label: str = "SnowflakeServiceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: SnowflakeCredentialToServiceUserRelProperties = (
        SnowflakeCredentialToServiceUserRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeCredentialSchema(CartographyNodeSchema):
    """Represents one authentication factor registered against a Snowflake user."""

    # Deliberately not labelled APIKey. This node covers every factor kind, including
    # passwords, passkeys and TOTP, so labelling it would make cross-provider
    # `MATCH (:APIKey)` queries count MFA factors as API keys. The one factor that
    # genuinely is an API key, a programmatic access token, is already carried by
    # SnowflakeProgrammaticAccessToken, which does hold the label.
    label: str = "SnowflakeCredential"
    properties: SnowflakeCredentialNodeProperties = SnowflakeCredentialNodeProperties()
    sub_resource_relationship: SnowflakeCredentialToAccountRel = (
        SnowflakeCredentialToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeCredentialToUserRel(),
            SnowflakeCredentialToServiceUserRel(),
        ],
    )
