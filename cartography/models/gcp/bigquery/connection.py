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
    id: PropertyRef = PropertyRef(
        "name", description="Stable identifier for this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="The full resource name of the connection."
    )
    friendly_name: PropertyRef = PropertyRef(
        "friendlyName", description="User-friendly name for the connection."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the connection."
    )
    connection_type: PropertyRef = PropertyRef(
        "connection_type",
        description="Type of connection (e.g., cloudSql, spark, aws, azure).",
    )
    creation_time: PropertyRef = PropertyRef(
        "creationTime", description="Creation time of the connection."
    )
    last_modified_time: PropertyRef = PropertyRef(
        "lastModifiedTime", description="Last modification time of the connection."
    )
    has_credential: PropertyRef = PropertyRef(
        "hasCredential",
        description="Whether the connection has a credential configured.",
    )
    cloud_sql_instance_id: PropertyRef = PropertyRef(
        "cloud_sql_instance_id",
        description="The Cloud SQL instance ID for cloudSql connections (format: `project:region:instance`).",
    )
    aws_role_arn: PropertyRef = PropertyRef(
        "aws_role_arn", description="The IAM role ARN for aws connections."
    )
    azure_app_client_id: PropertyRef = PropertyRef(
        "azure_app_client_id",
        description="The federated application client ID for azure connections.",
    )
    service_account_id: PropertyRef = PropertyRef(
        "service_account_id",
        description="The service account email for cloudResource connections.",
    )


@dataclass(frozen=True)
class ProjectToConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """Represents a GCP BigQuery Connection (external data source connection)."""

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
