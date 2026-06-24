"""
CIS AWS IAM Security Checks

Implements CIS AWS Foundations Benchmark Section 2: Identity and Access Management
Based on CIS AWS Foundations Benchmark v6.0.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BeforeValidator

from cartography.rules.data.frameworks.cis import cis_aws
from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference
from cartography.util import to_datetime

# Type alias for datetime fields that may come from Neo4j as neo4j.time.DateTime
Neo4jDateTime = Annotated[datetime | None, BeforeValidator(to_datetime)]

CIS_REFERENCES = [
    RuleReference(
        text="CIS AWS Foundations Benchmark v6.0.0",
        url="https://www.cisecurity.org/benchmark/amazon_web_services",
    ),
    RuleReference(
        text="AWS IAM Best Practices",
        url="https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html",
    ),
]


# =============================================================================
# CIS AWS 2.13: Access keys not rotated in 90 days
# Main node: AccountAccessKey
# =============================================================================
class AccessKeyNotRotatedOutput(Finding):
    """Output model for access key rotation check."""

    user_name: str | None = None
    access_key_id: str | None = None
    user_arn: str | None = None
    key_create_date: Neo4jDateTime = None
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
      AND key.createdate_dt IS NOT NULL
      AND date(datetime(key.createdate_dt)) < date() - duration('P90D')
    RETURN
        key.accesskeyid AS access_key_id,
        user.name AS user_name,
        user.arn AS user_arn,
        key.createdate_dt AS key_create_date,
        duration.inDays(date(datetime(key.createdate_dt)), date()).days AS days_since_rotation,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
      AND key.createdate_dt IS NOT NULL
      AND date(datetime(key.createdate_dt)) < date() - duration('P90D')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (key:AccountAccessKey)
    RETURN COUNT(key) AS count
    """,
    identity_fields=("access_key_id",),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

aws_access_keys_not_rotated = Rule(
    id="aws_access_keys_not_rotated",
    name="Access Keys Not Rotated",
    description=(
        "Access keys should be rotated every 90 days or less to reduce the window "
        "of opportunity for compromised keys to be used maliciously."
    ),
    output_model=AccessKeyNotRotatedOutput,
    facts=(_aws_access_key_not_rotated,),
    tags=("iam", "credentials", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("2.13"),
        iso27001_annex_a("5.17"),
    ),
)


# =============================================================================
# CIS AWS 2.11: Credentials unused for 45 days or more
# Main node: AccountAccessKey
# =============================================================================
class UnusedCredentialsOutput(Finding):
    """Output model for unused credentials check."""

    user_name: str | None = None
    access_key_id: str | None = None
    user_arn: str | None = None
    last_used_date: Neo4jDateTime = None
    key_create_date: Neo4jDateTime = None
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
    WITH a, user, key
    WHERE (key.lastuseddate_dt IS NOT NULL AND date(datetime(key.lastuseddate_dt)) < date() - duration('P45D'))
       OR (key.lastuseddate_dt IS NULL AND key.createdate_dt IS NOT NULL
           AND date(datetime(key.createdate_dt)) < date() - duration('P45D'))
    RETURN
        key.accesskeyid AS access_key_id,
        user.name AS user_name,
        user.arn AS user_arn,
        key.lastuseddate_dt AS last_used_date,
        key.createdate_dt AS key_create_date,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AccountAccessKey)
    WHERE key.status = 'Active'
    WITH p, a, user, key
    WHERE (key.lastuseddate_dt IS NOT NULL AND date(datetime(key.lastuseddate_dt)) < date() - duration('P45D'))
       OR (key.lastuseddate_dt IS NULL AND key.createdate_dt IS NOT NULL
           AND date(datetime(key.createdate_dt)) < date() - duration('P45D'))
    RETURN *
    """,
    cypher_count_query="""
    MATCH (key:AccountAccessKey)
    RETURN COUNT(key) AS count
    """,
    identity_fields=("access_key_id",),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

aws_unused_credentials = Rule(
    id="aws_unused_credentials",
    name="Unused Credentials",
    description=(
        "Credentials unused for 45 days or greater should be disabled to reduce "
        "the attack surface and prevent unauthorized access."
    ),
    output_model=UnusedCredentialsOutput,
    facts=(_aws_unused_credentials,),
    tags=("iam", "credentials", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("2.11"),
        iso27001_annex_a("5.18"),
    ),
)


# =============================================================================
# CIS AWS 2.14: Users with directly attached policies
# Main node: AWSUser
# =============================================================================
class UserDirectPoliciesOutput(Finding):
    """Output model for user direct policies check."""

    user_name: str | None = None
    user_arn: str | None = None
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
    cypher_count_query="""
    MATCH (user:AWSUser)
    RETURN COUNT(user) AS count
    """,
    asset_id_field="user_arn",
    identity_fields=("user_arn", "policy_arn"),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

aws_users_with_direct_policy_attachments = Rule(
    id="aws_users_with_direct_policy_attachments",
    name="Users With Direct Policy Attachments",
    description=(
        "IAM users should receive permissions only through groups. Direct policy "
        "attachments make permission management complex and error-prone."
    ),
    output_model=UserDirectPoliciesOutput,
    facts=(_aws_user_direct_policies,),
    tags=("iam", "policies", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("2.14"),
        iso27001_annex_a("5.18"),
    ),
)


# =============================================================================
# CIS AWS 2.12: Users with multiple active access keys
# Main node: AWSUser
# =============================================================================
class MultipleAccessKeysOutput(Finding):
    """Output model for multiple access keys check."""

    user_name: str | None = None
    user_arn: str | None = None
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
    cypher_count_query="""
    MATCH (user:AWSUser)
    RETURN COUNT(user) AS count
    """,
    identity_fields=("user_arn",),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

aws_users_with_multiple_active_access_keys = Rule(
    id="aws_users_with_multiple_active_access_keys",
    name="Users With Multiple Active Access Keys",
    description=(
        "Each IAM user should have only one active access key. Multiple active keys "
        "increase the attack surface and complicate key rotation."
    ),
    output_model=MultipleAccessKeysOutput,
    facts=(_aws_multiple_access_keys,),
    tags=("iam", "credentials", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("2.12"),
        iso27001_annex_a("5.17"),
    ),
)


# =============================================================================
# CIS AWS 2.18: Expired SSL/TLS certificates
# Main node: ACMCertificate
# =============================================================================
class ExpiredCertificatesOutput(Finding):
    """Output model for expired certificates check."""

    domain_name: str | None = None
    certificate_arn: str | None = None
    status: str | None = None
    expiry_date: Neo4jDateTime = None
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
      AND date(cert.not_after) < date()
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
      AND date(cert.not_after) < date()
    RETURN *
    """,
    cypher_count_query="""
    MATCH (cert:ACMCertificate)
    RETURN COUNT(cert) AS count
    """,
    identity_fields=("certificate_arn",),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

