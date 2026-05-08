"""
CIS AWS Logging Security Checks

Implements CIS AWS Foundations Benchmark Section 4: Logging
Based on CIS AWS Foundations Benchmark v6.0.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.data.frameworks.cis import cis_aws
from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
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
        text="AWS CloudTrail Best Practices",
        url="https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html",
    ),
]


# =============================================================================
# CIS AWS 4.1: CloudTrail is enabled in all regions
# Main node: CloudTrailTrail
# =============================================================================
class CloudTrailMultiRegionOutput(Finding):
    """Output model for CloudTrail multi-region check."""

    trail_name: str | None = None
    trail_arn: str | None = None
    home_region: str | None = None
    is_multi_region: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_cloudtrail_not_multi_region = Fact(
    id="aws_cloudtrail_not_multi_region",
    name="AWS CloudTrail not configured for all regions",
    description=(
        "Detects CloudTrail trails that are not configured as multi-region. "
        "AWS CloudTrail should be enabled in all regions to ensure complete "
        "visibility into API activity across the entire AWS infrastructure."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.is_multi_region_trail IS NULL OR trail.is_multi_region_trail = false
    RETURN
        trail.name AS trail_name,
        trail.arn AS trail_arn,
        trail.home_region AS home_region,
        trail.is_multi_region_trail AS is_multi_region,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.is_multi_region_trail IS NULL OR trail.is_multi_region_trail = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (trail:CloudTrailTrail)
    RETURN COUNT(trail) AS count
    """,
    asset_id_field="trail_arn",
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_4_1_cloudtrail_multi_region = Rule(
    id="cis_aws_4_1_cloudtrail_multi_region",
    name="CIS AWS 4.1: CloudTrail Multi-Region",
    description=(
        "CloudTrail should be enabled in all regions to ensure complete visibility "
        "into API activity across the entire AWS infrastructure."
    ),
    output_model=CloudTrailMultiRegionOutput,
    facts=(_aws_cloudtrail_not_multi_region,),
    tags=("logging", "cloudtrail", "stride:repudiation"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("4.1"),
        iso27001_annex_a("8.15"),
        iso27001_annex_a("8.16"),
    ),
)


