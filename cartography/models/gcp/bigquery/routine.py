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
class GCPBigQueryRoutineProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Stable identifier for this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    routine_id: PropertyRef = PropertyRef(
        "routine_id", description="The short routine ID."
    )
    dataset_id: PropertyRef = PropertyRef(
        "dataset_id",
        description="The parent dataset identifier in `project_id:dataset_id` format.",
    )
    routine_type: PropertyRef = PropertyRef(
        "routine_type",
        description="Type: SCALAR_FUNCTION, PROCEDURE, or TABLE_VALUED_FUNCTION.",
    )
    language: PropertyRef = PropertyRef(
        "language", description="Language of the routine (e.g., SQL, JAVASCRIPT)."
    )
    creation_time: PropertyRef = PropertyRef(
        "creation_time", description="Creation time of the routine."
    )
    last_modified_time: PropertyRef = PropertyRef(
        "last_modified_time", description="Last modification time of the routine."
    )
    connection_id: PropertyRef = PropertyRef(
        "connection_id",
        description="The BigQuery connection resource name used by remote functions.",
    )


@dataclass(frozen=True)
class ProjectToRoutineRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class ProjectToRoutineRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToRoutineRelProperties = ProjectToRoutineRelProperties()


@dataclass(frozen=True)
class DatasetToRoutineRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class DatasetToRoutineRel(CartographyRelSchema):
    target_node_label: str = "GCPBigQueryDataset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dataset_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_ROUTINE"
    properties: DatasetToRoutineRelProperties = DatasetToRoutineRelProperties()


@dataclass(frozen=True)
class RoutineToConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class RoutineToConnectionRel(CartographyRelSchema):
    target_node_label: str = "GCPBigQueryConnection"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("connection_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CONNECTION"
    properties: RoutineToConnectionRelProperties = RoutineToConnectionRelProperties()


@dataclass(frozen=True)
class GCPBigQueryRoutineSchema(CartographyNodeSchema):
    """Represents a GCP BigQuery Routine (stored procedure, UDF, or table-valued function)."""

    label: str = "GCPBigQueryRoutine"
    properties: GCPBigQueryRoutineProperties = GCPBigQueryRoutineProperties()
    sub_resource_relationship: ProjectToRoutineRel = ProjectToRoutineRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatasetToRoutineRel(),
            RoutineToConnectionRel(),
        ],
    )