aws_expired_ssl_tls_certificates = Rule(
    id="aws_expired_ssl_tls_certificates",
    name="Expired SSL/TLS Certificates",
    description=(
        "Expired SSL/TLS certificates should be removed from ACM to maintain "
        "security hygiene and avoid confusion with valid certificates."
    ),
    output_model=ExpiredCertificatesOutput,
    facts=(_aws_expired_certificates,),
    tags=("certificates", "acm", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("2.18"),
        iso27001_annex_a("8.24"),
    ),
)


# =============================================================================
# CIS AWS 2.3: No root user account access key exists
# Main node: AWSAccount
# =============================================================================
class RootAccessKeyOutput(Finding):
    """Output model for the root access key check."""

    account: str | None = None
    account_id: str | None = None
    account_access_keys_present: int | None = None


_aws_root_access_key_present = Fact(
    id="aws_root_access_key_present",
    name="AWS account with a root user access key",
    description=(
        "Detects AWS accounts whose root user has an access key. Root access keys "
        "grant unrestricted access to the account and cannot be scoped down, so they "
        "should be removed entirely. The signal comes from the IAM account summary "
        "field AccountAccessKeysPresent."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)
    WHERE a.account_access_keys_present = 1
    RETURN
        a.id AS account_id,
        a.name AS account,
        a.account_access_keys_present AS account_access_keys_present
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)
    WHERE a.account_access_keys_present = 1
    RETURN *
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount)
    WHERE a.account_access_keys_present IS NOT NULL
    RETURN COUNT(a) AS count
    """,
    identity_fields=("account_id",),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

aws_root_user_access_keys = Rule(
    id="aws_root_user_access_keys",
    name="Root User Access Keys",
    description=(
        "The root user should not have any access keys. Root access keys grant "
        "unrestricted access to the account and cannot be scoped down, so they "
        "should be removed entirely."
    ),
    output_model=RootAccessKeyOutput,
    facts=(_aws_root_access_key_present,),
    tags=("iam", "credentials", "root", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("2.3"),
        iso27001_annex_a("8.2"),
        iso27001_annex_a("5.17"),
    ),
)


# =============================================================================
# CIS AWS 2.4: MFA is enabled for the root user account
# Main node: AWSAccount
# =============================================================================
class RootMfaDisabledOutput(Finding):
    """Output model for the root MFA check."""

    account: str | None = None
    account_id: str | None = None
    account_mfa_enabled: int | None = None


_aws_root_mfa_disabled = Fact(
    id="aws_root_mfa_disabled",
    name="AWS account without MFA enabled for the root user",
    description=(
        "Detects AWS accounts where multi-factor authentication is not enabled for "
        "the root user. The root user has unrestricted access, so it should always be "
        "protected with MFA. The signal comes from the IAM account summary field "
        "AccountMFAEnabled."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)
    WHERE a.account_mfa_enabled = 0
    RETURN
        a.id AS account_id,
        a.name AS account,
        a.account_mfa_enabled AS account_mfa_enabled
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)
    WHERE a.account_mfa_enabled = 0
    RETURN *
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount)
    WHERE a.account_mfa_enabled IS NOT NULL
    RETURN COUNT(a) AS count
    """,
    identity_fields=("account_id",),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

