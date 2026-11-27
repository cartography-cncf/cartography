"""
AWS RDS instance and snapshot configuration hygiene

Deletion protection, enhanced monitoring, IAM authentication, minor-version
upgrades, Multi-AZ placement, subnet-group placement, listening ports, the
master username, and encryption of instance snapshots. Encryption of instance
storage and public accessibility are already covered by ``cis_aws_storage``.

Every property used here is already synced by the AWS intel module; no
collector change is required. All rules are EXPERIMENTAL until validated
against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsRdsInstanceAutoMinorVersionUpgradeOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    db_identifier: str | None = None
    engine: str | None = None
    db_cluster_identifier: str | None = None
    master_username: str | None = None
    backup_retention_period: str | None = None
    deletion_protection: str | None = None
    cluster_identifier: str | None = None
    cluster_deletion_protection: str | None = None
    iam_database_authentication_enabled: str | None = None
    auto_minor_version_upgrade: str | None = None
    multi_az: str | None = None


_aws_rds_instance_auto_minor_version_upgrade_fact = Fact(
    id="aws_rds_instance_auto_minor_version_upgrade_fact",
    name="RDS instance auto minor upgrade disabled",
    description="Instances with auto_minor_version_upgrade=false.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.auto_minor_version_upgrade = false
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier, i.engine AS engine,
               i.auto_minor_version_upgrade AS auto_minor_version_upgrade

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.auto_minor_version_upgrade = false
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier, i.engine AS engine,
               i.auto_minor_version_upgrade AS auto_minor_version_upgrade

    """,
    cypher_count_query="""
    MATCH (i:AWSRDSInstance) RETURN COUNT(i) AS count
    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "account", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_instance_auto_minor_version_upgrade = Rule(
    id="aws_rds_instance_auto_minor_version_upgrade",
    name="RDS Instance Auto Minor Version Upgrade",
    description="RDS instance has automatic minor version upgrades disabled (auto_minor_version_upgrade=false). Strict false per the spec predicate: null is not flagged because sync population of the field is unverified (upstream CIS 3.2.2 TODO claims it is missing). Verify populated in the live graph before promotion.",
    output_model=AwsRdsInstanceAutoMinorVersionUpgradeOutput,
    facts=(_aws_rds_instance_auto_minor_version_upgrade_fact,),
    tags=("security", "rds", "patching", "cspm"),
    version="0.1.0",
)


class AwsRdsInstanceDefaultAdminUsernameOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    db_identifier: str | None = None
    engine: str | None = None
    db_cluster_identifier: str | None = None
    master_username: str | None = None
    backup_retention_period: str | None = None
    deletion_protection: str | None = None
    cluster_identifier: str | None = None
    cluster_deletion_protection: str | None = None
    iam_database_authentication_enabled: str | None = None
    auto_minor_version_upgrade: str | None = None
    multi_az: str | None = None


_aws_rds_instance_default_admin_username_fact = Fact(
    id="aws_rds_instance_default_admin_username_fact",
    name="RDS instance default admin",
    description="Instances whose master_username is 'admin' or 'postgres'.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.master_username IN ['admin', 'postgres']
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier, i.engine AS engine,
               i.master_username AS master_username

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.master_username IN ['admin', 'postgres']
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier, i.engine AS engine,
               i.master_username AS master_username

    """,
    cypher_count_query="""
    MATCH (i:AWSRDSInstance) RETURN COUNT(i) AS count
    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "account", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_instance_default_admin_username = Rule(
    id="aws_rds_instance_default_admin_username",
    name="RDS Instance Default Admin Username",
    description="RDS instance master username is a default/guessable admin name ('admin' or 'postgres').",
    output_model=AwsRdsInstanceDefaultAdminUsernameOutput,
    facts=(_aws_rds_instance_default_admin_username_fact,),
    tags=("security", "rds", "credentials", "cspm"),
    version="0.1.0",
)


class AwsRdsInstanceDeletionProtectionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    db_identifier: str | None = None
    engine: str | None = None
    db_cluster_identifier: str | None = None
    master_username: str | None = None
    backup_retention_period: str | None = None
    deletion_protection: str | None = None
    cluster_identifier: str | None = None
    cluster_deletion_protection: str | None = None
    iam_database_authentication_enabled: str | None = None
    auto_minor_version_upgrade: str | None = None
    multi_az: str | None = None


_aws_rds_instance_deletion_protection_fact = Fact(
    id="aws_rds_instance_deletion_protection_fact",
    name="RDS instance deletion protection",
    description="Instances with deletion_protection=false/null whose parent cluster (if any) also lacks deletion protection.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        OPTIONAL MATCH (i)-[:IS_CLUSTER_MEMBER_OF]->(c:AWSRDSCluster)
        WITH a, i, c
        WHERE coalesce(i.deletion_protection, false) = false
          AND (c IS NULL OR coalesce(c.deletion_protection, false) = false)
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier,
               i.db_cluster_identifier AS db_cluster_identifier,
               i.deletion_protection AS deletion_protection,
               c.db_cluster_identifier AS cluster_identifier,
               c.deletion_protection AS cluster_deletion_protection

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        OPTIONAL MATCH (i)-[:IS_CLUSTER_MEMBER_OF]->(c:AWSRDSCluster)
        WITH a, i, c
        WHERE coalesce(i.deletion_protection, false) = false
          AND (c IS NULL OR coalesce(c.deletion_protection, false) = false)
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier,
               i.db_cluster_identifier AS db_cluster_identifier,
               i.deletion_protection AS deletion_protection,
               c.db_cluster_identifier AS cluster_identifier,
               c.deletion_protection AS cluster_deletion_protection

    """,
    cypher_count_query="""
    MATCH (i:AWSRDSInstance) RETURN COUNT(i) AS count
    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_id",
    identity_fields=(
        "account_id",
        "account",
        "instance_id",
        "cluster_identifier",
        "cluster_deletion_protection",
    ),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_instance_deletion_protection = Rule(
    id="aws_rds_instance_deletion_protection",
    name="RDS Instance Deletion Protection",
    description="RDS instance deletion protection is disabled (deletion_protection false or null). For cluster members the parent cluster's deletion_protection is also evaluated via IS_CLUSTER_MEMBER_OF: a member passes when its cluster has deletion protection enabled.",
    output_model=AwsRdsInstanceDeletionProtectionOutput,
    facts=(_aws_rds_instance_deletion_protection_fact,),
    tags=("security", "rds", "resilience", "cspm"),
    version="0.1.0",
)


class AwsRdsInstanceEnhancedMonitoringOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_arn: str | None = None
    instance_id: str | None = None
    engine: str | None = None
    enhanced_monitoring_resource_arn: str | None = None
    monitoring_role_arn: str | None = None
    endpoint_port: str | None = None
    default_port: str | None = None


_aws_rds_instance_enhanced_monitoring_fact = Fact(
    id="aws_rds_instance_enhanced_monitoring_fact",
    name="RDS enhanced monitoring off",
    description="Instances with null/empty enhanced_monitoring_resource_arn.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.enhanced_monitoring_resource_arn IS NULL
           OR i.enhanced_monitoring_resource_arn = ''
        RETURN a.id AS account_id, a.name AS account,
               i.arn AS instance_arn, i.db_instance_identifier AS instance_id,
               i.engine AS engine,
               i.enhanced_monitoring_resource_arn AS enhanced_monitoring_resource_arn,
               i.monitoring_role_arn AS monitoring_role_arn

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.enhanced_monitoring_resource_arn IS NULL
           OR i.enhanced_monitoring_resource_arn = ''
        RETURN a.id AS account_id, a.name AS account,
               i.arn AS instance_arn, i.db_instance_identifier AS instance_id,
               i.engine AS engine,
               i.enhanced_monitoring_resource_arn AS enhanced_monitoring_resource_arn,
               i.monitoring_role_arn AS monitoring_role_arn

    """,
    cypher_count_query="""
    MATCH (i:AWSRDSInstance) RETURN COUNT(i) AS count
    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_arn",
    identity_fields=("account_id", "account", "instance_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_instance_enhanced_monitoring = Rule(
    id="aws_rds_instance_enhanced_monitoring",
    name="RDS Enhanced Monitoring Disabled",
    description="RDS instance without Enhanced Monitoring: enhanced_monitoring_resource_arn is null or empty (the ARN is only present when the monitoring interval is > 0). Enhanced Monitoring provides OS-level metrics for troubleshooting.",
    output_model=AwsRdsInstanceEnhancedMonitoringOutput,
    facts=(_aws_rds_instance_enhanced_monitoring_fact,),
    tags=("rds", "observability", "cspm", "low"),
    version="0.1.0",
)


class AwsRdsInstanceIamAuthenticationOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    db_identifier: str | None = None
    engine: str | None = None
    db_cluster_identifier: str | None = None
    master_username: str | None = None
    backup_retention_period: str | None = None
    deletion_protection: str | None = None
    cluster_identifier: str | None = None
    cluster_deletion_protection: str | None = None
    iam_database_authentication_enabled: str | None = None
    auto_minor_version_upgrade: str | None = None
    multi_az: str | None = None


_aws_rds_instance_iam_authentication_fact = Fact(
    id="aws_rds_instance_iam_authentication_fact",
    name="RDS instance IAM auth disabled",
    description="Supported-engine instances with iam_database_authentication_enabled=false/null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.engine IN ['mysql', 'mariadb', 'postgres', 'aurora', 'aurora-mysql', 'aurora-postgresql']
          AND (i.iam_database_authentication_enabled IS NULL
               OR i.iam_database_authentication_enabled = false)
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier, i.engine AS engine,
               i.iam_database_authentication_enabled AS iam_database_authentication_enabled

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.engine IN ['mysql', 'mariadb', 'postgres', 'aurora', 'aurora-mysql', 'aurora-postgresql']
          AND (i.iam_database_authentication_enabled IS NULL
               OR i.iam_database_authentication_enabled = false)
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier, i.engine AS engine,
               i.iam_database_authentication_enabled AS iam_database_authentication_enabled

    """,
    cypher_count_query="""
    MATCH (i:AWSRDSInstance)
        WHERE i.engine IN ['mysql', 'mariadb', 'postgres', 'aurora', 'aurora-mysql', 'aurora-postgresql']
        RETURN COUNT(i) AS count
    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "account", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_instance_iam_authentication = Rule(
    id="aws_rds_instance_iam_authentication",
    name="RDS Instance IAM Authentication",
    description="RDS instance on an IAM-authentication-capable engine (mysql, mariadb, postgres, aurora, aurora-mysql, aurora-postgresql) has iam_database_authentication_enabled false or null. Other engines do not support IAM database authentication and are excluded.",
    output_model=AwsRdsInstanceIamAuthenticationOutput,
    facts=(_aws_rds_instance_iam_authentication_fact,),
    tags=("security", "rds", "authentication", "cspm"),
    version="0.1.0",
)


class AwsRdsInstanceInsideVpcOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    db_identifier: str | None = None
    engine: str | None = None
    subnet_group: str | None = None
    vpc_id: str | None = None


_aws_rds_instance_inside_vpc_fact = Fact(
    id="aws_rds_instance_inside_vpc_fact",
    name="RDS instance outside VPC",
    description="Instances without a DB subnet group, or whose group has no vpc_id.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(rds:AWSRDSInstance)
        OPTIONAL MATCH (rds)-[:MEMBER_OF_DB_SUBNET_GROUP]->(sg:AWSDBSubnetGroup)
        WITH a, rds, sg
        WHERE sg IS NULL OR sg.vpc_id IS NULL
        RETURN a.id AS account_id, a.name AS account, rds.id AS instance_id,
               rds.db_instance_identifier AS db_identifier, rds.engine AS engine,
               sg.name AS subnet_group, sg.vpc_id AS vpc_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(rds:AWSRDSInstance)
        OPTIONAL MATCH (rds)-[:MEMBER_OF_DB_SUBNET_GROUP]->(sg:AWSDBSubnetGroup)
        WITH a, rds, sg
        WHERE sg IS NULL OR sg.vpc_id IS NULL
        RETURN a.id AS account_id, a.name AS account, rds.id AS instance_id,
               rds.db_instance_identifier AS db_identifier, rds.engine AS engine,
               sg.name AS subnet_group, sg.vpc_id AS vpc_id

    """,
    cypher_count_query="""
        MATCH (rds:AWSRDSInstance)
        OPTIONAL MATCH (rds)-[:MEMBER_OF_DB_SUBNET_GROUP]->(sg:AWSDBSubnetGroup)
        WITH rds, sg
        RETURN COUNT(rds) AS count, COUNT(rds) AS total_assets,
               COUNT(CASE WHEN sg IS NULL OR sg.vpc_id IS NULL THEN 1 END) AS failing

    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "account", "instance_id", "subnet_group", "vpc_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_instance_inside_vpc = Rule(
    id="aws_rds_instance_inside_vpc",
    name="RDS Instance Deployed In VPC",
    description="RDS instance is not deployed in a VPC (EC2-Classic): it has no MEMBER_OF_DB_SUBNET_GROUP link to an AWSDBSubnetGroup with a non-null vpc_id. The instance node carries no vpc_id; VPC membership is resolved via the DB subnet group.",
    output_model=AwsRdsInstanceInsideVpcOutput,
    facts=(_aws_rds_instance_inside_vpc_fact,),
    tags=("security", "rds", "network", "cspm"),
    version="0.1.0",
)


class AwsRdsInstanceMultiAzOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_id: str | None = None
    db_identifier: str | None = None
    engine: str | None = None
    db_cluster_identifier: str | None = None
    master_username: str | None = None
    backup_retention_period: str | None = None
    deletion_protection: str | None = None
    cluster_identifier: str | None = None
    cluster_deletion_protection: str | None = None
    iam_database_authentication_enabled: str | None = None
    auto_minor_version_upgrade: str | None = None
    multi_az: str | None = None


_aws_rds_instance_multi_az_fact = Fact(
    id="aws_rds_instance_multi_az_fact",
    name="RDS instance not Multi-AZ",
    description="Instances with multi_az=false.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.multi_az = false
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier, i.engine AS engine,
               i.multi_az AS multi_az

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WHERE i.multi_az = false
        RETURN a.id AS account_id, a.name AS account, i.id AS instance_id,
               i.db_instance_identifier AS db_identifier, i.engine AS engine,
               i.multi_az AS multi_az

    """,
    cypher_count_query="""
    MATCH (i:AWSRDSInstance) RETURN COUNT(i) AS count
    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_id",
    identity_fields=("account_id", "account", "instance_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_instance_multi_az = Rule(
    id="aws_rds_instance_multi_az",
    name="RDS Instance Multi-AZ",
    description="RDS instance is not a Multi-AZ deployment (multi_az=false). Strict false per the spec predicate: null is not flagged because sync population of the field is unverified (upstream CIS 3.2.4 TODO claims it is missing). Aurora cluster members may report multi_az=false despite cluster-level multi-AZ storage; they are not excluded, per the spec predicate.",
    output_model=AwsRdsInstanceMultiAzOutput,
    facts=(_aws_rds_instance_multi_az_fact,),
    tags=("security", "rds", "resilience", "cspm"),
    version="0.1.0",
)


class AwsRdsInstanceNonDefaultPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    instance_arn: str | None = None
    instance_id: str | None = None
    engine: str | None = None
    enhanced_monitoring_resource_arn: str | None = None
    monitoring_role_arn: str | None = None
    endpoint_port: str | None = None
    default_port: str | None = None


_aws_rds_instance_non_default_port_fact = Fact(
    id="aws_rds_instance_non_default_port_fact",
    name="Instance port equals engine default",
    description="Instances whose endpoint_port equals the mapped engine default port.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WITH a, i, CASE
            WHEN i.engine IN ['mysql', 'mariadb', 'aurora-mysql', 'aurora'] THEN 3306
            WHEN i.engine IN ['postgres', 'aurora-postgresql'] THEN 5432
            WHEN i.engine STARTS WITH 'sqlserver' THEN 1433
            WHEN i.engine STARTS WITH 'oracle' THEN 1521
            WHEN i.engine STARTS WITH 'db2' THEN 50000
            ELSE NULL
        END AS default_port
        WHERE i.endpoint_port IS NOT NULL AND i.endpoint_port = default_port
        RETURN a.id AS account_id, a.name AS account,
               i.arn AS instance_arn, i.db_instance_identifier AS instance_id,
               i.engine AS engine, i.endpoint_port AS endpoint_port,
               default_port AS default_port

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(i:AWSRDSInstance)
        WITH a, i, CASE
            WHEN i.engine IN ['mysql', 'mariadb', 'aurora-mysql', 'aurora'] THEN 3306
            WHEN i.engine IN ['postgres', 'aurora-postgresql'] THEN 5432
            WHEN i.engine STARTS WITH 'sqlserver' THEN 1433
            WHEN i.engine STARTS WITH 'oracle' THEN 1521
            WHEN i.engine STARTS WITH 'db2' THEN 50000
            ELSE NULL
        END AS default_port
        WHERE i.endpoint_port IS NOT NULL AND i.endpoint_port = default_port
        RETURN a.id AS account_id, a.name AS account,
               i.arn AS instance_arn, i.db_instance_identifier AS instance_id,
               i.engine AS engine, i.endpoint_port AS endpoint_port,
               default_port AS default_port

    """,
    cypher_count_query="""
    MATCH (i:AWSRDSInstance) RETURN COUNT(i) AS count
    """,
    asset_label="AWSRDSInstance",
    asset_id_field="instance_arn",
    identity_fields=("account_id", "account", "instance_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_instance_non_default_port = Rule(
    id="aws_rds_instance_non_default_port",
    name="RDS Instance On Default Engine Port",
    description="RDS instance whose endpoint_port equals its engine's default port (3306 MySQL/MariaDB/Aurora MySQL incl. legacy 'aurora', 5432 PostgreSQL/Aurora PostgreSQL, 1433 SQL Server, 1521 Oracle, 50000 DB2). Non-default ports reduce automated-scanner noise. Engines outside the mapping are not assessed.",
    output_model=AwsRdsInstanceNonDefaultPortOutput,
    facts=(_aws_rds_instance_non_default_port_fact,),
    tags=("rds", "hygiene", "cspm", "low"),
    version="0.1.0",
)


class AwsRdsSnapshotEncryptedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    snapshot_arn: str | None = None
    snapshot_identifier: str | None = None
    source_instance: str | None = None
    snapshot_type: str | None = None
    encrypted: str | None = None
    kms_key_id: str | None = None


_aws_rds_snapshot_encrypted_fact = Fact(
    id="aws_rds_snapshot_encrypted_fact",
    name="RDS snapshot encryption",
    description="DB instance snapshots with encrypted=false/null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSRDSSnapshot)
        WHERE s.encrypted IS NULL OR s.encrypted = false
        RETURN a.id AS account_id, a.name AS account, s.arn AS snapshot_arn,
               s.db_snapshot_identifier AS snapshot_identifier,
               s.db_instance_identifier AS source_instance,
               s.snapshot_type AS snapshot_type, s.encrypted AS encrypted,
               s.kms_key_id AS kms_key_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSRDSSnapshot)
        WHERE s.encrypted IS NULL OR s.encrypted = false
        RETURN a.id AS account_id, a.name AS account, s.arn AS snapshot_arn,
               s.db_snapshot_identifier AS snapshot_identifier,
               s.db_instance_identifier AS source_instance,
               s.snapshot_type AS snapshot_type, s.encrypted AS encrypted,
               s.kms_key_id AS kms_key_id

    """,
    cypher_count_query="""
    MATCH (s:AWSRDSSnapshot)
        RETURN COUNT(s) AS count, COUNT(s) AS total_assets,
               COUNT(CASE WHEN s.encrypted IS NULL OR s.encrypted = false THEN 1 END) AS failing
    """,
    asset_label="AWSRDSSnapshot",
    asset_id_field="snapshot_arn",
    identity_fields=("snapshot_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_snapshot_encrypted = Rule(
    id="aws_rds_snapshot_encrypted",
    name="RDS Snapshot Encrypted",
    description="RDS DB instance snapshot is not encrypted (encrypted false or null). DB cluster snapshots have no node label in cartography (not synced), so cluster-snapshot encryption is out of graph scope.",
    output_model=AwsRdsSnapshotEncryptedOutput,
    facts=(_aws_rds_snapshot_encrypted_fact,),
    tags=("security", "rds", "encryption", "cspm"),
    version="0.1.0",
)
