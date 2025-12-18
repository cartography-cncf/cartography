"""
CIS AWS Logging Security Checks

Implements CIS AWS Foundations Benchmark Section 3: Logging
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
# CIS 3.1: Ensure CloudTrail is enabled in all regions
# -----------------------------------------------------------------------------
_cis_3_1_cloudtrail_not_multi_region = Fact(
    id="cis_3_1_cloudtrail_not_multi_region",
    name="CIS 3.1: CloudTrail not configured for all regions",
    description=(
        "Detects CloudTrail trails that are not configured as multi-region. "
        "AWS CloudTrail should be enabled in all regions to ensure complete "
        "visibility into API activity across the entire AWS infrastructure."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.is_multi_region_trail IS NULL OR trail.is_multi_region_trail = false
    RETURN
        a.id AS account_id,
        a.name AS account,
        trail.name AS trail_name,
        trail.arn AS trail_arn,
        trail.home_region AS home_region,
        trail.is_multi_region_trail AS is_multi_region
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.is_multi_region_trail IS NULL OR trail.is_multi_region_trail = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 3.4: Ensure CloudTrail log file validation is enabled
# -----------------------------------------------------------------------------
_cis_3_4_cloudtrail_log_validation_disabled = Fact(
    id="cis_3_4_cloudtrail_log_validation_disabled",
    name="CIS 3.4: CloudTrail log file validation not enabled",
    description=(
        "Detects CloudTrail trails that do not have log file validation enabled. "
        "Log file validation ensures the integrity of CloudTrail log files by "
        "generating a digitally signed digest file."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.log_file_validation_enabled IS NULL OR trail.log_file_validation_enabled = false
    RETURN
        a.id AS account_id,
        a.name AS account,
        trail.name AS trail_name,
        trail.arn AS trail_arn,
        trail.home_region AS home_region,
        trail.log_file_validation_enabled AS log_validation_enabled
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.log_file_validation_enabled IS NULL OR trail.log_file_validation_enabled = false
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 3.5: Ensure CloudTrail logs are integrated with CloudWatch Logs
# -----------------------------------------------------------------------------
_cis_3_5_cloudtrail_no_cloudwatch = Fact(
    id="cis_3_5_cloudtrail_no_cloudwatch",
    name="CIS 3.5: CloudTrail not integrated with CloudWatch Logs",
    description=(
        "Detects CloudTrail trails that are not sending logs to CloudWatch Logs. "
        "Integrating CloudTrail with CloudWatch Logs enables real-time analysis "
        "and alerting on API activity."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.cloudwatch_logs_log_group_arn IS NULL OR trail.cloudwatch_logs_log_group_arn = ''
    RETURN
        a.id AS account_id,
        a.name AS account,
        trail.name AS trail_name,
        trail.arn AS trail_arn,
        trail.home_region AS home_region,
        trail.cloudwatch_logs_log_group_arn AS cloudwatch_log_group
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.cloudwatch_logs_log_group_arn IS NULL OR trail.cloudwatch_logs_log_group_arn = ''
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 3.7: Ensure CloudTrail logs are encrypted at rest using KMS CMKs
# -----------------------------------------------------------------------------
_cis_3_7_cloudtrail_not_encrypted = Fact(
    id="cis_3_7_cloudtrail_not_encrypted",
    name="CIS 3.7: CloudTrail logs not encrypted with KMS",
    description=(
        "Detects CloudTrail trails that are not configured to encrypt logs "
        "using AWS KMS customer managed keys (CMKs). Encrypting logs provides "
        "an additional layer of security for sensitive API activity data."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.kms_key_id IS NULL OR trail.kms_key_id = ''
    RETURN
        a.id AS account_id,
        a.name AS account,
        trail.name AS trail_name,
        trail.arn AS trail_arn,
        trail.home_region AS home_region,
        trail.kms_key_id AS kms_key_id
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(trail:CloudTrailTrail)
    WHERE trail.kms_key_id IS NULL OR trail.kms_key_id = ''
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# Output Model
# -----------------------------------------------------------------------------
class CISAWSLoggingOutput(Finding):
    """Output model for CIS AWS Logging checks."""
    account_id: str | None = None
    account: str | None = None
    trail_name: str | None = None
    trail_arn: str | None = None
    home_region: str | None = None
    is_multi_region: bool | None = None
    log_validation_enabled: bool | None = None
    cloudwatch_log_group: str | None = None
    kms_key_id: str | None = None


# -----------------------------------------------------------------------------
# Rule Definition
# -----------------------------------------------------------------------------
cis_aws_logging = Rule(
    id="cis_aws_logging",
    name="CIS AWS Logging Security Checks",
    description=(
        "CIS AWS Foundations Benchmark - Logging controls. "
        "Detects CloudTrail misconfigurations including missing multi-region "
        "coverage, disabled log validation, and missing encryption."
    ),
    output_model=CISAWSLoggingOutput,
    facts=(
        _cis_3_1_cloudtrail_not_multi_region,
        _cis_3_4_cloudtrail_log_validation_disabled,
        _cis_3_5_cloudtrail_no_cloudwatch,
        _cis_3_7_cloudtrail_not_encrypted,
    ),
    tags=("cis", "compliance", "cis_aws_5.0", "logging", "cloudtrail"),
    version="1.0.0",
    references=[
        RuleReference(
            text="CIS AWS Foundations Benchmark v5.0",
            url="https://www.cisecurity.org/benchmark/amazon_web_services",
        ),
        RuleReference(
            text="AWS CloudTrail Best Practices",
            url="https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html",
        ),
    ],
)