aws_root_user_mfa_disabled = Rule(
    id="aws_root_user_mfa_disabled",
    name="Root User MFA Disabled",
    description=(
        "Multi-factor authentication should be enabled for the root user. The root "
        "user has unrestricted access to the account, so it must always be protected "
        "with an additional authentication factor."
    ),
    output_model=RootMfaDisabledOutput,
    facts=(_aws_root_mfa_disabled,),
    tags=("iam", "credentials", "root", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("2.4"),
        iso27001_annex_a("8.5"),
        iso27001_annex_a("8.2"),
    ),
)

# =============================================================================
# TODO: CIS AWS 2.7: IAM password policy requires minimum length of 14 or greater
# Missing datamodel or evidence: IAM account password policy fields such as MinimumPasswordLength
# =============================================================================

# =============================================================================
# TODO: CIS AWS 2.8: IAM password policy prevents password reuse
# Missing datamodel or evidence: IAM account password policy field PasswordReusePrevention
# =============================================================================

# =============================================================================
# TODO: CIS AWS 2.9: MFA is enabled for all IAM users that have a console password
# Missing datamodel or evidence: credential report fields for password_enabled and mfa_active on IAM users
# =============================================================================


# =============================================================================
# CIS AWS 2.15: IAM policies that allow full *:* administrative privileges
# Main node: AWSPolicy
# =============================================================================
class AdminPolicyAttachedOutput(Finding):
    """Output model for the full administrative privileges check."""

    policy_name: str | None = None
    policy_id: str | None = None
    policy_arn: str | None = None
    statement_sid: str | None = None
    principal_arn: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_admin_policy_attached = Fact(
    id="aws_admin_policy_attached",
    name="AWS IAM policy granting full administrative privileges",
    description=(
        "Detects managed or inline IAM policies attached to a user, group, or role "
        "that grant full '*:*' administrative privileges, i.e. an Allow statement "
        "whose action includes '*' (or '*:*') on resource '*'. Such policies violate "
        "least privilege and should be replaced with scoped permissions. Inline "
        "policies have no ARN, so policy.id is used as the stable identifier."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
    WHERE stmt.effect = 'Allow'
      AND any(action IN stmt.action WHERE action = '*' OR action = '*:*')
      AND any(resource IN stmt.resource WHERE resource = '*')
    RETURN DISTINCT
        policy.id AS policy_id,
        policy.arn AS policy_arn,
        policy.name AS policy_name,
        stmt.sid AS statement_sid,
        principal.arn AS principal_arn,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
    WHERE stmt.effect = 'Allow'
      AND any(action IN stmt.action WHERE action = '*' OR action = '*:*')
      AND any(resource IN stmt.resource WHERE resource = '*')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (:AWSPrincipal)-[:POLICY]->(policy:AWSPolicy)
    RETURN COUNT(DISTINCT policy.id) AS count
    """,
    asset_id_field="policy_id",
    identity_fields=("policy_id", "principal_arn"),
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

aws_policies_with_full_administrative_privileges = Rule(
    id="aws_policies_with_full_administrative_privileges",
    name="Full Administrative Privilege Policies",
    description=(
        "IAM policies that allow full '*:*' administrative privileges should not be "
        "attached to users, groups, or roles. Granting full administrative access "
        "violates the principle of least privilege and broadens the blast radius of "
        "a compromised identity."
    ),
    output_model=AdminPolicyAttachedOutput,
    facts=(_aws_admin_policy_attached,),
    tags=("iam", "policies", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("2.15"),
        iso27001_annex_a("8.2"),
        iso27001_annex_a("5.18"),
    ),
)

# =============================================================================
# TODO: CIS AWS 2.16: A support role has been created to manage incidents with AWS Support
# Missing datamodel or evidence: AWSSupportAccess managed policy attachments or equivalent support role relationships
# =============================================================================

# =============================================================================
# TODO: CIS AWS 2.17: IAM instance roles are used for AWS resource access from instances
# Missing datamodel or evidence: EC2 instance profile or IAM role attachment state, plus secret-scanning evidence for embedded AWS credentials
# =============================================================================

# =============================================================================
# TODO: CIS AWS 2.19: IAM External Access Analyzer is enabled for all regions
# Missing datamodel or evidence: IAM Access Analyzer inventory and regional analyzer status
# =============================================================================

# =============================================================================
# TODO: ISO 27001 Annex A 8.5: Secure authentication
# Missing datamodel or evidence: IAM user console password state, MFA state,
# root account MFA state, and password policy details.
# =============================================================================
