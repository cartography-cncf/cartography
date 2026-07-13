from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Azure Facts
# Only the public-internet exposure class belongs in this rule. The special
# Azure SQL `start_ip=end_ip=0.0.0.0` "Allow Azure services" row is a
# different exposure class (per Microsoft's documentation) and should be
# tracked under a dedicated rule, not lumped here.
_azure_sql_internet_exposed = Fact(
    id="azure_sql_internet_exposed",
    name="Internet-Accessible Azure SQL Server Attack Surface",
    description=(
        "Azure SQL Servers reachable from the public internet. Triggered "
        "when public_network_access = 'Enabled' and a firewall rule allows "
        "traffic from public IP space (start_ip=0.0.0.0, end_ip is set and "
        "not also 0.0.0.0)."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(server:AzureSQLServer)
    MATCH (rule:AzureSQLServerFirewallRule)-[:MEMBER_OF_AZURE_SQL_SERVER]->(server)
    WHERE coalesce(server.public_network_access, 'Enabled') = 'Enabled'
      AND rule.start_ip_address = '0.0.0.0'
      AND rule.end_ip_address IS NOT NULL
      AND rule.end_ip_address <> '0.0.0.0'
    RETURN DISTINCT
        server.id AS id,
        server.name AS host,
        'Microsoft.Sql' AS engine,
        1433 AS port,
        server.location AS region
    """,
    cypher_visual_query="""
    MATCH p=(sub:AzureSubscription)-[:RESOURCE]->(server:AzureSQLServer)<-[:MEMBER_OF_AZURE_SQL_SERVER]-(rule:AzureSQLServerFirewallRule)
    WHERE coalesce(server.public_network_access, 'Enabled') = 'Enabled'
      AND rule.start_ip_address = '0.0.0.0'
      AND rule.end_ip_address IS NOT NULL
      AND rule.end_ip_address <> '0.0.0.0'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (server:AzureSQLServer)
    RETURN COUNT(server) AS count
    """,
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


_azure_cosmosdb_public_access = Fact(
    id="azure_cosmosdb_public_access",
    name="Internet-Accessible Azure Cosmos DB Account",
    description=(
        "Azure Cosmos DB accounts with publicnetworkaccess = 'Enabled' and "
        "no IP allowlist or VNet filter, leaving the account reachable from "
        "any public IP. The intel layer normalises ipruleslist into a list "
        "(possibly empty), so the empty-list case is the no-allowlist "
        "signal here."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(account:AzureCosmosDBAccount)
    WHERE account.publicnetworkaccess = 'Enabled'
      AND coalesce(account.virtualnetworkfilterenabled, false) = false
      AND size(coalesce(account.ipranges, [])) = 0
    RETURN
        account.id AS id,
        account.documentendpoint AS host,
        coalesce(account.kind, 'Microsoft.DocumentDB') AS engine,
        account.location AS region
    """,
    cypher_visual_query="""
    MATCH p=(sub:AzureSubscription)-[:RESOURCE]->(account:AzureCosmosDBAccount)
    WHERE account.publicnetworkaccess = 'Enabled'
      AND coalesce(account.virtualnetworkfilterenabled, false) = false
      AND size(coalesce(account.ipranges, [])) = 0
    RETURN *
    """,
    cypher_count_query="""
    MATCH (account:AzureCosmosDBAccount)
    RETURN COUNT(account) AS count
    """,
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


# GCP Facts
_gcp_cloud_sql_public_access = Fact(
    id="gcp_cloud_sql_public_access",
    name="Internet-Accessible Cloud SQL Database Attack Surface",
    description=(
        "GCP Cloud SQL instances that allow inbound connections from any IP "
        "(authorized network 0.0.0.0/0)."
    ),
    cypher_query="""
    MATCH (sql:GCPCloudSQLInstance)-[:AUTHORIZED_NETWORK]-(net:GCPCloudSQLAuthorizedNetwork)
    WHERE net.value = '0.0.0.0/0'
    RETURN DISTINCT
        sql.id AS id,
        sql.database_version AS engine,
        sql.connection_name AS host,
        sql.region AS region,
        sql.require_ssl AS encrypted
    """,
    cypher_visual_query="""
    MATCH p=(sql:GCPCloudSQLInstance)-[:AUTHORIZED_NETWORK]-(net:GCPCloudSQLAuthorizedNetwork)
    WHERE net.value = '0.0.0.0/0'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sql:GCPCloudSQLInstance)
    RETURN COUNT(sql) AS count
    """,
    identity_fields=("id",),
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


# AWS Facts
_aws_rds_public_access = Fact(
    id="aws_rds_public_access",
    name="Internet-Accessible RDS Database Attack Surface",
    description=(
        "AWS RDS instances reachable from the public internet. The DB must "
        "have publicly_accessible = true AND at least one attached security "
        "group with an inbound rule permitting 0.0.0.0/0 over TCP "
        "(or `-1` / `all` covering every protocol) on a port range that "
        "covers the DB's endpoint_port. Either flag alone is not sufficient "
        "for actual public reachability, and a UDP-only wide-open rule does "
        "not expose the TCP DB port."
    ),
    cypher_query="""
    MATCH (rds:AWSRDSInstance {publicly_accessible: true})
    WHERE rds.endpoint_port IS NOT NULL
    MATCH (rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)
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
        rds.engine AS engine,
        rds.db_instance_class AS instance_class,
        rds.endpoint_address AS host,
        rds.endpoint_port AS port,
        rds.region AS region,
        rds.storage_encrypted AS encrypted
    """,
    cypher_visual_query="""
    MATCH p1=(rds:AWSRDSInstance {publicly_accessible: true})
    MATCH p2=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:AWSEC2SecurityGroup)
        <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound:AWSIpRule)
    MATCH p3=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange {range: '0.0.0.0/0'})
    WHERE rds.endpoint_port IS NOT NULL
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
    MATCH (rds:AWSRDSInstance)
    RETURN COUNT(rds) AS count
    """,
    identity_fields=("id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Scaleway Facts
# Scaleway managed databases expose an `is_public` flag that the intel layer
# derives from the endpoints list: it is true when the instance has a
# load-balancer or direct-access endpoint, i.e. a routable public endpoint.
# That single flag is the internet-reachability signal here (no separate
# firewall layer to join, unlike AWS/GCP).
_scaleway_rdb_public_access = Fact(
    id="scaleway_rdb_public_access",
    name="Internet-Accessible Scaleway Managed Database Attack Surface",
    description=(
        "Scaleway Managed Databases for PostgreSQL / MySQL (RDB) that expose "
        "a public endpoint (is_public = true), reachable from the internet."
    ),
    cypher_query="""
    MATCH (prj:ScalewayProject)-[:RESOURCE]->(db:ScalewayRdbInstance)
    WHERE db.is_public = true
    RETURN
        db.id AS id,
        coalesce(db.public_endpoint_hostname, db.public_endpoint_ip) AS host,
        db.engine AS engine,
        db.public_endpoint_port AS port,
        db.region AS region,
        db.encryption_at_rest_enabled AS encrypted
    """,
    cypher_visual_query="""
    MATCH p=(prj:ScalewayProject)-[:RESOURCE]->(db:ScalewayRdbInstance)
    WHERE db.is_public = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (db:ScalewayRdbInstance)
    RETURN COUNT(db) AS count
    """,
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.SCALEWAY,
    maturity=Maturity.EXPERIMENTAL,
)


_scaleway_redis_public_access = Fact(
    id="scaleway_redis_public_access",
    name="Internet-Accessible Scaleway Managed Redis Attack Surface",
    description=(
        "Scaleway Managed Redis clusters that expose a public endpoint "
        "(is_public = true), reachable from the internet."
    ),
    cypher_query="""
    MATCH (prj:ScalewayProject)-[:RESOURCE]->(rc:ScalewayRedisCluster)
    WHERE rc.is_public = true
    RETURN
        rc.id AS id,
        rc.public_endpoint_ip AS host,
        'Redis' + coalesce(' ' + rc.version, '') AS engine,
        rc.public_endpoint_port AS port,
        rc.zone AS region,
        rc.tls_enabled AS encrypted
    """,
    cypher_visual_query="""
    MATCH p=(prj:ScalewayProject)-[:RESOURCE]->(rc:ScalewayRedisCluster)
    WHERE rc.is_public = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (rc:ScalewayRedisCluster)
    RETURN COUNT(rc) AS count
    """,
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.SCALEWAY,
    maturity=Maturity.EXPERIMENTAL,
)


_scaleway_mongodb_public_access = Fact(
    id="scaleway_mongodb_public_access",
    name="Internet-Accessible Scaleway Managed MongoDB Attack Surface",
    description=(
        "Scaleway Managed MongoDB instances that expose a public endpoint "
        "(is_public = true), reachable from the internet."
    ),
    cypher_query="""
    MATCH (prj:ScalewayProject)-[:RESOURCE]->(m:ScalewayMongoDBInstance)
    WHERE m.is_public = true
    RETURN
        m.id AS id,
        m.public_endpoint_dns AS host,
        'MongoDB' + coalesce(' ' + m.version, '') AS engine,
        m.public_endpoint_port AS port,
        m.region AS region,
        null AS encrypted
    """,
    cypher_visual_query="""
    MATCH p=(prj:ScalewayProject)-[:RESOURCE]->(m:ScalewayMongoDBInstance)
    WHERE m.is_public = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (m:ScalewayMongoDBInstance)
    RETURN COUNT(m) AS count
    """,
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.SCALEWAY,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class DatabaseInstanceExposed(Finding):
    host: str | None = None
    id: str | None = None
    engine: str | None = None
    port: int | None = None
    region: str | None = None
    encrypted: bool | None = None


database_instance_exposed = Rule(
    id="database_instance_exposed",
    name="Internet-Exposed Databases",
    description=("Database instances accessible from the internet"),
    output_model=DatabaseInstanceExposed,
    facts=(
        _aws_rds_public_access,
        _azure_sql_internet_exposed,
        _azure_cosmosdb_public_access,
        _gcp_cloud_sql_public_access,
        _scaleway_rdb_public_access,
        _scaleway_redis_public_access,
        _scaleway_mongodb_public_access,
    ),
    tags=(
        "infrastructure",
        "databases",
        "attack_surface",
        "stride:information_disclosure",
        "stride:tampering",
    ),
    version="0.1.0",
    frameworks=(iso27001_annex_a("8.20"),),
)
