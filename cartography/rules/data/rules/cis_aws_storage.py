"""
CIS AWS Storage Security Checks

Implements CIS AWS Foundations Benchmark Section 3: Storage
Based on CIS AWS Foundations Benchmark v6.0.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS AWS Foundations Benchmark v6.0.0",
        url="https://www.cisecurity.org/benchmark/amazon_web_services",
    ),
    RuleReference(
        text="AWS S3 Security Best Practices",
        url="https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html",
    ),
]


# =============================================================================
# CIS AWS 3.1.2: MFA Delete is enabled on S3 buckets
# Main node: S3Bucket
# =============================================================================
# v6 3.1.2 requires both Versioning enabled and MFA Delete enabled. This rule
# matches the audit procedure: a bucket fails if either property is missing.
class S3MfaDeleteOutput(Finding):
    """Output model for S3 MFA Delete check."""

    bucket_name: str | None = None
    bucket_id: str | None = None
    region: str | None = None
    versioning_status: str | None = None
    mfa_delete_enabled: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_s3_mfa_delete_disabled = Fact(
    id="aws_s3_mfa_delete_disabled",
    name="AWS S3 buckets without Versioning and MFA Delete",
    description=(
        "Detects S3 buckets where either Versioning or MFA Delete is not enabled. "
        "MFA Delete requires Versioning to be enabled and adds an additional layer "
        "of authentication when deleting object versions."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.versioning_status IS NULL OR bucket.versioning_status <> 'Enabled'
       OR bucket.mfa_delete IS NULL OR bucket.mfa_delete = false
    RETURN
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.versioning_status AS versioning_status,
        bucket.mfa_delete AS mfa_delete_enabled,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(bucket:S3Bucket)
    WHERE bucket.versioning_status IS NULL OR bucket.versioning_status <> 'Enabled'
       OR bucket.mfa_delete IS NULL OR bucket.mfa_delete = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (bucket:S3Bucket)
    RETURN COUNT(bucket) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_3_1_2_s3_mfa_delete = Rule(
    id="cis_aws_3_1_2_s3_mfa_delete",
    name="CIS AWS 3.1.2: S3 Bucket MFA Delete",
    description=(
        "S3 buckets should have Versioning and MFA Delete enabled to require MFA "
        "authentication for deleting object versions or changing versioning state."
    ),
    output_model=S3MfaDeleteOutput,
    facts=(_aws_s3_mfa_delete_disabled,),
    tags=("storage", "s3", "stride:tampering"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="6.0.0",
            requirement="3.1.2",
        ),
    ),
)


# =============================================================================
# CIS AWS 3.1.4: S3 Block Public Access
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
    cypher_count_query="""
    MATCH (bucket:S3Bucket)
    RETURN COUNT(bucket) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_3_1_4_s3_block_public_access = Rule(
    id="cis_aws_3_1_4_s3_block_public_access",
    name="CIS AWS 3.1.4: S3 Block Public Access",
    description=(
        "S3 buckets should have all Block Public Access settings enabled to prevent "
        "accidental public exposure of data."
    ),
    output_model=S3BlockPublicAccessOutput,
    facts=(_aws_s3_block_public_access_disabled,),
    tags=("storage", "s3", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="6.0.0",
            requirement="3.1.4",
        ),
    ),
)


# =============================================================================
# CIS AWS 3.2.1: RDS Encryption at Rest
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
    cypher_count_query="""
    MATCH (rds:RDSInstance)
    RETURN COUNT(rds) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_3_2_1_rds_encryption = Rule(
    id="cis_aws_3_2_1_rds_encryption",
    name="CIS AWS 3.2.1: RDS Encryption at Rest",
    description=(
        "RDS instances should have storage encryption enabled to protect data at rest "
        "and meet compliance requirements."
    ),
    output_model=RdsEncryptionOutput,
    facts=(_aws_rds_encryption_disabled,),
    tags=("storage", "rds", "encryption", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="6.0.0",
            requirement="3.2.1",
        ),
    ),
)


# =============================================================================
# TODO: CIS AWS 3.1.1: S3 bucket policy is set to deny HTTP requests
# Missing datamodel or evidence: parsed S3 bucket policy statements, conditions, and effect evaluation for aws:SecureTransport or s3:TlsVersion deny rules
# =============================================================================

# =============================================================================
# TODO: CIS AWS 3.1.3: All data in Amazon S3 has been discovered, classified, and secured when necessary
# Missing datamodel or evidence: Macie job configuration or equivalent S3 data classification findings
# =============================================================================

# =============================================================================
# TODO: CIS AWS 3.2.2: Auto Minor Version Upgrade is enabled for RDS instances
# Missing datamodel or evidence: RDS field auto_minor_version_upgrade
# =============================================================================

# =============================================================================
# TODO: CIS AWS 3.2.3: RDS instances are not publicly accessible
# Missing datamodel or evidence: none; current RDS nodes already expose publicly_accessible, but the corresponding rule is not implemented yet
# =============================================================================

# =============================================================================
# TODO: CIS AWS 3.2.4: Multi-AZ deployments are used for enhanced availability in Amazon RDS
# Missing datamodel or evidence: RDS field multi_az
# =============================================================================

# =============================================================================
# TODO: CIS AWS 3.3.1: Encryption is enabled for EFS file systems
# Missing datamodel or evidence: EFS file system inventory with encrypted state
# =============================================================================
