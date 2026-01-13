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
class GCPSqlInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("selfLink")
    name: PropertyRef = PropertyRef("name")
    database_version: PropertyRef = PropertyRef("databaseVersion")
    region: PropertyRef = PropertyRef("region")
    gce_zone: PropertyRef = PropertyRef("gceZone")
    state: PropertyRef = PropertyRef("state")
    backend_type: PropertyRef = PropertyRef("backendType")
    network_id: PropertyRef = PropertyRef("network_id")
    service_account_email: PropertyRef = PropertyRef("service_account_email")
    connection_name: PropertyRef = PropertyRef("connectionName")
    tier: PropertyRef = PropertyRef("tier")
    disk_size_gb: PropertyRef = PropertyRef("disk_size_gb")
    disk_type: PropertyRef = PropertyRef("disk_type")
    availability_type: PropertyRef = PropertyRef("availability_type")
    backup_enabled: PropertyRef = PropertyRef("backup_enabled")
    require_ssl: PropertyRef = PropertyRef("require_ssl")
    ip_addresses: PropertyRef = PropertyRef("ip_addresses")
    backup_configuration: PropertyRef = PropertyRef("backup_configuration")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToSqlInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToSqlInstanceRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToSqlInstanceRelProperties = ProjectToSqlInstanceRelProperties()


@dataclass(frozen=True)
class SqlInstanceToVpcRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SqlInstanceToVpcRel(CartographyRelSchema):
    target_node_label: str = "GCPVpc"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("network_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: SqlInstanceToVpcRelProperties = SqlInstanceToVpcRelProperties()


@dataclass(frozen=True)
class SqlInstanceToServiceAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SqlInstanceToServiceAccountRel(CartographyRelSchema):
    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("service_account_email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SERVICE_ACCOUNT"
    properties: SqlInstanceToServiceAccountRelProperties = (
        SqlInstanceToServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class GCPSqlInstanceSchema(CartographyNodeSchema):
    label: str = "GCPCloudSQLInstance"
    properties: GCPSqlInstanceProperties = GCPSqlInstanceProperties()
    sub_resource_relationship: ProjectToSqlInstanceRel = ProjectToSqlInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SqlInstanceToVpcRel(),
            SqlInstanceToServiceAccountRel(),
        ],
    )