# =============================================================================
# CIS AWS 4.2: CloudTrail Log File Validation
# Main node: CloudTrailTrail
# =============================================================================
class CloudTrailLogValidationOutput(Finding):
    """Output model for CloudTrail log validation check."""

    trail_name: str | None = None
    trail_arn: str | None = None
    home_region: str | None = None
    log_validation_enabled: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_cloudtrail_log_validation_disabled = Fact(
    id="aws_cloudtrail_log_validation_disabled",
    name="AWS CloudTrail log file validation not enabled",
    description=(
        "Detects CloudTrail trails that do not have log file validation enabled. "
        "Log file validation ensures the integrity of CloudTrail log files by "
        "generating a digitally signed digest file."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.log_file_validation_enabled IS NULL OR trail.log_file_validation_enabled = false
    RETURN
        trail.name AS trail_name,
        trail.arn AS trail_arn,
        trail.home_region AS home_region,
        trail.log_file_validation_enabled AS log_validation_enabled,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.log_file_validation_enabled IS NULL OR trail.log_file_validation_enabled = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (trail:CloudTrailTrail)
    RETURN COUNT(trail) AS count
    """,
    asset_id_field="trail_arn",
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_4_2_cloudtrail_log_validation = Rule(
    id="cis_aws_4_2_cloudtrail_log_validation",
    name="CIS AWS 4.2: CloudTrail Log File Validation",
    description=(
        "CloudTrail should have log file validation enabled to ensure the integrity "
        "of log files through digitally signed digest files."
    ),
    output_model=CloudTrailLogValidationOutput,
    facts=(_aws_cloudtrail_log_validation_disabled,),
    tags=("logging", "cloudtrail", "stride:repudiation", "stride:tampering"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("4.2"),
        iso27001_annex_a("8.15"),
    ),
)


# =============================================================================
# CIS AWS 4.4: Server access logging on the CloudTrail S3 bucket
# Main node: S3Bucket
# =============================================================================
class CloudTrailBucketAccessLoggingOutput(Finding):
    """Output model for CloudTrail S3 bucket access logging check."""

    bucket_name: str | None = None
    bucket_id: str | None = None
    region: str | None = None
    logging_enabled: bool | None = None
    trail_names: list[str] | None = None
    trail_arns: list[str] | None = None
    account_id: str | None = None
    account: str | None = None


_aws_cloudtrail_bucket_access_logging_disabled = Fact(
    id="aws_cloudtrail_bucket_access_logging_disabled",
    name="AWS CloudTrail S3 bucket without server access logging",
    description=(
        "Detects S3 buckets that are CloudTrail destinations but do not have "
        "server access logging enabled. Access logging on the CloudTrail bucket "
        "captures requests against audit logs themselves."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)-[:LOGS_TO]->(bucket:S3Bucket)
    WHERE bucket.logging_enabled IS NULL OR bucket.logging_enabled = false
    RETURN
        bucket.name AS bucket_name,
        bucket.id AS bucket_id,
        bucket.region AS region,
        bucket.logging_enabled AS logging_enabled,
        collect(DISTINCT trail.name) AS trail_names,
        collect(DISTINCT trail.arn) AS trail_arns,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)-[:LOGS_TO]->(bucket:S3Bucket)
    WHERE bucket.logging_enabled IS NULL OR bucket.logging_enabled = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (:CloudTrailTrail)-[:LOGS_TO]->(bucket:S3Bucket)
    RETURN COUNT(DISTINCT bucket) AS count
    """,
    asset_id_field="bucket_id",
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_4_4_cloudtrail_bucket_access_logging = Rule(
    id="cis_aws_4_4_cloudtrail_bucket_access_logging",
    name="CIS AWS 4.4: CloudTrail S3 Bucket Access Logging",
    description=(
        "Server access logging should be enabled on the S3 bucket that stores "
        "CloudTrail logs to capture requests against the audit logs themselves."
    ),
    output_model=CloudTrailBucketAccessLoggingOutput,
    facts=(_aws_cloudtrail_bucket_access_logging_disabled,),
    tags=("logging", "cloudtrail", "s3", "stride:repudiation"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("4.4"),
        iso27001_annex_a("8.15"),
    ),
)


# =============================================================================
# CIS AWS 4.5: CloudTrail KMS Encryption
# Main node: CloudTrailTrail
# =============================================================================
class CloudTrailEncryptionOutput(Finding):
    """Output model for CloudTrail encryption check."""

    trail_name: str | None = None
    trail_arn: str | None = None
    home_region: str | None = None
    kms_key_id: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_cloudtrail_not_encrypted = Fact(
    id="aws_cloudtrail_not_encrypted",
    name="AWS CloudTrail logs not encrypted with KMS",
    description=(
        "Detects CloudTrail trails that are not configured to encrypt logs "
        "using AWS KMS customer managed keys (CMKs). Encrypting logs provides "
        "an additional layer of security for sensitive API activity data."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.kms_key_id IS NULL OR trail.kms_key_id = ''
    RETURN
        trail.name AS trail_name,
        trail.arn AS trail_arn,
        trail.home_region AS home_region,
        trail.kms_key_id AS kms_key_id,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.kms_key_id IS NULL OR trail.kms_key_id = ''
    RETURN *
    """,
    cypher_count_query="""
    MATCH (trail:CloudTrailTrail)
    RETURN COUNT(trail) AS count
    """,
    asset_id_field="trail_arn",
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_4_5_cloudtrail_encryption = Rule(
    id="cis_aws_4_5_cloudtrail_encryption",
    name="CIS AWS 4.5: CloudTrail KMS Encryption",
    description=(
        "CloudTrail logs should be encrypted using AWS KMS customer managed keys "
        "to provide an additional layer of security for sensitive API activity data."
    ),
    output_model=CloudTrailEncryptionOutput,
    facts=(_aws_cloudtrail_not_encrypted,),
    tags=("logging", "cloudtrail", "encryption", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("4.5"),
        iso27001_annex_a("8.24"),
    ),
)

# =============================================================================
# TODO: CIS AWS 4.3: AWS Config is enabled in all regions
# Missing datamodel or evidence: AWS Config recorder and delivery channel inventory plus recorder status per region
# =============================================================================

# =============================================================================
# TODO: CIS AWS 4.6: Rotation for customer-created symmetric CMKs is enabled
# Missing datamodel or evidence: KMS key inventory including KeySpec or equivalent symmetric-key discriminator and KeyRotationEnabled state
# =============================================================================

# =============================================================================
# TODO: CIS AWS 4.7: VPC flow logging is enabled in all VPCs
# Missing datamodel or evidence: VPC Flow Log inventory and delivery status per VPC
# =============================================================================

# =============================================================================
# TODO: CIS AWS 4.8: Object-level logging for write events is enabled for S3 buckets
# Missing datamodel or evidence: CloudTrail event selectors and S3 data event coverage for write-only or all object events
# =============================================================================

# =============================================================================
# TODO: CIS AWS 4.9: Object-level logging for read events is enabled for S3 buckets
# Missing datamodel or evidence: CloudTrail event selectors and S3 data event coverage for read-only or all object events
# =============================================================================

# =============================================================================
# TODO: CIS AWS 5.16: AWS Security Hub is enabled
# Missing datamodel or evidence: Security Hub regional hub subscription state
# =============================================================================

# =============================================================================
# TODO: ISO 27001 Annex A 8.15 and 8.16: Broader logging and monitoring coverage
# Missing datamodel or evidence: AWS Config recorder status, CloudWatch alarm
# configuration, metric filters, Security Hub state, VPC flow logs, and S3 data
# event selectors.
# =============================================================================
