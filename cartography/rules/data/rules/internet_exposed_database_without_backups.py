from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

_aws_public_rds_without_backups = Fact(
    id="aws_public_rds_without_backups",
    name="Internet-exposed RDS instances without backups",
    description=(
        "RDS instances that are publicly reachable through a 0.0.0.0/0 "
        "security-group path and have automated backup retention disabled."
    ),
    cypher_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(rds:RDSInstance {publicly_accessible: true})
    WHERE rds.endpoint_port IS NOT NULL
      AND coalesce(rds.backup_retention_period, 0) = 0
    MATCH (rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
        <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(:AWSIpRange {range: '0.0.0.0/0'})
    WHERE coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
      AND (
        rule.fromport IS NULL
        OR (
          coalesce(rule.fromport, 0) <= rds.endpoint_port
          AND coalesce(rule.toport, rule.fromport, 0) >= rds.endpoint_port
        )
      )
    RETURN DISTINCT
        rds.id AS id,
        rds.db_instance_identifier AS name,
        account.name AS account,
        account.id AS account_id,
        rds.region AS region,
        'aws' AS provider,
        rds.engine AS engine,
        rds.endpoint_address AS host,
        rds.endpoint_port AS port,
        rds.backup_retention_period AS backup_retention_days,
        rds.deletion_protection AS deletion_protection
    ORDER BY account, region, name
    """,
    cypher_visual_query="""
    MATCH p1=(account:AWSAccount)-[:RESOURCE]->(rds:RDSInstance {publicly_accessible: true})
    MATCH p2=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
        <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
    MATCH p3=(rule)<-[:MEMBER_OF_IP_RULE]-(:AWSIpRange {range: '0.0.0.0/0'})
    WHERE rds.endpoint_port IS NOT NULL
      AND coalesce(rds.backup_retention_period, 0) = 0
      AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
      AND (
        rule.fromport IS NULL
        OR (
          coalesce(rule.fromport, 0) <= rds.endpoint_port
          AND coalesce(rule.toport, rule.fromport, 0) >= rds.endpoint_port
        )
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (rds:RDSInstance)
    RETURN COUNT(rds) AS count
    """,
    asset_id_field="id",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)

_gcp_public_cloudsql_without_backups = Fact(
    id="gcp_public_cloudsql_without_backups",
    name="Internet-exposed Cloud SQL instances without backups",
    description=(
        "Cloud SQL instances that allow inbound connections from 0.0.0.0/0 "
        "and have automated backups disabled."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(sql:GCPCloudSQLInstance)
    MATCH (sql)-[:AUTHORIZED_NETWORK]-(net:GCPCloudSQLAuthorizedNetwork)
    WHERE net.value = '0.0.0.0/0'
      AND coalesce(sql.backup_enabled, false) = false
    RETURN DISTINCT
        sql.id AS id,
        sql.name AS name,
        project.id AS account,
        project.id AS account_id,
        sql.region AS region,
        'gcp' AS provider,
        sql.database_version AS engine,
        sql.connection_name AS host,
        null AS port,
        null AS backup_retention_days,
        null AS deletion_protection
    ORDER BY account, region, name
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(sql:GCPCloudSQLInstance)
          -[:AUTHORIZED_NETWORK]-(net:GCPCloudSQLAuthorizedNetwork)
    WHERE net.value = '0.0.0.0/0'
      AND coalesce(sql.backup_enabled, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sql:GCPCloudSQLInstance)
    RETURN COUNT(sql) AS count
    """,
    asset_id_field="id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


class InternetExposedDatabaseWithoutBackups(Finding):
    id: str | None = None
    name: str | None = None
    account: str | None = None
    account_id: str | None = None
    region: str | None = None
    provider: str | None = None
    engine: str | None = None
    host: str | None = None
    port: int | None = None
    backup_retention_days: int | None = None
    deletion_protection: bool | None = None


internet_exposed_database_without_backups = Rule(
    id="internet_exposed_database_without_backups",
    name="Internet-Exposed Databases Without Backups",
    description=(
        "Databases reachable from the public internet where the graph also "
        "shows automated backups are disabled. This combines exposure with "
        "recovery blast radius rather than reporting backup posture alone."
    ),
    output_model=InternetExposedDatabaseWithoutBackups,
    facts=(
        _aws_public_rds_without_backups,
        _gcp_public_cloudsql_without_backups,
    ),
    tags=(
        "data",
        "database",
        "attack_surface",
        "resilience",
        "stride:information_disclosure",
        "stride:tampering",
    ),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.13"),
        iso27001_annex_a("8.14"),
        iso27001_annex_a("8.20"),
    ),
)
