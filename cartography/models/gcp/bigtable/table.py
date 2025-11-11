import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPBigtableTableProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name")
    name: PropertyRef = PropertyRef("name")
    granularity: PropertyRef = PropertyRef("granularity")
    instance_id: PropertyRef = PropertyRef("instance_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableTableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableTableRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToBigtableTableRelProperties = (
        ProjectToBigtableTableRelProperties()
    )


@dataclass(frozen=True)
class TableToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TableToInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPBigtableInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TABLE"
    properties: TableToInstanceRelProperties = TableToInstanceRelProperties()


@dataclass(frozen=True)
class GCPBigtableTableSchema(CartographyNodeSchema):
    label: str = "GCPBigtableTable"
    properties: GCPBigtableTableProperties = GCPBigtableTableProperties()
    sub_resource_relationship: ProjectToBigtableTableRel = ProjectToBigtableTableRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TableToInstanceRel(),
        ],
    )
