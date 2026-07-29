from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AzureSQLMinimumTLSBelow12Output(Finding):
    server_name: str | None = None
    server_id: str | None = None
    subscription_id: str | None = None
    subscription: str | None = None
    location: str | None = None
    minimum_tls_version: str | None = None


_azure_sql_minimum_tls_below_1_2 = Fact(
    id="azure_sql_minimum_tls_below_1_2",
    name="Azure SQL servers allowing TLS versions below 1.2",
    description=(
        "Detects Azure SQL servers explicitly configured with a minimum TLS "
        "version of 1.0 or 1.1."
    ),
    cypher_query="""
    MATCH (subscription:AzureSubscription)-[:RESOURCE]->(server:AzureSQLServer)
    WHERE server.minimal_tls_version IN ['1.0', '1.1']
    RETURN
        server.name AS server_name,
        server.id AS server_id,
        subscription.id AS subscription_id,
        subscription.name AS subscription,
        server.location AS location,
        server.minimal_tls_version AS minimum_tls_version
    """,
    cypher_visual_query="""
    MATCH p=(subscription:AzureSubscription)-[:RESOURCE]->(server:AzureSQLServer)
    WHERE server.minimal_tls_version IN ['1.0', '1.1']
    RETURN *
    """,
    cypher_count_query="""
    MATCH (server:AzureSQLServer)
    WHERE server.minimal_tls_version IS NOT NULL
    RETURN COUNT(server) AS count
    """,
    asset_label="AzureSQLServer",
    asset_id_field="server_id",
    identity_fields=("server_id",),
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


azure_sql_minimum_tls_below_1_2 = Rule(
    id="azure_sql_minimum_tls_below_1_2",
    name="Azure SQL Minimum TLS Version Below 1.2",
    description=(
        "Detects Azure SQL servers explicitly configured to accept obsolete TLS "
        "protocol versions."
    ),
    output_model=AzureSQLMinimumTLSBelow12Output,
    facts=(_azure_sql_minimum_tls_below_1_2,),
    tags=("azure", "database", "encryption", "transport_security"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.24"),
        soc2_tsc("CC6.7"),
    ),
)
