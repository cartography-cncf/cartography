from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPBigQueryConnectionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    friendly_name: PropertyRef = PropertyRef("friendlyName")
    description: PropertyRef = PropertyRef("description")
    connection_type: PropertyRef = PropertyRef("connection_type")
    creation_time: PropertyRef = PropertyRef("creationTime")
    last_modified_time: PropertyRef = PropertyRef("lastModifiedTime")
    has_credential: PropertyRef = PropertyRef("hasCredential")


@dataclass(frozen=True)
class ProjectToConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToConnectionRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToConnectionRelProperties = ProjectToConnectionRelProperties()


@dataclass(frozen=True)
class GCPBigQueryConnectionSchema(CartographyNodeSchema):
    label: str = "GCPBigQueryConnection"
    properties: GCPBigQueryConnectionProperties = GCPBigQueryConnectionProperties()
    sub_resource_relationship: ProjectToConnectionRel = ProjectToConnectionRel()
