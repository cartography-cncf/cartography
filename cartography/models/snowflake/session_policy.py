"""Snowflake session policy nodes.

A session policy caps how long an idle Snowflake session stays authenticated,
separately for programmatic clients and for the Snowsight web interface. A long or
unset idle timeout means a stolen session token or an unattended browser tab keeps
working for as long as Snowflake's default allows.

The timeouts are only visible through ``DESCRIBE SESSION POLICY``, so the node
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
class SnowflakeSessionPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the session policy."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The session policy name."
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
    session_idle_timeout_mins: PropertyRef = PropertyRef(
        "session_idle_timeout_mins",
        description=(
            "Minutes an idle programmatic session stays authenticated before it has "
            "to re-authenticate."
        ),
    )
    session_ui_idle_timeout_mins: PropertyRef = PropertyRef(
        "session_ui_idle_timeout_mins",
        description=(
            "Minutes an idle Snowsight session stays authenticated. A high value "
            "leaves an unattended browser session usable."
        ),
    )
    allowed_secondary_authentication_methods: PropertyRef = PropertyRef(
        "allowed_secondary_authentication_methods",
        description=(
            "Secondary authentication methods the policy permits, such as password "
            "re-entry, when a session has to be re-verified."
        ),
    )


@dataclass(frozen=True)
class SnowflakeSessionPolicyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeSessionPolicy)
class SnowflakeSessionPolicyToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the session policy as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeSessionPolicyToAccountRelProperties = (
        SnowflakeSessionPolicyToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSessionPolicyToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeSessionPolicy)
class SnowflakeSessionPolicyToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the session policy."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeSessionPolicyToSchemaRelProperties = (
        SnowflakeSessionPolicyToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeSessionPolicySchema(CartographyNodeSchema):
    """Represents a Snowflake session policy: the idle timeouts that govern how long a session stays authenticated."""

    label: str = "SnowflakeSessionPolicy"
    properties: SnowflakeSessionPolicyNodeProperties = (
        SnowflakeSessionPolicyNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeSessionPolicyToAccountRel = (
        SnowflakeSessionPolicyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeSessionPolicyToSchemaRel()],
    )
