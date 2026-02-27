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
    cloud_sql_instance_id: PropertyRef = PropertyRef("cloud_sql_instance_id")
    aws_role_arn: PropertyRef = PropertyRef("aws_role_arn")
    azure_app_client_id: PropertyRef = PropertyRef("azure_app_client_id")
    service_account_id: PropertyRef = PropertyRef("service_account_id")


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
class ConnectionToCloudSQLRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ConnectionToCloudSQLRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"connection_name": PropertyRef("cloud_sql_instance_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: ConnectionToCloudSQLRelProperties = ConnectionToCloudSQLRelProperties()


@dataclass(frozen=True)
class ConnectionToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ConnectionToAWSRoleRel(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_WITH"
    properties: ConnectionToAWSRoleRelProperties = ConnectionToAWSRoleRelProperties()


@dataclass(frozen=True)
class ConnectionToEntraSPRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ConnectionToEntraSPRel(CartographyRelSchema):
    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("azure_app_client_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_WITH"
    properties: ConnectionToEntraSPRelProperties = ConnectionToEntraSPRelProperties()


@dataclass(frozen=True)
class ConnectionToGCPServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ConnectionToGCPServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_WITH"
    properties: ConnectionToGCPServiceAccountRelProperties = (
        ConnectionToGCPServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class GCPBigQueryConnectionSchema(CartographyNodeSchema):
    label: str = "GCPBigQueryConnection"
    properties: GCPBigQueryConnectionProperties = GCPBigQueryConnectionProperties()
    sub_resource_relationship: ProjectToConnectionRel = ProjectToConnectionRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ConnectionToCloudSQLRel(),
            ConnectionToAWSRoleRel(),
            ConnectionToEntraSPRel(),
            ConnectionToGCPServiceAccountRel(),
        ],
    )
