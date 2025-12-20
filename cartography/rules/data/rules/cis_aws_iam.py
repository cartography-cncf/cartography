"""
CIS AWS IAM Security Checks

Implements CIS AWS Foundations Benchmark Section 1: Identity and Access Management
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
        text="AWS IAM Best Practices",
        url="https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html",
    ),
]


# =============================================================================
# CIS 1.14: Access keys not rotated in 90 days
# Main node: AccountAccessKey
# =============================================================================
class AccessKeyNotRotatedOutput(Finding):
    """Output model for access key rotation check."""

    access_key_id: str | None = None
    user_name: str | None = None
    user_arn: str | None = None
    key_create_date: str | None = None
    days_since_rotation: int | None = None
    account_id: str | None = None
    account: str | None = None


_aws_access_key_not_rotated = Fact(
    id="aws_access_key_not_rotated",
    name="AWS access keys not rotated in 90 days",
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
    WITH a, user, key
    WHERE date(datetime(replace(toString(key.createdate), ' ', 'T'))) < date() - duration('P90D')
    RETURN
        key.accesskeyid AS access_key_id,
        user.name AS user_name,
        user.arn AS user_arn,
        key.createdate AS key_create_date,
        duration.inDays(date(datetime(replace(toString(key.createdate), ' ', 'T'))), date()).days AS days_since_rotation,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
      AND key.createdate IS NOT NULL
      AND key.createdate <> 'None'
    WITH p, a, user, key
    WHERE date(datetime(replace(toString(key.createdate), ' ', 'T'))) < date() - duration('P90D')
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_1_14_access_key_not_rotated = Rule(
    id="cis_1_14_access_key_not_rotated",
    name="CIS 1.14: Access Keys Not Rotated",
    description=(
        "Access keys should be rotated every 90 days or less to reduce the window "
        "of opportunity for compromised keys to be used maliciously."
    ),
    output_model=AccessKeyNotRotatedOutput,
    facts=(_aws_access_key_not_rotated,),
    tags=("cis_1_14", "cis:aws-5.0", "iam", "credentials"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS 1.12: Unused credentials (45+ days)
# Main node: AccountAccessKey
# =============================================================================
class UnusedCredentialsOutput(Finding):
    """Output model for unused credentials check."""

    access_key_id: str | None = None
    user_name: str | None = None
    user_arn: str | None = None
    last_used_date: str | None = None
    key_create_date: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_unused_credentials = Fact(
    id="aws_unused_credentials",
    name="AWS access keys unused for 45+ days",
    description=(
        "Detects IAM access keys that have not been used in the last 45 days. "
        "Unused credentials should be disabled to reduce the attack surface."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    WITH a, user, key,
         CASE WHEN key.lastuseddate IS NOT NULL AND key.lastuseddate <> 'None'
              THEN date(datetime(replace(toString(key.lastuseddate), ' ', 'T')))
              ELSE null END AS last_used,
         CASE WHEN key.createdate IS NOT NULL AND key.createdate <> 'None'
              THEN date(datetime(replace(toString(key.createdate), ' ', 'T')))
              ELSE null END AS created
    WHERE (last_used IS NOT NULL AND last_used < date() - duration('P45D'))
       OR (last_used IS NULL AND created IS NOT NULL AND created < date() - duration('P45D'))
    RETURN
        key.accesskeyid AS access_key_id,
        user.name AS user_name,
        user.arn AS user_arn,
        key.lastuseddate AS last_used_date,
        key.createdate AS key_create_date,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    WITH p, a, user, key,
         CASE WHEN key.lastuseddate IS NOT NULL AND key.lastuseddate <> 'None'
              THEN date(datetime(replace(toString(key.lastuseddate), ' ', 'T')))
              ELSE null END AS last_used,
         CASE WHEN key.createdate IS NOT NULL AND key.createdate <> 'None'
              THEN date(datetime(replace(toString(key.createdate), ' ', 'T')))
              ELSE null END AS created
    WHERE (last_used IS NOT NULL AND last_used < date() - duration('P45D'))
       OR (last_used IS NULL AND created IS NOT NULL AND created < date() - duration('P45D'))
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_1_12_unused_credentials = Rule(
    id="cis_1_12_unused_credentials",
    name="CIS 1.12: Unused Credentials",
    description=(
        "Credentials unused for 45 days or greater should be disabled to reduce "
        "the attack surface and prevent unauthorized access."
    ),
    output_model=UnusedCredentialsOutput,
    facts=(_aws_unused_credentials,),
    tags=("cis_1_12", "cis:aws-5.0", "iam", "credentials"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS 1.15: Users with directly attached policies
# Main node: AWSUser
# =============================================================================
class UserDirectPoliciesOutput(Finding):
    """Output model for user direct policies check."""

    user_arn: str | None = None
    user_name: str | None = None
    policy_name: str | None = None
    policy_arn: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_user_direct_policies = Fact(
    id="aws_user_direct_policies",
    name="AWS IAM users with directly attached policies",
    description=(
        "Detects IAM users that have policies directly attached to them instead of "
        "through IAM groups. Best practice is to manage permissions through groups "
        "to simplify access management and reduce errors."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:POLICY]->(policy:AWSPolicy)
    RETURN
        user.arn AS user_arn,
        user.name AS user_name,
        policy.name AS policy_name,
        policy.arn AS policy_arn,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:POLICY]->(policy:AWSPolicy)
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_1_15_user_direct_policies = Rule(
    id="cis_1_15_user_direct_policies",
    name="CIS 1.15: Users With Direct Policy Attachments",
    description=(
        "IAM users should receive permissions only through groups. Direct policy "
        "attachments make permission management complex and error-prone."
    ),
    output_model=UserDirectPoliciesOutput,
    facts=(_aws_user_direct_policies,),
    tags=("cis_1_15", "cis:aws-5.0", "iam", "policies"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS 1.13: Users with multiple active access keys
# Main node: AWSUser
# =============================================================================
class MultipleAccessKeysOutput(Finding):
    """Output model for multiple access keys check."""

    user_arn: str | None = None
    user_name: str | None = None
    active_key_count: int | None = None
    access_key_ids: list[str] | None = None
    account_id: str | None = None
    account: str | None = None


_aws_multiple_access_keys = Fact(
    id="aws_multiple_access_keys",
    name="AWS IAM users with multiple active access keys",
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
        user.arn AS user_arn,
        user.name AS user_name,
        size(keys) AS active_key_count,
        [k IN keys | k.accesskeyid] AS access_key_ids,
        a.id AS account_id,
        a.name AS account
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

cis_1_13_multiple_access_keys = Rule(
    id="cis_1_13_multiple_access_keys",
    name="CIS 1.13: Users With Multiple Active Access Keys",
    description=(
        "Each IAM user should have only one active access key. Multiple active keys "
        "increase the attack surface and complicate key rotation."
    ),
    output_model=MultipleAccessKeysOutput,
    facts=(_aws_multiple_access_keys,),
    tags=("cis_1_13", "cis:aws-5.0", "iam", "credentials"),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS 1.18: Expired SSL/TLS certificates
# Main node: ACMCertificate
# =============================================================================
class ExpiredCertificatesOutput(Finding):
    """Output model for expired certificates check."""

    domain_name: str | None = None
    certificate_arn: str | None = None
    status: str | None = None
    expiry_date: str | None = None
    certificate_type: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_expired_certificates = Fact(
    id="aws_expired_certificates",
    name="AWS expired SSL/TLS certificates",
    description=(
        "Detects ACM certificates that have expired. Expired certificates "
        "should be removed to maintain security hygiene and avoid confusion "
        "with valid certificates."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(cert:ACMCertificate)
    WHERE cert.not_after IS NOT NULL
      AND cert.not_after <> 'None'
    WITH a, cert
    WHERE date(datetime(replace(toString(cert.not_after), ' ', 'T'))) < date()
    RETURN
        cert.domainname AS domain_name,
        cert.arn AS certificate_arn,
        cert.status AS status,
        cert.not_after AS expiry_date,
        cert.type AS certificate_type,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(cert:ACMCertificate)
    WHERE cert.not_after IS NOT NULL
      AND cert.not_after <> 'None'
    WITH p, a, cert
    WHERE date(datetime(replace(toString(cert.not_after), ' ', 'T'))) < date()
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_1_18_expired_certificates = Rule(
    id="cis_1_18_expired_certificates",
    name="CIS 1.18: Expired SSL/TLS Certificates",
    description=(
        "Expired SSL/TLS certificates should be removed from ACM to maintain "
        "security hygiene and avoid confusion with valid certificates."
    ),
    output_model=ExpiredCertificatesOutput,
    facts=(_aws_expired_certificates,),
    tags=("cis_1_18", "cis:aws-5.0", "certificates", "acm"),
    version="1.0.0",
    references=CIS_REFERENCES,
)
