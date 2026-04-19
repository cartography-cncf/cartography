from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

_aws_ebs_snapshot_public = Fact(
    id="aws_ebs_snapshot_public",
    name="AWS public EBS snapshots",
    description=(
        "AWS EBS snapshots that allow the all group to create volumes from them."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(snapshot:EBSSnapshot)
    WHERE snapshot.ispublic = true
    RETURN
        snapshot.id AS id,
        snapshot.snapshotid AS snapshot_identifier,
        'EBS' AS snapshot_service,
        snapshot.region AS region,
        snapshot.ispublic AS public_access,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(snapshot:EBSSnapshot)
    WHERE snapshot.ispublic = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (snapshot:EBSSnapshot)
    WHERE snapshot.ispublic = true
    RETURN COUNT(snapshot) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


_aws_rds_snapshot_public = Fact(
    id="aws_rds_snapshot_public",
    name="AWS public RDS snapshots",
    description=("AWS manual RDS snapshots that are restorable by all AWS accounts."),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(snapshot:RDSSnapshot)
    WHERE snapshot.ispublic = true
    RETURN
        snapshot.id AS id,
        snapshot.db_snapshot_identifier AS snapshot_identifier,
        'RDS' AS snapshot_service,
        snapshot.region AS region,
        snapshot.ispublic AS public_access,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(snapshot:RDSSnapshot)
    WHERE snapshot.ispublic = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (snapshot:RDSSnapshot)
    WHERE snapshot.ispublic = true
    RETURN COUNT(snapshot) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class BackupSnapshotPublic(Finding):
    id: str | None = None
    snapshot_identifier: str | None = None
    snapshot_service: str | None = None
    account: str | None = None
    account_id: str | None = None
    region: str | None = None
    public_access: bool | None = None


backup_snapshot_public = Rule(
    id="backup_snapshot_public",
    name="Public Backup Snapshot Exposure",
    description=(
        "Publicly accessible AWS backup snapshots, including EBS snapshots and "
        "manual RDS snapshots."
    ),
    output_model=BackupSnapshotPublic,
    facts=(
        _aws_ebs_snapshot_public,
        _aws_rds_snapshot_public,
    ),
    tags=(
        "storage",
        "attack_surface",
        "stride:information_disclosure",
    ),
    version="0.1.0",
)
