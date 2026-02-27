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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    routine_id: PropertyRef = PropertyRef("routine_id")
    dataset_id: PropertyRef = PropertyRef("dataset_id")
    routine_type: PropertyRef = PropertyRef("routine_type")
    language: PropertyRef = PropertyRef("language")
    creation_time: PropertyRef = PropertyRef("creation_time")
    last_modified_time: PropertyRef = PropertyRef("last_modified_time")


@dataclass(frozen=True)
class ProjectToRoutineRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
class GCPBigQueryRoutineSchema(CartographyNodeSchema):
    label: str = "GCPBigQueryRoutine"
    properties: GCPBigQueryRoutineProperties = GCPBigQueryRoutineProperties()
    sub_resource_relationship: ProjectToRoutineRel = ProjectToRoutineRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DatasetToRoutineRel(),
        ],
    )
