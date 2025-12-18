"""
CIS AWS Storage Security Checks

Implements CIS AWS Foundations Benchmark Section 2: Storage
Based on CIS AWS Foundations Benchmark v5.0

Each Fact represents a specific CIS check that can be performed against
Neo4j data synced by Cartography.
"""
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference


# -----------------------------------------------------------------------------
# CIS 2.1.1: Ensure S3 Bucket Policy is set to deny HTTP requests
# (Covered partially - we check for public access settings)
# -----------------------------------------------------------------------------
# Note: This is already covered by object_storage_public rule, but we add
# additional checks for Block Public Access settings


# -----------------------------------------------------------------------------
# CIS 2.1.2: Ensure S3 bucket MFA Delete is enabled
# -----------------------------------------------------------------------------
_cis_2_1_2_s3_mfa_delete_disabled = Fact(
    id="cis_2_1_2_s3_mfa_delete_disabled",
    name="CIS 2.1.2: S3 buckets without MFA Delete",
    description=(
        "Detects S3 buckets that do not have MFA Delete enabled. MFA Delete "
        "provides an additional layer of security by requiring MFA authentication "
        "to delete object versions or change versioning state."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.mfa_delete IS NULL OR bucket.mfa_delete = false
    RETURN
        a.id AS account_id,
        a.name AS account,
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.mfa_delete AS mfa_delete_enabled
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.mfa_delete IS NULL OR bucket.mfa_delete = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 2.1.4: Ensure that S3 Buckets are configured with 'Block public access'
# -----------------------------------------------------------------------------
_cis_2_1_4_s3_block_public_access = Fact(
    id="cis_2_1_4_s3_block_public_access_disabled",
    name="CIS 2.1.4: S3 buckets without full Block Public Access",
    description=(
        "Detects S3 buckets that do not have all Block Public Access settings enabled. "
        "All four Block Public Access settings should be enabled to prevent public access."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.block_public_acls <> true
       OR bucket.ignore_public_acls <> true
       OR bucket.block_public_policy <> true
       OR bucket.restrict_public_buckets <> true
    RETURN
        a.id AS account_id,
        a.name AS account,
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.block_public_acls AS block_public_acls,
        bucket.ignore_public_acls AS ignore_public_acls,
        bucket.block_public_policy AS block_public_policy,
        bucket.restrict_public_buckets AS restrict_public_buckets
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.block_public_acls <> true
       OR bucket.ignore_public_acls <> true
       OR bucket.block_public_policy <> true
       OR bucket.restrict_public_buckets <> true
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 2.1.1: Ensure S3 bucket versioning is enabled
# -----------------------------------------------------------------------------
_cis_2_1_1_s3_versioning_disabled = Fact(
    id="cis_2_1_1_s3_versioning_disabled",
    name="CIS 2.1.1: S3 buckets without versioning enabled",
    description=(
        "Detects S3 buckets that do not have versioning enabled. Versioning helps "
        "protect against accidental deletion and enables recovery of objects."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.versioning_status IS NULL OR bucket.versioning_status <> 'Enabled'
    RETURN
        a.id AS account_id,
        a.name AS account,
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.versioning_status AS versioning_status
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.versioning_status IS NULL OR bucket.versioning_status <> 'Enabled'
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 2.1.5: Ensure S3 bucket access logging is enabled
# -----------------------------------------------------------------------------
_cis_2_1_5_s3_access_logging_disabled = Fact(
    id="cis_2_1_5_s3_access_logging_disabled",
    name="CIS 2.1.5: S3 buckets without access logging",
    description=(
        "Detects S3 buckets that do not have server access logging enabled. "
        "Access logging provides detailed records for access requests to the bucket."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.logging_enabled IS NULL OR bucket.logging_enabled = false
    RETURN
        a.id AS account_id,
        a.name AS account,
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.logging_enabled AS logging_enabled
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.logging_enabled IS NULL OR bucket.logging_enabled = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 2.1.6: Ensure S3 bucket default encryption is enabled
# -----------------------------------------------------------------------------
_cis_2_1_6_s3_encryption_disabled = Fact(
    id="cis_2_1_6_s3_encryption_disabled",
    name="CIS 2.1.6: S3 buckets without default encryption",
    description=(
        "Detects S3 buckets that do not have default encryption enabled. "
        "Default encryption ensures all objects stored are encrypted at rest."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.default_encryption IS NULL OR bucket.default_encryption = false
    RETURN
        a.id AS account_id,
        a.name AS account,
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.default_encryption AS default_encryption,
        bucket.encryption_algorithm AS encryption_algorithm
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.default_encryption IS NULL OR bucket.default_encryption = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 2.2.1: Ensure that encryption-at-rest is enabled for RDS instances
# -----------------------------------------------------------------------------
_cis_2_2_1_rds_encryption_disabled = Fact(
    id="cis_2_2_1_rds_encryption_disabled",
    name="CIS 2.2.1: RDS instances without encryption at rest",
    description=(
        "Detects RDS instances that do not have storage encryption enabled. "
        "Encrypting RDS instances protects data at rest and helps meet "
        "compliance requirements for sensitive data."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance)
    WHERE rds.storage_encrypted IS NULL OR rds.storage_encrypted = false
    RETURN
        a.id AS account_id,
        a.name AS account,
        rds.db_instance_identifier AS db_identifier,
        rds.arn AS db_arn,
        rds.engine AS engine,
        rds.engine_version AS engine_version,
        rds.db_instance_class AS instance_class,
        rds.storage_encrypted AS storage_encrypted,
        rds.publicly_accessible AS publicly_accessible
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance)
    WHERE rds.storage_encrypted IS NULL OR rds.storage_encrypted = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 2.3.1: Ensure EBS volume encryption is enabled
# -----------------------------------------------------------------------------
_cis_2_3_1_ebs_encryption_disabled = Fact(
    id="cis_2_3_1_ebs_encryption_disabled",
    name="CIS 2.3.1: EBS volumes without encryption",
    description=(
        "Detects EBS volumes that are not encrypted. Encrypting EBS volumes "
        "protects data at rest and data in transit between the volume and instance."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(volume:EBSVolume)
    WHERE volume.encrypted IS NULL OR volume.encrypted = false
    RETURN
        a.id AS account_id,
        a.name AS account,
        volume.id AS volume_id,
        volume.region AS region,
        volume.volumetype AS volume_type,
        volume.size AS size_gb,
        volume.state AS state,
        volume.encrypted AS encrypted
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(volume:EBSVolume)
    WHERE volume.encrypted IS NULL OR volume.encrypted = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# Output Model
# -----------------------------------------------------------------------------
class CISAWSStorageOutput(Finding):
    """Output model for CIS AWS Storage checks."""
    account_id: str | None = None
    account: str | None = None
    bucket_name: str | None = None
    bucket_id: str | None = None
    volume_id: str | None = None
    region: str | None = None
    mfa_delete_enabled: bool | None = None
    block_public_acls: bool | None = None
    ignore_public_acls: bool | None = None
    block_public_policy: bool | None = None
    restrict_public_buckets: bool | None = None
    versioning_status: str | None = None
    logging_enabled: bool | None = None
    default_encryption: bool | None = None
    encryption_algorithm: str | None = None
    encrypted: bool | None = None
    volume_type: str | None = None
    size_gb: int | None = None
    state: str | None = None
    # RDS fields
    db_identifier: str | None = None
    db_arn: str | None = None
    engine: str | None = None
    engine_version: str | None = None
    instance_class: str | None = None
    storage_encrypted: bool | None = None
    publicly_accessible: bool | None = None


# -----------------------------------------------------------------------------
# Rule Definition
# -----------------------------------------------------------------------------
cis_aws_storage = Rule(
    id="cis_aws_storage",
    name="CIS AWS Storage Security Checks",
    description=(
        "CIS AWS Foundations Benchmark - Storage controls. "
        "Detects S3 and EBS misconfigurations including missing encryption, "
        "disabled versioning, and insufficient access controls."
    ),
    output_model=CISAWSStorageOutput,
    facts=(
        _cis_2_1_2_s3_mfa_delete_disabled,
        _cis_2_1_4_s3_block_public_access,
        _cis_2_1_1_s3_versioning_disabled,
        _cis_2_1_5_s3_access_logging_disabled,
        _cis_2_1_6_s3_encryption_disabled,
        _cis_2_2_1_rds_encryption_disabled,
        _cis_2_3_1_ebs_encryption_disabled,
    ),
    tags=("cis", "compliance", "cis_aws_5.0", "storage", "s3", "ebs", "rds"),
    version="1.0.0",
    references=[
        RuleReference(
            text="CIS AWS Foundations Benchmark v5.0",
            url="https://www.cisecurity.org/benchmark/amazon_web_services",
        ),
        RuleReference(
            text="AWS S3 Security Best Practices",
            url="https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html",
        ),
    ],
)
