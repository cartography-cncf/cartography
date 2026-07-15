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
class GCPBigQueryTableProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    table_id: PropertyRef = PropertyRef("table_id", description="The short table ID.")
    dataset_id: PropertyRef = PropertyRef(
        "dataset_id",
        description="The parent dataset identifier in `project_id:dataset_id` format.",
    )
    type: PropertyRef = PropertyRef(
        "type", description="Table type: TABLE, VIEW, MATERIALIZED_VIEW, or EXTERNAL."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="Creation time of the table."
    )
    expiration_time: PropertyRef = PropertyRef(
        "expiration_time", description="Expiration time of the table, if set."
    )
    num_bytes: PropertyRef = PropertyRef(
        "num_bytes", description="Size of the table in bytes."
    )
    num_long_term_bytes: PropertyRef = PropertyRef(
        "num_long_term_bytes", description="Size of long-term storage in bytes."
    )
    num_rows: PropertyRef = PropertyRef(
        "num_rows", description="Number of rows in the table."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the table."
    )
    friendly_name: PropertyRef = PropertyRef(
        "friendly_name", description="User-friendly name for the table."
    )
    connection_id: PropertyRef = PropertyRef(
        "connection_id",
        description="The BigQuery connection resource name used by external tables.",
    )
    kms_key_name: PropertyRef = PropertyRef(
        "kms_key_name",
        description="Customer-managed encryption key configured on the table, when present.",
    )


@dataclass(frozen=True)
class ProjectToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class ProjectToTableRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToTableRelProperties = ProjectToTableRelProperties()


@dataclass(frozen=True)
class DatasetToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class DatasetToTableRel(CartographyRelSchema):
    target_node_label: str = "GCPBigQueryDataset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dataset_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TABLE"
    properties: DatasetToTableRelProperties = DatasetToTableRelProperties()


@dataclass(frozen=True)
class TableToConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class TableToConnectionRel(CartographyRelSchema):
    target_node_label: str = "GCPBigQueryConnection"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("connection_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CONNECTION"
    properties: TableToConnectionRelProperties = TableToConnectionRelProperties()


@dataclass(frozen=True)
class GCPBigQueryTableSchema(CartographyNodeSchema):
    """Represents a GCP BigQuery Table, View, or Materialized View."""

    label: str = "GCPBigQueryTable"
    properties: GCPBigQueryTableProperties = GCPBigQueryTableProperties()
    sub_resource_relationship: ProjectToTableRel = ProjectToTableRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatasetToTableRel(),
            TableToConnectionRel(),
        ],
    )
