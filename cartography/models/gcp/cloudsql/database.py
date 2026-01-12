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
class GCPSqlDatabaseProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    charset: PropertyRef = PropertyRef("charset")
    collation: PropertyRef = PropertyRef("collation")
    instance_id: PropertyRef = PropertyRef("instance_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToSqlDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToSqlDatabaseRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToSqlDatabaseRelProperties = ProjectToSqlDatabaseRelProperties()


@dataclass(frozen=True)
class InstanceToSqlDatabaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InstanceToSqlDatabaseRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: InstanceToSqlDatabaseRelProperties = (
        InstanceToSqlDatabaseRelProperties()
    )


@dataclass(frozen=True)
class GCPSqlDatabaseSchema(CartographyNodeSchema):
    label: str = "GCPCloudSQLDatabase"
    properties: GCPSqlDatabaseProperties = GCPSqlDatabaseProperties()
    sub_resource_relationship: ProjectToSqlDatabaseRel = ProjectToSqlDatabaseRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InstanceToSqlDatabaseRel(),
        ],
    )
