"""
AWS RDS cluster configuration hygiene

Storage encryption, deletion protection, backup rewinding, IAM authentication,
minor-version upgrades, Multi-AZ placement, listening ports and the master
username of the DB cluster itself. The CIS benchmark rules in
``cis_aws_storage`` cover DB instances only.

Every property used here is already synced by the AWS intel module; no
collector change is required. All rules are EXPERIMENTAL until validated
against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsRdsClusterBacktrackEnabledOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    cluster_arn: str | None = None
    cluster_id: str | None = None
    engine: str | None = None
    backtrack_window: str | None = None
    port: str | None = None
    default_port: str | None = None


_aws_rds_cluster_backtrack_enabled_fact = Fact(
    id="aws_rds_cluster_backtrack_enabled_fact",
    name="Aurora MySQL backtrack off",
    description="Aurora MySQL clusters with backtrack_window 0 or null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.engine = 'aurora-mysql'
          AND (c.backtrack_window IS NULL OR c.backtrack_window = 0)
        RETURN a.id AS account_id, a.name AS account,
               c.arn AS cluster_arn, c.db_cluster_identifier AS cluster_id,
               c.engine AS engine, c.backtrack_window AS backtrack_window

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.engine = 'aurora-mysql'
          AND (c.backtrack_window IS NULL OR c.backtrack_window = 0)
        RETURN a.id AS account_id, a.name AS account,
               c.arn AS cluster_arn, c.db_cluster_identifier AS cluster_id,
               c.engine AS engine, c.backtrack_window AS backtrack_window

    """,
    cypher_count_query="""
    MATCH (c:AWSRDSCluster) WHERE c.engine = 'aurora-mysql' RETURN COUNT(c) AS count
    """,
    asset_label="AWSRDSCluster",
    asset_id_field="cluster_arn",
    identity_fields=("account_id", "account", "cluster_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_cluster_backtrack_enabled = Rule(
    id="aws_rds_cluster_backtrack_enabled",
    name="Aurora MySQL Backtrack Disabled",
    description="Aurora MySQL cluster (engine='aurora-mysql') with backtrack_window = 0 or null, i.e. Backtrack disabled. Backtrack enables in-place rewind without a restore. Only meaningful for Aurora MySQL, so other engines are excluded.",
    output_model=AwsRdsClusterBacktrackEnabledOutput,
    facts=(_aws_rds_cluster_backtrack_enabled_fact,),
    tags=("rds", "resilience", "cspm", "low"),
    version="0.1.0",
)


class AwsRdsClusterDefaultAdminUsernameOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    cluster_arn: str | None = None
    cluster_identifier: str | None = None
    engine: str | None = None
    master_username: str | None = None
    deletion_protection: str | None = None
    multi_az: str | None = None


