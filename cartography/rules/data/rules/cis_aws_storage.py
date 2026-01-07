"""
CIS AWS Storage Security Checks

Implements CIS AWS Foundations Benchmark Section 2: Storage
Based on CIS AWS Foundations Benchmark v5.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS AWS Foundations Benchmark v5.0",
        url="https://www.cisecurity.org/benchmark/amazon_web_services",
    ),
    RuleReference(
        text="AWS S3 Security Best Practices",
        url="https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html",
    ),
]


# =============================================================================
# CIS AWS 2.1.1: S3 bucket versioning
# Main node: S3Bucket
# =============================================================================
class S3VersioningOutput(Finding):
    """Output model for S3 versioning check."""

    bucket_name: str | None = None
    bucket_id: str | None = None
    region: str | None = None
    versioning_status: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_s3_versioning_disabled = Fact(
    id="aws_s3_versioning_disabled",
    name="AWS S3 buckets without versioning enabled",
    description=(
        "Detects S3 buckets that do not have versioning enabled. Versioning helps "
        "protect against accidental deletion and enables recovery of objects."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.versioning_status IS NULL OR bucket.versioning_status <> 'Enabled'
    RETURN
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.versioning_status AS versioning_status,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.versioning_status IS NULL OR bucket.versioning_status <> 'Enabled'
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_2_1_1_s3_versioning = Rule(
    id="cis_2_1_1_s3_versioning",
    name="CIS AWS 2.1.1: S3 Bucket Versioning",
    description=(
        "S3 buckets should have versioning enabled to protect against accidental "
        "deletion and enable recovery of objects."
    ),
    output_model=S3VersioningOutput,
    facts=(_aws_s3_versioning_disabled,),
    tags=("cis:2.1.1", "cis:aws-5.0", "storage", "s3", "stride:tampering"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 2.1.2: S3 bucket MFA Delete
# Main node: S3Bucket
# =============================================================================
class S3MfaDeleteOutput(Finding):
    """Output model for S3 MFA Delete check."""

    bucket_name: str | None = None
    bucket_id: str | None = None
    region: str | None = None
    mfa_delete_enabled: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_s3_mfa_delete_disabled = Fact(
    id="aws_s3_mfa_delete_disabled",
    name="AWS S3 buckets without MFA Delete",
    description=(
        "Detects S3 buckets that do not have MFA Delete enabled. MFA Delete "
        "provides an additional layer of security by requiring MFA authentication "
        "to delete object versions or change versioning state."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.mfa_delete IS NULL OR bucket.mfa_delete = false
    RETURN
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.mfa_delete AS mfa_delete_enabled,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.mfa_delete IS NULL OR bucket.mfa_delete = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_2_1_2_s3_mfa_delete = Rule(
    id="cis_2_1_2_s3_mfa_delete",
    name="CIS AWS 2.1.2: S3 Bucket MFA Delete",
    description=(
        "S3 buckets should have MFA Delete enabled to require MFA authentication "
        "for deleting object versions or changing versioning state."
    ),
    output_model=S3MfaDeleteOutput,
    facts=(_aws_s3_mfa_delete_disabled,),
    tags=("cis:2.1.2", "cis:aws-5.0", "storage", "s3", "stride:tampering"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 2.1.4: S3 Block Public Access
# Main node: S3Bucket
# =============================================================================
class S3BlockPublicAccessOutput(Finding):
    """Output model for S3 Block Public Access check."""

    bucket_name: str | None = None
    bucket_id: str | None = None
    region: str | None = None
    block_public_acls: bool | None = None
    ignore_public_acls: bool | None = None
    block_public_policy: bool | None = None
    restrict_public_buckets: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_s3_block_public_access_disabled = Fact(
    id="aws_s3_block_public_access_disabled",
    name="AWS S3 buckets without full Block Public Access",
    description=(
        "Detects S3 buckets that do not have all Block Public Access settings enabled. "
        "All four Block Public Access settings should be enabled to prevent public access."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE (bucket.block_public_acls IS NULL OR bucket.block_public_acls <> true)
       OR (bucket.ignore_public_acls IS NULL OR bucket.ignore_public_acls <> true)
       OR (bucket.block_public_policy IS NULL OR bucket.block_public_policy <> true)
       OR (bucket.restrict_public_buckets IS NULL OR bucket.restrict_public_buckets <> true)
    RETURN
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.block_public_acls AS block_public_acls,
        bucket.ignore_public_acls AS ignore_public_acls,
        bucket.block_public_policy AS block_public_policy,
        bucket.restrict_public_buckets AS restrict_public_buckets,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE (bucket.block_public_acls IS NULL OR bucket.block_public_acls <> true)
       OR (bucket.ignore_public_acls IS NULL OR bucket.ignore_public_acls <> true)
       OR (bucket.block_public_policy IS NULL OR bucket.block_public_policy <> true)
       OR (bucket.restrict_public_buckets IS NULL OR bucket.restrict_public_buckets <> true)
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_2_1_4_s3_block_public_access = Rule(
    id="cis_2_1_4_s3_block_public_access",
    name="CIS AWS 2.1.4: S3 Block Public Access",
    description=(
        "S3 buckets should have all Block Public Access settings enabled to prevent "
        "accidental public exposure of data."
    ),
    output_model=S3BlockPublicAccessOutput,
    facts=(_aws_s3_block_public_access_disabled,),
    tags=("cis:2.1.4", "cis:aws-5.0", "storage", "s3", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 2.1.5: S3 Access Logging
# Main node: S3Bucket
# =============================================================================
class S3AccessLoggingOutput(Finding):
    """Output model for S3 access logging check."""

    bucket_name: str | None = None
    bucket_id: str | None = None
    region: str | None = None
    logging_enabled: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_s3_access_logging_disabled = Fact(
    id="aws_s3_access_logging_disabled",
    name="AWS S3 buckets without access logging",
    description=(
        "Detects S3 buckets that do not have server access logging enabled. "
        "Access logging provides detailed records for access requests to the bucket."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.logging_enabled IS NULL OR bucket.logging_enabled = false
    RETURN
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.logging_enabled AS logging_enabled,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.logging_enabled IS NULL OR bucket.logging_enabled = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_2_1_5_s3_access_logging = Rule(
    id="cis_2_1_5_s3_access_logging",
    name="CIS AWS 2.1.5: S3 Bucket Access Logging",
    description=(
        "S3 buckets should have server access logging enabled to provide detailed "
        "records for access requests."
    ),
    output_model=S3AccessLoggingOutput,
    facts=(_aws_s3_access_logging_disabled,),
    tags=("cis:2.1.5", "cis:aws-5.0", "storage", "s3", "logging", "stride:repudiation"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 2.1.6: S3 Default Encryption
# Main node: S3Bucket
# =============================================================================
class S3EncryptionOutput(Finding):
    """Output model for S3 encryption check."""

    bucket_name: str | None = None
    bucket_id: str | None = None
    region: str | None = None
    default_encryption: bool | None = None
    encryption_algorithm: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_s3_encryption_disabled = Fact(
    id="aws_s3_encryption_disabled",
    name="AWS S3 buckets without default encryption",
    description=(
        "Detects S3 buckets that do not have default encryption enabled. "
        "Default encryption ensures all objects stored are encrypted at rest."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.default_encryption IS NULL OR bucket.default_encryption = false
    RETURN
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.default_encryption AS default_encryption,
        bucket.encryption_algorithm AS encryption_algorithm,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.default_encryption IS NULL OR bucket.default_encryption = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_2_1_6_s3_encryption = Rule(
    id="cis_2_1_6_s3_encryption",
    name="CIS AWS 2.1.6: S3 Default Encryption",
    description=(
        "S3 buckets should have default encryption enabled to ensure all objects "
        "are encrypted at rest."
    ),
    output_model=S3EncryptionOutput,
    facts=(_aws_s3_encryption_disabled,),
    tags=(
        "cis:2.1.6",
        "cis:aws-5.0",
        "storage",
        "s3",
        "encryption",
        "stride:information_disclosure",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 2.2.1: RDS Encryption at Rest
# Main node: RDSInstance
# =============================================================================
class RdsEncryptionOutput(Finding):
    """Output model for RDS encryption check."""

    db_identifier: str | None = None
    db_arn: str | None = None
    engine: str | None = None
    engine_version: str | None = None
    instance_class: str | None = None
    storage_encrypted: bool | None = None
    publicly_accessible: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_rds_encryption_disabled = Fact(
    id="aws_rds_encryption_disabled",
    name="AWS RDS instances without encryption at rest",
    description=(
        "Detects RDS instances that do not have storage encryption enabled. "
        "Encrypting RDS instances protects data at rest and helps meet "
        "compliance requirements for sensitive data."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance)
    WHERE rds.storage_encrypted IS NULL OR rds.storage_encrypted = false
    RETURN
        rds.db_instance_identifier AS db_identifier,
        rds.arn AS db_arn,
        rds.engine AS engine,
        rds.engine_version AS engine_version,
        rds.db_instance_class AS instance_class,
        rds.storage_encrypted AS storage_encrypted,
        rds.publicly_accessible AS publicly_accessible,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(rds:RDSInstance)
    WHERE rds.storage_encrypted IS NULL OR rds.storage_encrypted = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_2_2_1_rds_encryption = Rule(
    id="cis_2_2_1_rds_encryption",
    name="CIS AWS 2.2.1: RDS Encryption at Rest",
    description=(
        "RDS instances should have storage encryption enabled to protect data at rest "
        "and meet compliance requirements."
    ),
    output_model=RdsEncryptionOutput,
    facts=(_aws_rds_encryption_disabled,),
    tags=(
        "cis:2.2.1",
        "cis:aws-5.0",
        "storage",
        "rds",
        "encryption",
        "stride:information_disclosure",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 2.3.1: EBS Volume Encryption
# Main node: EBSVolume
# =============================================================================
class EbsEncryptionOutput(Finding):
    """Output model for EBS encryption check."""

    volume_id: str | None = None
    region: str | None = None
    volume_type: str | None = None
    size_gb: int | None = None
    state: str | None = None
    encrypted: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_ebs_encryption_disabled = Fact(
    id="aws_ebs_encryption_disabled",
    name="AWS EBS volumes without encryption",
    description=(
        "Detects EBS volumes that are not encrypted. Encrypting EBS volumes "
        "protects data at rest and data in transit between the volume and instance."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(volume:EBSVolume)
    WHERE volume.encrypted IS NULL OR volume.encrypted = false
    RETURN
        volume.id AS volume_id,
        volume.region AS region,
        volume.volumetype AS volume_type,
        volume.size AS size_gb,
        volume.state AS state,
        volume.encrypted AS encrypted,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(volume:EBSVolume)
    WHERE volume.encrypted IS NULL OR volume.encrypted = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_2_3_1_ebs_encryption = Rule(
    id="cis_2_3_1_ebs_encryption",
    name="CIS AWS 2.3.1: EBS Volume Encryption",
    description=(
        "EBS volumes should be encrypted to protect data at rest and in transit "
        "between the volume and instance."
    ),
    output_model=EbsEncryptionOutput,
    facts=(_aws_ebs_encryption_disabled,),
    tags=(
        "cis:2.3.1",
        "cis:aws-5.0",
        "storage",
        "ebs",
        "encryption",
        "stride:information_disclosure",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)
