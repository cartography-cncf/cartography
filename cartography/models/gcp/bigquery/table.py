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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    table_id: PropertyRef = PropertyRef("table_id")
    dataset_id: PropertyRef = PropertyRef("dataset_id")
    type: PropertyRef = PropertyRef("type")
    creation_time: PropertyRef = PropertyRef("creation_time")
    expiration_time: PropertyRef = PropertyRef("expiration_time")
    num_bytes: PropertyRef = PropertyRef("num_bytes")
    num_long_term_bytes: PropertyRef = PropertyRef("num_long_term_bytes")
    num_rows: PropertyRef = PropertyRef("num_rows")
    description: PropertyRef = PropertyRef("description")
    friendly_name: PropertyRef = PropertyRef("friendly_name")
    connection_id: PropertyRef = PropertyRef("connection_id")


@dataclass(frozen=True)
class ProjectToTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    label: str = "GCPBigQueryTable"
    properties: GCPBigQueryTableProperties = GCPBigQueryTableProperties()
    sub_resource_relationship: ProjectToTableRel = ProjectToTableRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatasetToTableRel(),
            TableToConnectionRel(),
        ],
    )
