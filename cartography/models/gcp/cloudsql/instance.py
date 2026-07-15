import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPSqlInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "selfLink",
        description="Canonical Cloud SQL instance selfLink used as the node ID.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="The user-assigned name of the instance."
    )
    database_version: PropertyRef = PropertyRef(
        "databaseVersion",
        description="Cloud SQL database engine and major version reported by the API.",
    )
    database_engine: PropertyRef = PropertyRef(
        "database_engine",
        description="Database engine family derived from database_version, such as MYSQL, POSTGRES, or SQLSERVER.",
    )
    region: PropertyRef = PropertyRef(
        "region", description="The GCP region the instance lives in."
    )
    gce_zone: PropertyRef = PropertyRef(
        "gceZone",
        description="Compute Engine zone hosting the primary Cloud SQL instance, when zonal.",
    )
    state: PropertyRef = PropertyRef(
        "state", description="The current state of the instance (e.g., `RUNNABLE`)."
    )
    backend_type: PropertyRef = PropertyRef(
        "backendType",
        description="Cloud SQL backend type reported for the instance.",
    )
    network_id: PropertyRef = PropertyRef(
        "network_id",
        description="Project-relative URI of the private VPC network attached to the instance.",
    )
    service_account_email: PropertyRef = PropertyRef(
        "service_account_email",
        description="Google-managed service account used by the Cloud SQL instance.",
    )
    connection_name: PropertyRef = PropertyRef(
        "connectionName",
        description="Cloud SQL connection name in project:region:instance form.",
    )
    tier: PropertyRef = PropertyRef(
        "tier", description="The machine type tier (e.g., `db-custom-1-3840`)."
    )
    disk_size_gb: PropertyRef = PropertyRef(
        "disk_size_gb",
        description=(
            "Provisioned data disk capacity in gigabytes, derived from "
            "settings.dataDiskSizeGb."
        ),
    )
    disk_type: PropertyRef = PropertyRef(
        "disk_type",
        description="Cloud SQL data disk type, such as PD_SSD or PD_HDD.",
    )
    availability_type: PropertyRef = PropertyRef(
        "availability_type",
        description="Instance availability topology, such as ZONAL or REGIONAL.",
    )
    backup_enabled: PropertyRef = PropertyRef(
        "backup_enabled",
        description="Whether automated backups are enabled in the instance settings.",
    )
    require_ssl: PropertyRef = PropertyRef(
        "require_ssl",
        description="Whether the instance rejects unencrypted client connections.",
    )
    ssl_mode: PropertyRef = PropertyRef(
        "ssl_mode",
        description="Configured Cloud SQL transport-encryption policy.",
    )
    ip_addresses: PropertyRef = PropertyRef(
        "ip_addresses",
        description="Instance IP assignments encoded as JSON, including address and assignment type.",
    )
    authorized_networks: PropertyRef = PropertyRef(
        "authorized_networks",
        description="Authorized client network entries encoded as JSON from ipConfiguration.authorizedNetworks.",
    )
    backup_configuration: PropertyRef = PropertyRef(
        "backup_configuration",
        description="Cloud SQL backup configuration encoded as JSON.",
    )
    database_flags: PropertyRef = PropertyRef(
        "database_flags",
        description="Configured database flags encoded as JSON name-value entries.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class ProjectToSqlInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """Representation of a GCP [Cloud SQL Instance](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/instances)."""

    label: str = "GCPCloudSQLInstance"
    properties: GCPSqlInstanceProperties = GCPSqlInstanceProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    sub_resource_relationship: ProjectToSqlInstanceRel = ProjectToSqlInstanceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SqlInstanceToVpcRel(),
            SqlInstanceToServiceAccountRel(),
        ],
    )
