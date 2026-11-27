"""
AWS EBS encryption and snapshot coverage


Each rule is a single-property check over data the AWS sync already collects.
All are EXPERIMENTAL until validated against a live graph.

"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsEc2EbsSnapshotEncryptionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    snapshot_id: str | None = None
    encrypted: str | None = None
    source_volume_id: str | None = None


_aws_ec2_ebs_snapshot_encryption_fact = Fact(
    id="aws_ec2_ebs_snapshot_encryption_fact",
    name="EBS snapshot encryption",
    description="Snapshots with encrypted=false or encrypted IS NULL.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSEBSSnapshot)
        WHERE s.encrypted = false OR s.encrypted IS NULL
        RETURN a.id AS account_id, a.name AS account, s.snapshotid AS snapshot_id,
               s.encrypted AS encrypted, s.volumeid AS source_volume_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(s:AWSEBSSnapshot)
        WHERE s.encrypted = false OR s.encrypted IS NULL
        RETURN a.id AS account_id, a.name AS account, s.snapshotid AS snapshot_id,
               s.encrypted AS encrypted, s.volumeid AS source_volume_id

    """,
    cypher_count_query="""
    MATCH (s:AWSEBSSnapshot) RETURN COUNT(s) AS count
    """,
    asset_label="AWSEBSSnapshot",
    asset_id_field="snapshot_id",
    identity_fields=("snapshot_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_ebs_snapshot_encryption = Rule(
    id="aws_ec2_ebs_snapshot_encryption",
    name="EBS Snapshot Encryption at Rest",
    description="EBS snapshot is not encrypted at rest. A NULL ``encrypted`` (absent from the graph) is treated as unencrypted so those snapshots are not silently passed.",
    output_model=AwsEc2EbsSnapshotEncryptionOutput,
    facts=(_aws_ec2_ebs_snapshot_encryption_fact,),
    tags=("security", "ec2", "ebs", "encryption", "cspm"),
    version="0.1.0",
)


class AwsEc2EbsVolumeHasSnapshotOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    volume_id: str | None = None
    state: str | None = None


_aws_ec2_ebs_volume_has_snapshot_fact = Fact(
    id="aws_ec2_ebs_volume_has_snapshot_fact",
    name="EBS volume without snapshot",
    description="Volumes for which no AWSEBSSnapshot shares the volume's volumeid.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(v:AWSEBSVolume)
        OPTIONAL MATCH (snap:AWSEBSSnapshot)
        WHERE snap.volumeid = v.volumeid
        WITH a, v, snap
        WHERE snap IS NULL
        RETURN a.id AS account_id, a.name AS account, v.volumeid AS volume_id,
               v.state AS state

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(v:AWSEBSVolume)
        OPTIONAL MATCH (snap:AWSEBSSnapshot)
        WHERE snap.volumeid = v.volumeid
        WITH a, v, snap
        WHERE snap IS NULL
        RETURN a.id AS account_id, a.name AS account, v.volumeid AS volume_id,
               v.state AS state

    """,
    cypher_count_query="""
    MATCH (v:AWSEBSVolume) RETURN COUNT(v) AS count
    """,
    asset_label="AWSEBSVolume",
    asset_id_field="volume_id",
    identity_fields=("volume_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_ebs_volume_has_snapshot = Rule(
    id="aws_ec2_ebs_volume_has_snapshot",
    name="EBS Volume Has a Snapshot",
    description="EBS volume has no snapshot. Joined on snapshot.volumeid = volume.volumeid (property join); the volume's CREATED_FROM edge points to the snapshot the volume was created FROM, not to snapshots OF the volume, so it is not used. Snapshot sync is account-owned (Owners=self), a per-account lookup.",
    output_model=AwsEc2EbsVolumeHasSnapshotOutput,
    facts=(_aws_ec2_ebs_volume_has_snapshot_fact,),
    tags=("security", "ec2", "ebs", "backup", "cspm"),
    version="0.1.0",
)
