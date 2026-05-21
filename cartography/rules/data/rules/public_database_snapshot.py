from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

_aws_public_rds_snapshots = Fact(
    id="aws_public_rds_snapshots",
    name="Public AWS RDS snapshots",
    description=(
        "RDS DB snapshots marked public. Public database snapshots can expose "
        "database contents outside the account even when the source database is "
        "private."
    ),
    cypher_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(snapshot:RDSSnapshot)
    WHERE coalesce(snapshot.ispublic, false) = true
    RETURN
        snapshot.arn AS snapshot_id,
        snapshot.db_snapshot_identifier AS snapshot_name,
        account.name AS account,
        account.id AS account_id,
        snapshot.region AS region,
        snapshot.engine AS engine,
        snapshot.encrypted AS encrypted,
        snapshot.snapshot_type AS snapshot_type,
        snapshot.db_instance_identifier AS source_database,
        snapshot.snapshot_create_time AS created_at
    ORDER BY account, region, snapshot_name
    """,
    cypher_visual_query="""
    MATCH p=(account:AWSAccount)-[:RESOURCE]->(snapshot:RDSSnapshot)
    WHERE coalesce(snapshot.ispublic, false) = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (snapshot:RDSSnapshot)
    RETURN COUNT(snapshot) AS count
    """,
    asset_id_field="snapshot_id",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class PublicDatabaseSnapshot(Finding):
    snapshot_id: str | None = None
    snapshot_name: str | None = None
    account: str | None = None
    account_id: str | None = None
    region: str | None = None
    engine: str | None = None
    encrypted: bool | None = None
    snapshot_type: str | None = None
    source_database: str | None = None
    created_at: str | None = None


public_database_snapshot = Rule(
    id="public_database_snapshot",
    name="Public Database Snapshots",
    description=(
        "Database snapshots shared publicly. These are high-signal exposure "
        "findings because the snapshot can contain production data independent "
        "of the live database network posture."
    ),
    output_model=PublicDatabaseSnapshot,
    facts=(_aws_public_rds_snapshots,),
    tags=(
        "data",
        "database",
        "backup",
        "attack_surface",
        "stride:information_disclosure",
    ),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.3"),
        iso27001_annex_a("8.12"),
    ),
)
