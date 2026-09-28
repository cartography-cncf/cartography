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
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeNetworkRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the network rule."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The network rule name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        extra_index=True,
        description="Fully qualified DATABASE.SCHEMA.NAME of the network rule.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Name of the database containing the network rule."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Name of the schema containing the network rule."
    )
    rule_type: PropertyRef = PropertyRef(
        "rule_type",
        description=(
            "What the value list holds: IPV4, IPV6, AWSVPCEID, AZURELINKID, HOST_PORT "
            "or PRIVATE_HOST_PORT."
        ),
    )
    mode: PropertyRef = PropertyRef(
        "mode",
        description=(
            "Direction the rule governs: INGRESS for inbound connections, EGRESS for "
            "outbound calls from UDFs and procedures, INTERNAL_STAGE for stage access."
        ),
    )
    value_list: PropertyRef = PropertyRef(
        "value_list",
        description="The addresses, endpoint ids or host:port pairs the rule matches.",
    )
    value_count: PropertyRef = PropertyRef(
        "value_count", description="Number of entries in the rule's value list."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the network rule."
    )
    comment: PropertyRef = PropertyRef("comment", description="Network rule comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the network rule was created."
    )


@dataclass(frozen=True)
class SnowflakeNetworkRuleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeNetworkRule)
class SnowflakeNetworkRuleToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the network rule as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeNetworkRuleToAccountRelProperties = (
        SnowflakeNetworkRuleToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNetworkRuleToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeNetworkRule)
class SnowflakeNetworkRuleToSchemaRel(CartographyRelSchema):
    """A Snowflake schema contains the network rule."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeNetworkRuleToSchemaRelProperties = (
        SnowflakeNetworkRuleToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNetworkRuleSchema(CartographyNodeSchema):
    """Represents a Snowflake network rule: a reusable list of network identifiers referenced by policies and integrations."""

    label: str = "SnowflakeNetworkRule"
    properties: SnowflakeNetworkRuleNodeProperties = (
        SnowflakeNetworkRuleNodeProperties()
    )
    # NetworkAccessControl: ontology label; a network rule gates network access.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [NETWORK_ACCESS_CONTROL, SNOWFLAKE_SECURABLE],
    )
    sub_resource_relationship: SnowflakeNetworkRuleToAccountRel = (
        SnowflakeNetworkRuleToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [SnowflakeNetworkRuleToSchemaRel()],
    )
