"""Snowflake password policy nodes.

A password policy is a schema-level object that sets the length, complexity, age,
retry and history requirements for every user it is attached to. The requirements
themselves are only visible through ``DESCRIBE PASSWORD POLICY``, so the node
combines the listing row with the described settings.

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
class SnowflakePasswordPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the password policy."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The password policy name."
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
    password_min_length: PropertyRef = PropertyRef(
        "password_min_length", description="Minimum number of characters required."
    )
    password_max_length: PropertyRef = PropertyRef(
        "password_max_length", description="Maximum number of characters allowed."
    )
    password_min_upper_case_chars: PropertyRef = PropertyRef(
        "password_min_upper_case_chars",
        description="Minimum number of uppercase characters required.",
    )
    password_min_lower_case_chars: PropertyRef = PropertyRef(
        "password_min_lower_case_chars",
        description="Minimum number of lowercase characters required.",
    )
    password_min_numeric_chars: PropertyRef = PropertyRef(
        "password_min_numeric_chars",
        description="Minimum number of digits required.",
    )
    password_min_special_chars: PropertyRef = PropertyRef(
        "password_min_special_chars",
        description="Minimum number of special characters required.",
    )
    password_min_age_days: PropertyRef = PropertyRef(
        "password_min_age_days",
        description="Days a password must be kept before it may be changed again.",
    )
    password_max_age_days: PropertyRef = PropertyRef(
        "password_max_age_days",
        description=(
            "Days before a password must be rotated. Zero disables expiry, so "
            "passwords under this policy never have to change."
        ),
    )
    password_max_retries: PropertyRef = PropertyRef(
        "password_max_retries",
        description="Failed attempts allowed before the user is locked out.",
    )
    password_lockout_time_mins: PropertyRef = PropertyRef(
        "password_lockout_time_mins",
        description="Minutes a user stays locked out after too many failed attempts.",
    )
    password_history: PropertyRef = PropertyRef(
        "password_history",
        description="Number of previous passwords that may not be reused.",
    )


@dataclass(frozen=True)
class SnowflakePasswordPolicyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakePasswordPolicy)
class SnowflakePasswordPolicyToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the password policy as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakePasswordPolicyToAccountRelProperties = (
        SnowflakePasswordPolicyToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakePasswordPolicyToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakePasswordPolicy)
class SnowflakePasswordPolicyToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the password policy."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakePasswordPolicyToSchemaRelProperties = (
        SnowflakePasswordPolicyToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakePasswordPolicySchema(CartographyNodeSchema):
    """Represents a Snowflake password policy: the complexity and rotation rules applied to passwords."""

    label: str = "SnowflakePasswordPolicy"
    properties: SnowflakePasswordPolicyNodeProperties = (
        SnowflakePasswordPolicyNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakePasswordPolicyToAccountRel = (
        SnowflakePasswordPolicyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakePasswordPolicyToSchemaRel()],
    )
