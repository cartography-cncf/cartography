"""
CIS AWS Logging Security Checks

Implements CIS AWS Foundations Benchmark Section 3: Logging
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
        text="AWS CloudTrail Best Practices",
        url="https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html",
    ),
]


# =============================================================================
# CIS AWS 3.1: CloudTrail Multi-Region
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
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_3_1_cloudtrail_multi_region = Rule(
    id="cis_3_1_cloudtrail_multi_region",
    name="CIS AWS 3.1: CloudTrail Multi-Region",
    description=(
        "CloudTrail should be enabled in all regions to ensure complete visibility "
        "into API activity across the entire AWS infrastructure."
    ),
    output_model=CloudTrailMultiRegionOutput,
    facts=(_aws_cloudtrail_not_multi_region,),
    tags=("cis:3.1", "cis:aws-5.0", "logging", "cloudtrail", "stride:repudiation"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 3.4: CloudTrail Log File Validation
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
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_3_4_cloudtrail_log_validation = Rule(
    id="cis_3_4_cloudtrail_log_validation",
    name="CIS AWS 3.4: CloudTrail Log File Validation",
    description=(
        "CloudTrail should have log file validation enabled to ensure the integrity "
        "of log files through digitally signed digest files."
    ),
    output_model=CloudTrailLogValidationOutput,
    facts=(_aws_cloudtrail_log_validation_disabled,),
    tags=(
        "cis:3.4",
        "cis:aws-5.0",
        "logging",
        "cloudtrail",
        "stride:repudiation",
        "stride:tampering",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 3.5: CloudTrail CloudWatch Integration
# Main node: CloudTrailTrail
# =============================================================================
class CloudTrailCloudWatchOutput(Finding):
    """Output model for CloudTrail CloudWatch integration check."""

    trail_name: str | None = None
    trail_arn: str | None = None
    home_region: str | None = None
    cloudwatch_log_group: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_cloudtrail_no_cloudwatch = Fact(
    id="aws_cloudtrail_no_cloudwatch",
    name="AWS CloudTrail not integrated with CloudWatch Logs",
    description=(
        "Detects CloudTrail trails that are not sending logs to CloudWatch Logs. "
        "Integrating CloudTrail with CloudWatch Logs enables real-time analysis "
        "and alerting on API activity."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.cloudwatch_logs_log_group_arn IS NULL OR trail.cloudwatch_logs_log_group_arn = ''
    RETURN
        trail.name AS trail_name,
        trail.arn AS trail_arn,
        trail.home_region AS home_region,
        trail.cloudwatch_logs_log_group_arn AS cloudwatch_log_group,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.cloudwatch_logs_log_group_arn IS NULL OR trail.cloudwatch_logs_log_group_arn = ''
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_3_5_cloudtrail_cloudwatch = Rule(
    id="cis_3_5_cloudtrail_cloudwatch",
    name="CIS AWS 3.5: CloudTrail CloudWatch Integration",
    description=(
        "CloudTrail should be integrated with CloudWatch Logs to enable real-time "
        "analysis and alerting on API activity."
    ),
    output_model=CloudTrailCloudWatchOutput,
    facts=(_aws_cloudtrail_no_cloudwatch,),
    tags=(
        "cis:3.5",
        "cis:aws-5.0",
        "logging",
        "cloudtrail",
        "cloudwatch",
        "stride:repudiation",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 3.7: CloudTrail KMS Encryption
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
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_3_7_cloudtrail_encryption = Rule(
    id="cis_3_7_cloudtrail_encryption",
    name="CIS AWS 3.7: CloudTrail KMS Encryption",
    description=(
        "CloudTrail logs should be encrypted using AWS KMS customer managed keys "
        "to provide an additional layer of security for sensitive API activity data."
    ),
    output_model=CloudTrailEncryptionOutput,
    facts=(_aws_cloudtrail_not_encrypted,),
    tags=(
        "cis:3.7",
        "cis:aws-5.0",
        "logging",
        "cloudtrail",
        "encryption",
        "stride:information_disclosure",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)
