from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS Facts
_aws_ebs_snapshot_public = Fact(
    id="aws_ebs_snapshot_public",
    name="Publicly Shared EBS Snapshots",
    description=(
        "AWS EBS snapshots shared publicly. A public snapshot can be copied "
        "or restored into a volume by any AWS account, exposing the full "
        "contents of the source volume to anyone."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(s:EBSSnapshot)
    WHERE s.ispublic = true
    RETURN
        coalesce(s.description, s.id) AS name,
        s.id AS id,
        s.id AS arn,
        s.volumeid AS source_identifier,
        s.encrypted AS encrypted,
        s.region AS region,
        a.id AS account_id,
        a.name AS account,
        'EBSSnapshot' AS resource_type
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(s:EBSSnapshot)
    WHERE s.ispublic = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (s:EBSSnapshot)
    RETURN COUNT(s) AS count
    """,
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


_aws_rds_snapshot_public = Fact(
    id="aws_rds_snapshot_public",
    name="Publicly Shared RDS Snapshots",
    description=(
        "AWS RDS snapshots shared publicly. A public snapshot can be copied "
        "or restored into a database by any AWS account, exposing the full "
        "contents of the source database to anyone."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(s:RDSSnapshot)
    WHERE s.ispublic = true
    RETURN
        s.db_snapshot_identifier AS name,
        s.db_snapshot_identifier AS id,
        s.arn AS arn,
        s.db_instance_identifier AS source_identifier,
        s.encrypted AS encrypted,
        s.region AS region,
        a.id AS account_id,
        a.name AS account,
        'RDSSnapshot' AS resource_type
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(s:RDSSnapshot)
    WHERE s.ispublic = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (s:RDSSnapshot)
    RETURN COUNT(s) AS count
    """,
    asset_id_field="arn",
    identity_fields=("arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


_aws_ami_public = Fact(
    id="aws_ami_public",
    name="Publicly Shared AMIs",
    description=(
        "AWS AMIs (machine images) owned by the account and shared publicly. "
        "A public AMI can be launched by any AWS account, exposing the full "
        "contents of every disk baked into the image (including any secrets "
        "or data left on the root volume). The ownership filter (i.owner = "
        "a.id) is required because EC2 image ingestion also attaches "
        "third-party public AMIs referenced by instances/launch templates to "
        "the syncing account; those are in use, not owned, and must not be "
        "flagged."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(i:EC2Image)
    WHERE i.ispublic = true
      AND i.owner = a.id
    RETURN
        coalesce(i.name, i.id) AS name,
        i.id AS id,
        i.imageid AS arn,
        i.name AS source_identifier,
        null AS encrypted,
        i.region AS region,
        a.id AS account_id,
        a.name AS account,
        'EC2Image' AS resource_type
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(i:EC2Image)
    WHERE i.ispublic = true
      AND i.owner = a.id
    RETURN *
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(i:EC2Image)
    WHERE i.owner = a.id
    RETURN COUNT(i) AS count
    """,
    asset_id_field="id",
    identity_fields=("id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class PublicSnapshots(Finding):
    name: str | None = None
    id: str | None = None
    arn: str | None = None
    source_identifier: str | None = None
    encrypted: bool | None = None
    region: str | None = None
    account_id: str | None = None
    account: str | None = None
    resource_type: str | None = None


public_snapshots = Rule(
    id="public_snapshots",
    name="Publicly Accessible Snapshots",
    description=(
        "EBS snapshots, RDS snapshots, and AMIs shared publicly, allowing any "
        "AWS account to copy or restore an entire volume, database, or machine "
        "image. This is a classic data-exfiltration path that bypasses bucket "
        "and network controls."
    ),
    output_model=PublicSnapshots,
    facts=(
        _aws_ebs_snapshot_public,
        _aws_rds_snapshot_public,
        _aws_ami_public,
    ),
    tags=(
        "infrastructure",
        "data",
        "attack_surface",
        "stride:information_disclosure",
    ),
    version="0.1.0",
    frameworks=(iso27001_annex_a("8.3"),),
)
