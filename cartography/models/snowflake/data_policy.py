"""Snowflake data governance policy nodes.

Snowflake ships five schema-level policies that control what a query may see:
masking (column values), row access (which rows), projection (whether a column may
be selected at all), aggregation (whether only aggregates may be returned) and
join (whether a table may be joined). They are separate ``SHOW`` commands but one
concept, and ``ACCOUNT_USAGE.POLICY_REFERENCES`` returns their attachments in a
single row shape, so Cartography collapses all five onto one label with a
``policy_kind`` discriminator. A label per kind would multiply the attachment
edges fivefold for no analytical gain.

All five are Enterprise-edition features, so a Standard-edition account has no
data policy nodes at all.

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
class SnowflakeDataPolicyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the data policy."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The data policy name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="Fully qualified name of the policy, as DATABASE.SCHEMA.NAME.",
    )
    policy_kind: PropertyRef = PropertyRef(
        "policy_kind",
        extra_index=True,
        description=(
            "Which governance policy this is: MASKING_POLICY, ROW_ACCESS_POLICY, "
            "PROJECTION_POLICY, AGGREGATION_POLICY or JOIN_POLICY."
        ),
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database holding the policy."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema holding the policy."
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description="The object kind Snowflake reports for the policy.",
    )
    signature: PropertyRef = PropertyRef(
        "signature",
        description=(
            "The policy's argument list, which decides the column types it can be "
            "attached to."
        ),
    )
    return_type: PropertyRef = PropertyRef(
        "return_type",
        description="The type the policy body returns, for masking policies.",
    )
    body: PropertyRef = PropertyRef(
        "body",
        description=(
            "The SQL expression the policy evaluates. This is where the actual "
            "condition lives, for example which roles see unmasked values."
        ),
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


@dataclass(frozen=True)
class SnowflakeDataPolicyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeDataPolicy)
class SnowflakeDataPolicyToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the data policy as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeDataPolicyToAccountRelProperties = (
        SnowflakeDataPolicyToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeDataPolicyToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeDataPolicy)
class SnowflakeDataPolicyToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the data policy."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeDataPolicyToSchemaRelProperties = (
        SnowflakeDataPolicyToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeDataPolicySchema(CartographyNodeSchema):
    """Represents a Snowflake data governance policy that restricts what a query may read."""

    label: str = "SnowflakeDataPolicy"
    properties: SnowflakeDataPolicyNodeProperties = SnowflakeDataPolicyNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeDataPolicyToAccountRel = (
        SnowflakeDataPolicyToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeDataPolicyToSchemaRel()],
    )
