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
class SnowflakeNotebookNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the notebook."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Notebook name."
    )
    qualified_name: PropertyRef = PropertyRef(
        "qualified_name",
        description="Fully-qualified database.schema.notebook name.",
    )
    database_name: PropertyRef = PropertyRef(
        "database_name", description="Database containing the notebook."
    )
    schema_name: PropertyRef = PropertyRef(
        "schema_name", description="Schema containing the notebook."
    )
    title: PropertyRef = PropertyRef(
        "title", description="Display title shown in Snowsight."
    )
    query_warehouse: PropertyRef = PropertyRef(
        "query_warehouse",
        description="Name of the virtual warehouse the notebook's SQL cells run on.",
    )
    compute_pool: PropertyRef = PropertyRef(
        "compute_pool",
        description="Name of the compute pool backing a container-runtime notebook.",
    )
    external_access_integrations: PropertyRef = PropertyRef(
        "external_access_integrations",
        description="External access integrations that let the notebook reach the network.",
    )
    external_access_secrets: PropertyRef = PropertyRef(
        "external_access_secrets",
        description="References to the secrets the notebook may read when calling out.",
    )
    runtime_name: PropertyRef = PropertyRef(
        "runtime_name", description="Container runtime image the notebook executes on."
    )
    default_version: PropertyRef = PropertyRef(
        "default_version",
        description="Version of the notebook's files that Snowflake runs by default.",
    )
    main_file: PropertyRef = PropertyRef(
        "main_file", description="Path of the notebook file that is executed."
    )
    url_id: PropertyRef = PropertyRef(
        "url_id", description="Opaque identifier used in the notebook's Snowsight URL."
    )
    import_urls: PropertyRef = PropertyRef(
        "import_urls",
        description="Stage locations the notebook's supporting files were imported from.",
    )
    live_version_location_uri: PropertyRef = PropertyRef(
        "live_version_location_uri",
        description="Stage URI holding the currently live version of the notebook's files.",
    )
    owner: PropertyRef = PropertyRef(
        "owner", description="Name of the role that owns the notebook."
    )
    comment: PropertyRef = PropertyRef("comment", description="Notebook comment.")
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the notebook was created."
    )


@dataclass(frozen=True)
class SnowflakeNotebookToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeNotebook)
class SnowflakeNotebookToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the notebook as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeNotebookToAccountRelProperties = (
        SnowflakeNotebookToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotebookToSchemaRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeSchema)-[:CONTAINS]->(:SnowflakeNotebook)
class SnowflakeNotebookToSchemaRel(CartographyRelSchema):
    """A Snowflake schema holds the notebook in its namespace."""

    target_node_label: str = "SnowflakeSchema"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_schema_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: SnowflakeNotebookToSchemaRelProperties = (
        SnowflakeNotebookToSchemaRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotebookToWarehouseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeNotebook)-[:USES_WAREHOUSE]->(:SnowflakeWarehouse)
class SnowflakeNotebookToWarehouseRel(CartographyRelSchema):
    """A Snowflake notebook runs its queries on this virtual warehouse."""

    target_node_label: str = "SnowflakeWarehouse"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("warehouse_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_WAREHOUSE"
    properties: SnowflakeNotebookToWarehouseRelProperties = (
        SnowflakeNotebookToWarehouseRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotebookToComputePoolRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeNotebook)-[:RUNS_ON]->(:SnowflakeComputePool)
# Deliberately not WORKLOAD_PARENT: neither endpoint carries a workload ontology
# label, so no ontology relationship constraint applies to this pair and inventing
# the canonical name here would imply a mapping that does not exist.
class SnowflakeNotebookToComputePoolRel(CartographyRelSchema):
    """A container-runtime Snowflake notebook executes on this compute pool."""

    target_node_label: str = "SnowflakeComputePool"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("compute_pool_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_ON"
    properties: SnowflakeNotebookToComputePoolRelProperties = (
        SnowflakeNotebookToComputePoolRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotebookToExternalAccessIntegrationRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeNotebook)-[:USES_INTEGRATION]->(:SnowflakeExternalAccessIntegration)
class SnowflakeNotebookToExternalAccessIntegrationRel(CartographyRelSchema):
    """A Snowflake notebook reaches the network through this external access integration."""

    target_node_label: str = "SnowflakeExternalAccessIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("external_access_integration_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_INTEGRATION"
    properties: SnowflakeNotebookToExternalAccessIntegrationRelProperties = (
        SnowflakeNotebookToExternalAccessIntegrationRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotebookToSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeNotebook)-[:USES_SECRET]->(:SnowflakeSecret)
class SnowflakeNotebookToSecretRel(CartographyRelSchema):
    """A Snowflake notebook is allowed to read this secret when calling out."""

    target_node_label: str = "SnowflakeSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("secret_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: SnowflakeNotebookToSecretRelProperties = (
        SnowflakeNotebookToSecretRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotebookSchema(CartographyNodeSchema):
    """Represents a Snowflake notebook: interactive code and SQL stored as an account object."""

    label: str = "SnowflakeNotebook"
    properties: SnowflakeNotebookNodeProperties = SnowflakeNotebookNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeNotebookToAccountRel = (
        SnowflakeNotebookToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeNotebookToSchemaRel(),
            SnowflakeNotebookToWarehouseRel(),
            SnowflakeNotebookToComputePoolRel(),
            SnowflakeNotebookToSecretRel(),
            SnowflakeNotebookToExternalAccessIntegrationRel(),
        ],
    )
