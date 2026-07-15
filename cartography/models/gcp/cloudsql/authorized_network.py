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
class GCPCloudSQLAuthorizedNetworkProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="`{instance_self_link}/authorizedNetworks/{value}`."
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Human-readable label assigned to the authorized network entry.",
    )
    value: PropertyRef = PropertyRef(
        "value",
        description="The CIDR allowed inbound, e.g. `203.0.113.0/24` or `0.0.0.0/0`.",
    )
    expiration_time: PropertyRef = PropertyRef(
        "expiration_time",
        description="RFC 3339 timestamp at which the entry expires, if set.",
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id", description="The selfLink of the parent GCPCloudSQLInstance."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="The timestamp of the last update.",
    )


@dataclass(frozen=True)
class AuthorizedNetworkToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class AuthorizedNetworkToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AuthorizedNetworkToProjectRelProperties = (
        AuthorizedNetworkToProjectRelProperties()
    )


@dataclass(frozen=True)
class AuthorizedNetworkToSqlInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class AuthorizedNetworkToSqlInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AUTHORIZED_NETWORK"
    properties: AuthorizedNetworkToSqlInstanceRelProperties = (
        AuthorizedNetworkToSqlInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudSQLAuthorizedNetworkSchema(CartographyNodeSchema):
    """A CIDR entry authorized to connect to a Cloud SQL instance."""

    label: str = "GCPCloudSQLAuthorizedNetwork"
    properties: GCPCloudSQLAuthorizedNetworkProperties = (
        GCPCloudSQLAuthorizedNetworkProperties()
    )
    sub_resource_relationship: AuthorizedNetworkToProjectRel = (
        AuthorizedNetworkToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AuthorizedNetworkToSqlInstanceRel(),
        ],
    )
