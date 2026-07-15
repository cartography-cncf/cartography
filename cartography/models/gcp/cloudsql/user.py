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


# --- Node Properties ---
@dataclass(frozen=True)
class GCPSqlUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Synthetic `{instance_self_link}/users/{user_name}@{host}` identifier."
        ),
    )
    name: PropertyRef = PropertyRef("name", description="The name of the user.")
    host: PropertyRef = PropertyRef(
        "host", description="The host from which the user is allowed to connect."
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id",
        description="Identifier of the parent service instance.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class ProjectToSqlUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class ProjectToSqlUserRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToSqlUserRelProperties = ProjectToSqlUserRelProperties()


@dataclass(frozen=True)
class InstanceToSqlUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class InstanceToSqlUserRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_USER"
    properties: InstanceToSqlUserRelProperties = InstanceToSqlUserRelProperties()


@dataclass(frozen=True)
class GCPSqlUserSchema(CartographyNodeSchema):
    """Representation of a GCP [Cloud SQL User](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/users)."""

    label: str = "GCPCloudSQLUser"
    properties: GCPSqlUserProperties = GCPSqlUserProperties()
    sub_resource_relationship: ProjectToSqlUserRel = ProjectToSqlUserRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InstanceToSqlUserRel(),
        ],
    )
