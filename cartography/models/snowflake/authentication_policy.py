"""Snowflake authentication policy nodes.

An authentication policy decides *how* an identity may prove itself: which
authentication methods are accepted, whether MFA is required and for which
methods, which client types may connect, which security integrations are usable
for SAML or OAuth, and whether programmatic access tokens are allowed at all.
Everything that determines whether MFA can be skipped for a set of users is in
here, which is why the described settings are stored rather than just the listing
row.

The settings are only visible through ``DESCRIBE AUTHENTICATION POLICY``, so the
node combines the listing row with the described settings.

The policy is scoped to the account rather than to its schema so that cleanup can
still delete a policy whose schema was dropped between syncs; the schema is
recorded as a containment edge instead.
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
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeAuthenticationPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the authentication policy."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The authentication policy name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="Fully qualified name of the policy, as DATABASE.SCHEMA.NAME.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database holding the policy."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema holding the policy."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the policy."
    )
    owner_role_type: PropertyRef = PropertyRef(
        "owner_role_type",
        description="Whether the owning role is an account role or a database role.",
    )
    comment: PropertyRef = PropertyRef("comment", description="Policy comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the policy was created."
    )
    authentication_methods: PropertyRef = PropertyRef(
        "authentication_methods",
        description=(
            "Authentication methods the policy accepts, such as PASSWORD, SAML, "
            "OAUTH, KEYPAIR or PROGRAMMATIC_ACCESS_TOKEN. ALL accepts every method."
        ),
    )
    mfa_authentication_methods: PropertyRef = PropertyRef(
        "mfa_authentication_methods",
        description=(
            "Methods for which MFA is enforced. A method accepted by the policy but "
            "absent here can authenticate with a single factor."
        ),
    )
    mfa_enrollment: PropertyRef = PropertyRef(
        "mfa_enrollment",
        description=(
            "Whether users under the policy must enroll in MFA. OPTIONAL leaves "
            "enrollment to the user."
        ),
    )
    client_types: PropertyRef = PropertyRef(
        "client_types",
        description=(
            "Client types allowed to connect, such as SNOWFLAKE_UI, DRIVERS or "
            "SNOWSQL. ALL allows every client."
        ),
    )
    security_integrations: PropertyRef = PropertyRef(
        "security_integrations",
        description=(
            "Security integrations the policy permits for federated or OAuth "
            "authentication. ALL permits every integration in the account."
        ),
    )
    pat_policy: PropertyRef = PropertyRef(
        "pat_policy",
        description=(
            "Constraints the policy places on programmatic access tokens, such as the "
            "maximum lifetime and whether a network policy is required to use one."
        ),
    )


@dataclass(frozen=True)
class SnowflakeAuthenticationPolicyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeAuthenticationPolicy)
class SnowflakeAuthenticationPolicyToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the authentication policy as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeAuthenticationPolicyToAccountRelProperties = (
        SnowflakeAuthenticationPolicyToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAuthenticationPolicyToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeAuthenticationPolicy)
class SnowflakeAuthenticationPolicyToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the authentication policy."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeAuthenticationPolicyToSchemaRelProperties = (
        SnowflakeAuthenticationPolicyToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAuthenticationPolicySchema(CartographyNodeSchema):
    """Represents a Snowflake authentication policy: which authentication methods, clients and MFA rules apply."""

    label: str = "SnowflakeAuthenticationPolicy"
    properties: SnowflakeAuthenticationPolicyNodeProperties = (
        SnowflakeAuthenticationPolicyNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeAuthenticationPolicyToAccountRel = (
        SnowflakeAuthenticationPolicyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeAuthenticationPolicyToSchemaRel()],
    )
