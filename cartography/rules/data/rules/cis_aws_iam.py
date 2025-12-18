"""
CIS AWS IAM Security Checks

Implements CIS AWS Foundations Benchmark Section 1: Identity and Access Management
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
# CIS 1.14: Ensure access keys are rotated every 90 days or less
# -----------------------------------------------------------------------------
_cis_1_14_access_keys_not_rotated = Fact(
    id="cis_1_14_access_keys_not_rotated",
    name="CIS 1.14: Access keys not rotated in 90 days",
    description=(
        "Detects IAM access keys that have not been rotated within the last 90 days. "
        "Rotating access keys regularly reduces the window of opportunity for "
        "compromised keys to be used maliciously."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    AND key.createdate IS NOT NULL
    AND key.createdate <> 'None'
    AND date(datetime(replace(key.createdate, ' ', 'T'))) < date() - duration('P90D')
    RETURN
        a.id AS account_id,
        a.name AS account,
        user.name AS user_name,
        user.arn AS user_arn,
        key.accesskeyid AS access_key_id,
        key.createdate AS key_create_date,
        duration.inDays(date(datetime(replace(key.createdate, ' ', 'T'))), date()).days AS days_since_rotation
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    AND key.createdate IS NOT NULL
    AND key.createdate <> 'None'
    AND date(datetime(replace(key.createdate, ' ', 'T'))) < date() - duration('P90D')
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 1.15: Ensure IAM Users receive permissions only through groups
# -----------------------------------------------------------------------------
_cis_1_15_user_direct_policies = Fact(
    id="cis_1_15_user_direct_policies",
    name="CIS 1.15: IAM users with directly attached policies",
    description=(
        "Detects IAM users that have policies directly attached to them instead of "
        "through IAM groups. Best practice is to manage permissions through groups "
        "to simplify access management and reduce errors."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:POLICY]->(policy:AWSPolicy)
    RETURN
        a.id AS account_id,
        a.name AS account,
        user.name AS user_name,
        user.arn AS user_arn,
        policy.name AS policy_name,
        policy.arn AS policy_arn
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:POLICY]->(policy:AWSPolicy)
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 1.12: Ensure credentials unused for 45 days or greater are disabled
# -----------------------------------------------------------------------------
_cis_1_12_unused_credentials = Fact(
    id="cis_1_12_unused_credentials",
    name="CIS 1.12: Access keys unused for 45+ days",
    description=(
        "Detects IAM access keys that have not been used in the last 45 days. "
        "Unused credentials should be disabled to reduce the attack surface."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    AND (
        (key.lastuseddate IS NOT NULL AND key.lastuseddate <> 'None'
         AND date(datetime(replace(key.lastuseddate, ' ', 'T'))) < date() - duration('P45D'))
        OR ((key.lastuseddate IS NULL OR key.lastuseddate = 'None')
            AND key.createdate IS NOT NULL AND key.createdate <> 'None'
            AND date(datetime(replace(key.createdate, ' ', 'T'))) < date() - duration('P45D'))
    )
    RETURN
        a.id AS account_id,
        a.name AS account,
        user.name AS user_name,
        user.arn AS user_arn,
        key.accesskeyid AS access_key_id,
        key.lastuseddate AS last_used_date,
        key.createdate AS key_create_date
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    AND (
        (key.lastuseddate IS NOT NULL AND key.lastuseddate <> 'None'
         AND date(datetime(replace(key.lastuseddate, ' ', 'T'))) < date() - duration('P45D'))
        OR ((key.lastuseddate IS NULL OR key.lastuseddate = 'None')
            AND key.createdate IS NOT NULL AND key.createdate <> 'None'
            AND date(datetime(replace(key.createdate, ' ', 'T'))) < date() - duration('P45D'))
    )
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 1.13: Ensure there is only one active access key available for any single IAM user
# -----------------------------------------------------------------------------
_cis_1_13_multiple_access_keys = Fact(
    id="cis_1_13_multiple_access_keys",
    name="CIS 1.13: Users with multiple active access keys",
    description=(
        "Detects IAM users that have more than one active access key. Having multiple "
        "active keys increases the attack surface and makes key rotation more complex."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    WITH a, user, collect(key) AS keys
    WHERE size(keys) > 1
    RETURN
        a.id AS account_id,
        a.name AS account,
        user.name AS user_name,
        user.arn AS user_arn,
        size(keys) AS active_key_count,
        [k IN keys | k.accesskeyid] AS access_key_ids
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    WITH a, user, collect(key) AS keys, collect(p) AS paths
    WHERE size(keys) > 1
    UNWIND paths AS path
    RETURN path
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# Output Model
# -----------------------------------------------------------------------------
class CISAWSIAMOutput(Finding):
    """Output model for CIS AWS IAM checks."""
    account_id: str | None = None
    account: str | None = None
    user_name: str | None = None
    user_arn: str | None = None
    access_key_id: str | None = None
    key_create_date: str | None = None
    last_used_date: str | None = None
    days_since_rotation: int | None = None
    active_key_count: int | None = None
    policy_name: str | None = None
    policy_arn: str | None = None


# -----------------------------------------------------------------------------
# Rule Definition
# -----------------------------------------------------------------------------
cis_aws_iam = Rule(
    id="cis_aws_iam",
    name="CIS AWS IAM Security Checks",
    description=(
        "CIS AWS Foundations Benchmark - Identity and Access Management controls. "
        "Detects IAM misconfigurations including access key rotation issues, "
        "users with direct policies, and unused credentials."
    ),
    output_model=CISAWSIAMOutput,
    facts=(
        _cis_1_14_access_keys_not_rotated,
        _cis_1_15_user_direct_policies,
        _cis_1_12_unused_credentials,
        _cis_1_13_multiple_access_keys,
    ),
    tags=("cis", "compliance", "cis_aws_5.0", "iam"),
    version="1.0.0",
    references=[
        RuleReference(
            text="CIS AWS Foundations Benchmark v5.0",
            url="https://www.cisecurity.org/benchmark/amazon_web_services",
        ),
        RuleReference(
            text="AWS IAM Best Practices",
            url="https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html",
        ),
    ],
)