_aws_rds_cluster_default_admin_username_fact = Fact(
    id="aws_rds_cluster_default_admin_username_fact",
    name="RDS cluster default admin",
    description="Clusters whose master_username is 'admin' or 'postgres'.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.master_username IN ['admin', 'postgres']
        RETURN a.id AS account_id, a.name AS account, c.arn AS cluster_arn,
               c.db_cluster_identifier AS cluster_identifier, c.engine AS engine,
               c.master_username AS master_username

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.master_username IN ['admin', 'postgres']
        RETURN a.id AS account_id, a.name AS account, c.arn AS cluster_arn,
               c.db_cluster_identifier AS cluster_identifier, c.engine AS engine,
               c.master_username AS master_username

    """,
    cypher_count_query="""
    MATCH (c:AWSRDSCluster) RETURN COUNT(c) AS count
    """,
    asset_label="AWSRDSCluster",
    asset_id_field="cluster_arn",
    identity_fields=("account_id", "account", "cluster_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_cluster_default_admin_username = Rule(
    id="aws_rds_cluster_default_admin_username",
    name="RDS Cluster Default Admin Username",
    description="RDS cluster master username is a default/guessable admin name ('admin' or 'postgres').",
    output_model=AwsRdsClusterDefaultAdminUsernameOutput,
    facts=(_aws_rds_cluster_default_admin_username_fact,),
    tags=("security", "rds", "credentials", "cspm"),
    version="0.1.0",
)


class AwsRdsClusterDeletionProtectionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    cluster_arn: str | None = None
    cluster_identifier: str | None = None
    engine: str | None = None
    master_username: str | None = None
    deletion_protection: str | None = None
    multi_az: str | None = None


_aws_rds_cluster_deletion_protection_fact = Fact(
    id="aws_rds_cluster_deletion_protection_fact",
    name="RDS cluster deletion protection",
    description="Clusters with deletion_protection=false/null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.deletion_protection IS NULL OR c.deletion_protection = false
        RETURN a.id AS account_id, a.name AS account, c.arn AS cluster_arn,
               c.db_cluster_identifier AS cluster_identifier, c.engine AS engine,
               c.deletion_protection AS deletion_protection

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.deletion_protection IS NULL OR c.deletion_protection = false
        RETURN a.id AS account_id, a.name AS account, c.arn AS cluster_arn,
               c.db_cluster_identifier AS cluster_identifier, c.engine AS engine,
               c.deletion_protection AS deletion_protection

    """,
    cypher_count_query="""
    MATCH (c:AWSRDSCluster) RETURN COUNT(c) AS count
    """,
    asset_label="AWSRDSCluster",
    asset_id_field="cluster_arn",
    identity_fields=("account_id", "account", "cluster_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_cluster_deletion_protection = Rule(
    id="aws_rds_cluster_deletion_protection",
    name="RDS Cluster Deletion Protection",
    description="RDS cluster deletion protection is disabled (deletion_protection false or null).",
    output_model=AwsRdsClusterDeletionProtectionOutput,
    facts=(_aws_rds_cluster_deletion_protection_fact,),
    tags=("security", "rds", "resilience", "cspm"),
    version="0.1.0",
)


class AwsRdsClusterIamAuthOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    cluster_id: str | None = None
    cluster_arn: str | None = None
    cluster_identifier: str | None = None
    engine: str | None = None
    multi_az: str | None = None
    region: str | None = None


_aws_rds_cluster_iam_auth_fact = Fact(
    id="aws_rds_cluster_iam_auth_fact",
    name="RDS cluster member without IAM auth",
    description="Clusters with a member instance whose iam_database_authentication_enabled=false.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)<-[:IS_CLUSTER_MEMBER_OF]-(i:AWSRDSInstance)
        WHERE i.iam_database_authentication_enabled = false
        RETURN DISTINCT a.id AS account_id, a.name AS account, c.id AS cluster_id,
               c.arn AS cluster_arn, c.db_cluster_identifier AS cluster_identifier,
               c.engine AS engine, c.multi_az AS multi_az, c.region AS region

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)<-[:IS_CLUSTER_MEMBER_OF]-(i:AWSRDSInstance)
        WHERE i.iam_database_authentication_enabled = false
        RETURN DISTINCT a.id AS account_id, a.name AS account, c.id AS cluster_id,
               c.arn AS cluster_arn, c.db_cluster_identifier AS cluster_identifier,
               c.engine AS engine, c.multi_az AS multi_az, c.region AS region

    """,
    cypher_count_query="""
        MATCH (c:AWSRDSCluster)
        WHERE (:AWSRDSInstance)-[:IS_CLUSTER_MEMBER_OF]->(c)
        RETURN COUNT(c) AS count

    """,
    asset_label="AWSRDSCluster",
    asset_id_field="cluster_id",
    identity_fields=("account_id", "account", "cluster_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_cluster_iam_auth = Rule(
    id="aws_rds_cluster_iam_auth",
    name="RDS Cluster IAM Database Authentication Enabled",
    description="RDS cluster has at least one member instance with IAM database authentication disabled (iam_database_authentication_enabled=false). The cluster-level flag is not synced, so this is an instance-level proxy: strong for Aurora (the instance flag mirrors the cluster setting) and per-instance for Multi-AZ DB clusters. Clusters with no synced member instances are undetermined and excluded.",
    output_model=AwsRdsClusterIamAuthOutput,
    facts=(_aws_rds_cluster_iam_auth_fact,),
    tags=("security", "rds", "iam", "cspm"),
    version="0.1.0",
)


class AwsRdsClusterMinorUpgradeOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    cluster_id: str | None = None
    cluster_arn: str | None = None
    cluster_identifier: str | None = None
    engine: str | None = None
    multi_az: str | None = None
    region: str | None = None


_aws_rds_cluster_minor_upgrade_fact = Fact(
    id="aws_rds_cluster_minor_upgrade_fact",
    name="RDS cluster member without auto minor upgrade",
    description="Clusters with a member instance whose auto_minor_version_upgrade=false.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)<-[:IS_CLUSTER_MEMBER_OF]-(i:AWSRDSInstance)
        WHERE i.auto_minor_version_upgrade = false
        RETURN DISTINCT a.id AS account_id, a.name AS account, c.id AS cluster_id,
               c.arn AS cluster_arn, c.db_cluster_identifier AS cluster_identifier,
               c.engine AS engine, c.multi_az AS multi_az, c.region AS region

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)<-[:IS_CLUSTER_MEMBER_OF]-(i:AWSRDSInstance)
        WHERE i.auto_minor_version_upgrade = false
        RETURN DISTINCT a.id AS account_id, a.name AS account, c.id AS cluster_id,
               c.arn AS cluster_arn, c.db_cluster_identifier AS cluster_identifier,
               c.engine AS engine, c.multi_az AS multi_az, c.region AS region

    """,
    cypher_count_query="""
        MATCH (c:AWSRDSCluster)
        WHERE (:AWSRDSInstance)-[:IS_CLUSTER_MEMBER_OF]->(c)
        RETURN COUNT(c) AS count

    """,
    asset_label="AWSRDSCluster",
    asset_id_field="cluster_id",
    identity_fields=("account_id", "account", "cluster_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_cluster_minor_upgrade = Rule(
    id="aws_rds_cluster_minor_upgrade",
    name="RDS Cluster Auto Minor Version Upgrade Enabled",
    description="RDS cluster has at least one member instance with automatic minor version upgrades disabled (auto_minor_version_upgrade=false). The cluster-level flag is not synced; AutoMinorVersionUpgrade is an instance-level RDS attribute, so this instance-level proxy is close to exact for Multi-AZ DB clusters. Clusters with no synced member instances are undetermined and excluded.",
    output_model=AwsRdsClusterMinorUpgradeOutput,
    facts=(_aws_rds_cluster_minor_upgrade_fact,),
    tags=("security", "rds", "patching", "cspm"),
    version="0.1.0",
)


class AwsRdsClusterMultiAzOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    cluster_arn: str | None = None
    cluster_identifier: str | None = None
    engine: str | None = None
    master_username: str | None = None
    deletion_protection: str | None = None
    multi_az: str | None = None


_aws_rds_cluster_multi_az_fact = Fact(
    id="aws_rds_cluster_multi_az_fact",
    name="RDS cluster not Multi-AZ",
    description="mysql/postgres clusters with multi_az=false/null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.engine IN ['mysql', 'postgres']
          AND (c.multi_az IS NULL OR c.multi_az = false)
        RETURN a.id AS account_id, a.name AS account, c.arn AS cluster_arn,
               c.db_cluster_identifier AS cluster_identifier, c.engine AS engine,
               c.multi_az AS multi_az

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.engine IN ['mysql', 'postgres']
          AND (c.multi_az IS NULL OR c.multi_az = false)
        RETURN a.id AS account_id, a.name AS account, c.arn AS cluster_arn,
               c.db_cluster_identifier AS cluster_identifier, c.engine AS engine,
               c.multi_az AS multi_az

    """,
    cypher_count_query="""
    MATCH (c:AWSRDSCluster)
        WHERE c.engine IN ['mysql', 'postgres']
        RETURN COUNT(c) AS count
    """,
    asset_label="AWSRDSCluster",
    asset_id_field="cluster_arn",
    identity_fields=("account_id", "account", "cluster_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_cluster_multi_az = Rule(
    id="aws_rds_cluster_multi_az",
    name="RDS Cluster Multi-AZ",
    description="RDS Multi-AZ DB cluster has multi_az false or null. Evaluated only for engine mysql/postgres (the Multi-AZ DB cluster engines); Aurora clusters are inherently multi-AZ and do not report MultiAZ, so they are excluded. multi_az population is unverified (EXPERIMENTAL).",
    output_model=AwsRdsClusterMultiAzOutput,
    facts=(_aws_rds_cluster_multi_az_fact,),
    tags=("security", "rds", "resilience", "cspm"),
    version="0.1.0",
)


class AwsRdsClusterNonDefaultPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    cluster_arn: str | None = None
    cluster_id: str | None = None
    engine: str | None = None
    backtrack_window: str | None = None
    port: str | None = None
    default_port: str | None = None


_aws_rds_cluster_non_default_port_fact = Fact(
    id="aws_rds_cluster_non_default_port_fact",
    name="Cluster port equals engine default",
    description="Clusters whose port equals the mapped engine default port.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WITH a, c, CASE
            WHEN c.engine IN ['mysql', 'mariadb', 'aurora-mysql', 'aurora'] THEN 3306
            WHEN c.engine IN ['postgres', 'aurora-postgresql'] THEN 5432
            WHEN c.engine STARTS WITH 'sqlserver' THEN 1433
            WHEN c.engine STARTS WITH 'oracle' THEN 1521
            WHEN c.engine STARTS WITH 'db2' THEN 50000
            ELSE NULL
        END AS default_port
        WHERE c.port IS NOT NULL AND c.port = default_port
        RETURN a.id AS account_id, a.name AS account,
               c.arn AS cluster_arn, c.db_cluster_identifier AS cluster_id,
               c.engine AS engine, c.port AS port, default_port AS default_port

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WITH a, c, CASE
            WHEN c.engine IN ['mysql', 'mariadb', 'aurora-mysql', 'aurora'] THEN 3306
            WHEN c.engine IN ['postgres', 'aurora-postgresql'] THEN 5432
            WHEN c.engine STARTS WITH 'sqlserver' THEN 1433
            WHEN c.engine STARTS WITH 'oracle' THEN 1521
            WHEN c.engine STARTS WITH 'db2' THEN 50000
            ELSE NULL
        END AS default_port
        WHERE c.port IS NOT NULL AND c.port = default_port
        RETURN a.id AS account_id, a.name AS account,
               c.arn AS cluster_arn, c.db_cluster_identifier AS cluster_id,
               c.engine AS engine, c.port AS port, default_port AS default_port

    """,
    cypher_count_query="""
    MATCH (c:AWSRDSCluster) RETURN COUNT(c) AS count
    """,
    asset_label="AWSRDSCluster",
    asset_id_field="cluster_arn",
    identity_fields=("account_id", "account", "cluster_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_cluster_non_default_port = Rule(
    id="aws_rds_cluster_non_default_port",
    name="RDS Cluster On Default Engine Port",
    description="RDS cluster listening on its engine's default port (3306 MySQL/MariaDB/Aurora MySQL incl. legacy 'aurora', 5432 PostgreSQL/Aurora PostgreSQL, 1433 SQL Server, 1521 Oracle, 50000 DB2). Non-default ports reduce automated-scanner noise. Engines outside the mapping are not assessed.",
    output_model=AwsRdsClusterNonDefaultPortOutput,
    facts=(_aws_rds_cluster_non_default_port_fact,),
    tags=("rds", "hygiene", "cspm", "low"),
    version="0.1.0",
)


class AwsRdsClusterStorageEncryptedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    cluster_arn: str | None = None
    cluster_identifier: str | None = None
    engine: str | None = None
    storage_encrypted: str | None = None
    kms_key_id: str | None = None


_aws_rds_cluster_storage_encrypted_fact = Fact(
    id="aws_rds_cluster_storage_encrypted_fact",
    name="RDS cluster encryption",
    description="Clusters with storage_encrypted=false/null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.storage_encrypted IS NULL OR c.storage_encrypted = false
        RETURN a.id AS account_id, a.name AS account, c.arn AS cluster_arn,
               c.db_cluster_identifier AS cluster_identifier, c.engine AS engine,
               c.storage_encrypted AS storage_encrypted, c.kms_key_id AS kms_key_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(c:AWSRDSCluster)
        WHERE c.storage_encrypted IS NULL OR c.storage_encrypted = false
        RETURN a.id AS account_id, a.name AS account, c.arn AS cluster_arn,
               c.db_cluster_identifier AS cluster_identifier, c.engine AS engine,
               c.storage_encrypted AS storage_encrypted, c.kms_key_id AS kms_key_id

    """,
    cypher_count_query="""
    MATCH (c:AWSRDSCluster)
        RETURN COUNT(c) AS count, COUNT(c) AS total_assets,
               COUNT(CASE WHEN c.storage_encrypted IS NULL OR c.storage_encrypted = false THEN 1 END) AS failing
    """,
    asset_label="AWSRDSCluster",
    asset_id_field="cluster_arn",
    identity_fields=("cluster_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_rds_cluster_storage_encrypted = Rule(
    id="aws_rds_cluster_storage_encrypted",
    name="RDS Cluster Storage Encrypted",
    description="RDS cluster storage is not encrypted (storage_encrypted false or null). The built-in aws_rds_encryption_at_rest covers instances only; this is the cluster delta.",
    output_model=AwsRdsClusterStorageEncryptedOutput,
    facts=(_aws_rds_cluster_storage_encrypted_fact,),
    tags=("security", "rds", "encryption", "cspm"),
    version="0.1.0",
)
