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
class SnowflakeAlertNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the alert."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Alert name.")
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description="Fully-qualified database.schema.alert name.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the alert."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the alert."
    )
    warehouse: PropertyRef = PropertyRef(
        "warehouse",
        description="Name of the virtual warehouse that evaluates the alert's condition.",
    )
    schedule: PropertyRef = PropertyRef(
        "schedule",
        description="How often the condition is evaluated, as a cron expression or an interval.",
    )
    state: PropertyRef = PropertyRef(
        "state", description="Whether the alert is started or suspended."
    )
    condition: PropertyRef = PropertyRef(
        "condition",
        description="SQL query whose result decides whether the action runs.",
    )
    action: PropertyRef = PropertyRef(
        "action", description="SQL the alert executes when the condition is met."
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the alert."
    )
    comment: PropertyRef = PropertyRef("comment", description="Alert comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the alert was created."
    )


@dataclass(frozen=True)
class SnowflakeAlertToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeAlert)
class SnowflakeAlertToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the alert as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeAlertToAccountRelProperties = (
        SnowflakeAlertToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAlertToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeAlert)
class SnowflakeAlertToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the alert in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeAlertToSchemaRelProperties = (
        SnowflakeAlertToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAlertToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAlert)-[:USES_WAREHOUSE]->(:SnowflakeWarehouse)
class SnowflakeAlertToWarehouseRel(CartographyRelSchema):
    """A Snowflake alert evaluates its condition on this virtual warehouse."""

    target_node_label: str = "SnowflakeWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: SnowflakeAlertToWarehouseRelProperties = (
        SnowflakeAlertToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeAlertSchema(CartographyNodeSchema):
    """Represents a Snowflake alert: a scheduled condition query paired with the SQL it triggers."""

    label: str = "SnowflakeAlert"
    properties: SnowflakeAlertNodeProperties = SnowflakeAlertNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeAlertToAccountRel = SnowflakeAlertToAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeAlertToSchemaRel(),
            SnowflakeAlertToWarehouseRel(),
        ],
    )
