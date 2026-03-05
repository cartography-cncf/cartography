from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# =============================================================================
# AWS Account Not Synced: Detects AWSAccount nodes with no resources
# Main node: AWSAccount
# =============================================================================

_aws_account_not_synced = Fact(
    id="aws-account-not-synced",
    name="AWS Account Not Synced by Cartography",
    description=(
        "Detects AWS accounts that exist in the graph but have no resources, "
        "indicating they were discovered but not actually synced by Cartography."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)
    OPTIONAL MATCH (a)-[:RESOURCE]->(n)
    WITH a, count(n) AS resource_count
    WHERE resource_count <= 1
    RETURN a.id AS account_id, a.name AS account_name, resource_count
    ORDER BY a.name
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount)
    OPTIONAL MATCH (a)-[:RESOURCE]->(n)
    WITH a, count(n) AS resource_count
    WHERE resource_count <= 1
    RETURN a
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class AWSAccountNotSyncedOutput(Finding):
    account_id: str | None = None
    account_name: str | None = None
    resource_count: int | None = None


aws_account_not_synced = Rule(
    id="aws_account_not_synced",
    name="AWS Account Not Synced",
    description=(
        "Detects AWS accounts present in the graph that are not being synced "
        "by Cartography. An account with no resources indicates it was "
        "discovered (e.g. via organizations) but its resources are not being "
        "ingested."
    ),
    output_model=AWSAccountNotSyncedOutput,
    tags=(
        "aws",
        "infrastructure",
        "misconfiguration",
    ),
    facts=(_aws_account_not_synced,),
    version="0.1.0",
)
