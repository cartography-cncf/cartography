from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Azure Facts
# SQL Server firewall rules need to be split into two distinct exposure
# classes (per Microsoft's documentation): the special start_ip=end_ip=0.0.0.0
# row only allows Azure services / resources, not arbitrary public IPs, while
# any rule that actually covers public IP space exposes the server to the
# internet.
_azure_sql_internet_exposed = Fact(
    id="azure_sql_internet_exposed",
    name="Internet-Accessible Azure SQL Server Attack Surface",
    description=(
        "Azure SQL Servers reachable from the public internet. Triggered "
        "when public_network_access = 'Enabled' and a firewall rule allows "
        "traffic from public IP space (start_ip=0.0.0.0, end_ip!=0.0.0.0)."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(server:AzureSQLServer)
    MATCH (rule:AzureSQLServerFirewallRule)-[:MEMBER_OF_AZURE_SQL_SERVER]->(server)
    WHERE coalesce(server.public_network_access, 'Enabled') = 'Enabled'
      AND rule.start_ip_address = '0.0.0.0'
      AND rule.end_ip_address IS NOT NULL
      AND rule.end_ip_address <> '0.0.0.0'
    RETURN
        server.id AS id,
        server.name AS host,
        'Microsoft.Sql' AS engine,
        1433 AS port,
        server.location AS region,
        server.minimal_tls_version AS encrypted
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
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


_azure_sql_allow_azure_services = Fact(
    id="azure_sql_allow_azure_services",
    name="Azure SQL Server with Allow-Azure-Services Firewall Rule",
    description=(
        "Azure SQL Servers with the special start_ip=0.0.0.0 / end_ip=0.0.0.0 "
        "firewall rule. Microsoft documents this row as 'allow Azure-hosted "
        "services and resources to access this server', which is a different "
        "exposure class than public-internet reachability and should be "
        "evaluated separately."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(server:AzureSQLServer)
    MATCH (rule:AzureSQLServerFirewallRule)-[:MEMBER_OF_AZURE_SQL_SERVER]->(server)
    WHERE rule.start_ip_address = '0.0.0.0'
      AND rule.end_ip_address = '0.0.0.0'
    RETURN
        server.id AS id,
        server.name AS host,
        'Microsoft.Sql' AS engine,
        1433 AS port,
        server.location AS region,
        server.minimal_tls_version AS encrypted
    """,
    cypher_visual_query="""
    MATCH p=(sub:AzureSubscription)-[:RESOURCE]->(server:AzureSQLServer)<-[:MEMBER_OF_AZURE_SQL_SERVER]-(rule:AzureSQLServerFirewallRule)
    WHERE rule.start_ip_address = '0.0.0.0'
      AND rule.end_ip_address = '0.0.0.0'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (server:AzureSQLServer)
    RETURN COUNT(server) AS count
    """,
    asset_id_field="id",
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


_azure_cosmosdb_public_access = Fact(
    id="azure_cosmosdb_public_access",
    name="Internet-Accessible Azure Cosmos DB Account",
    description=(
        "Azure Cosmos DB accounts with publicnetworkaccess = 'Enabled' and "
        "no IP allowlist or VNet filter, leaving the account reachable from "
        "any public IP."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(account:AzureCosmosDBAccount)
    WHERE account.publicnetworkaccess = 'Enabled'
      AND coalesce(account.virtualnetworkfilterenabled, false) = false
      AND (account.ipranges IS NULL OR account.ipranges = '')
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
      AND (account.ipranges IS NULL OR account.ipranges = '')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (account:AzureCosmosDBAccount)
    RETURN COUNT(account) AS count
    """,
    asset_id_field="id",
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
    RETURN
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
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


# AWS Facts
_aws_rds_public_access = Fact(
    id="aws_rds_public_access",
    name="Internet-Accessible RDS Database Attack Surface",
    description="AWS RDS instances accessible from the internet",
    cypher_query="""
    MATCH (rds:RDSInstance)
    WHERE rds.publicly_accessible = true
    RETURN rds.id AS id,
        rds.engine AS engine,
        rds.db_instance_class AS instance_class,
        rds.endpoint_address AS host,
        rds.endpoint_port AS port,
        rds.region AS region,
        rds.storage_encrypted AS encrypted
    """,
    cypher_visual_query="""
    MATCH p1=(rds:RDSInstance{publicly_accessible: true})
    OPTIONAL MATCH p2=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
    OPTIONAL MATCH p3=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound:AWSIpRule)
    OPTIONAL MATCH p4=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound:AWSIpRule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (rds:RDSInstance)
    RETURN COUNT(rds) AS count
    """,
    module=Module.AWS,
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
        _azure_sql_allow_azure_services,
        _azure_cosmosdb_public_access,
        _gcp_cloud_sql_public_access,
    ),
    tags=(
        "infrastructure",
        "databases",
        "attack_surface",
        "stride:information_disclosure",
        "stride:tampering",
    ),
    version="0.1.0",
)
