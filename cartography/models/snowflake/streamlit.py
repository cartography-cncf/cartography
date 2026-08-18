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
class SnowflakeStreamlitNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the Streamlit app."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Streamlit app name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description="Fully-qualified database.schema.streamlit name.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the Streamlit app."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the Streamlit app."
    )
    title: PropertyRef = PropertyRef(
        "title", description="Display title shown in Snowsight."
    )
    url_id: PropertyRef = PropertyRef(
        "url_id", description="Opaque identifier used in the app's Snowsight URL."
    )
    query_warehouse: PropertyRef = PropertyRef(
        "query_warehouse",
        description="Name of the virtual warehouse the app's queries run on.",
    )
    compute_pool: PropertyRef = PropertyRef(
        "compute_pool",
        description="Name of the compute pool backing a container-runtime app.",
    )
    external_access_integrations: PropertyRef = PropertyRef(
        "external_access_integrations",
        description="External access integrations that let the app reach the network.",
    )
    main_file: PropertyRef = PropertyRef(
        "main_file", description="Path of the Python file that renders the app."
    )
    root_location: PropertyRef = PropertyRef(
        "root_location",
        description="Stage location holding the app's source files.",
    )
    default_packages: PropertyRef = PropertyRef(
        "default_packages",
        description="Packages Snowflake installs into the app's environment.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the Streamlit app."
    )
    comment: PropertyRef = PropertyRef("comment", description="Streamlit app comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the Streamlit app was created."
    )


@dataclass(frozen=True)
class SnowflakeStreamlitToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeStreamlit)
class SnowflakeStreamlitToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the Streamlit app as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeStreamlitToAccountRelProperties = (
        SnowflakeStreamlitToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStreamlitToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeStreamlit)
class SnowflakeStreamlitToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the Streamlit app in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeStreamlitToSchemaRelProperties = (
        SnowflakeStreamlitToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStreamlitToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStreamlit)-[:USES_WAREHOUSE]->(:SnowflakeWarehouse)
class SnowflakeStreamlitToWarehouseRel(CartographyRelSchema):
    """A Snowflake Streamlit app runs its queries on this virtual warehouse."""

    target_node_label: str = "SnowflakeWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: SnowflakeStreamlitToWarehouseRelProperties = (
        SnowflakeStreamlitToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStreamlitToComputePoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStreamlit)-[:RUNS_ON]->(:SnowflakeComputePool)
# Deliberately not WORKLOAD_PARENT: neither endpoint carries a workload ontology
# label, so no ontology relationship constraint applies to this pair and inventing
# the canonical name here would imply a mapping that does not exist.
class SnowflakeStreamlitToComputePoolRel(CartographyRelSchema):
    """A container-runtime Snowflake Streamlit app executes on this compute pool."""

    target_node_label: str = "SnowflakeComputePool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("compute_pool_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_ON"
    properties: SnowflakeStreamlitToComputePoolRelProperties = (
        SnowflakeStreamlitToComputePoolRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStreamlitToExternalAccessIntegrationRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeStreamlit)-[:USES_INTEGRATION]->(:SnowflakeExternalAccessIntegration)
class SnowflakeStreamlitToExternalAccessIntegrationRel(CartographyRelSchema):
    """A Snowflake Streamlit app reaches the network through this external access integration."""

    target_node_label: str = "SnowflakeExternalAccessIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("external_access_integration_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeStreamlitToExternalAccessIntegrationRelProperties = (
        SnowflakeStreamlitToExternalAccessIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeStreamlitSchema(CartographyNodeSchema):
    """Represents a Snowflake Streamlit app: a Python web app served by Snowflake over account data."""

    label: str = "SnowflakeStreamlit"
    properties: SnowflakeStreamlitNodeProperties = SnowflakeStreamlitNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeStreamlitToAccountRel = (
        SnowflakeStreamlitToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeStreamlitToSchemaRel(),
            SnowflakeStreamlitToWarehouseRel(),
            SnowflakeStreamlitToComputePoolRel(),
            SnowflakeStreamlitToExternalAccessIntegrationRel(),
        ],
    )
