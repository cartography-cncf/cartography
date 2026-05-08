from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class IdentityMfaGapOutput(Finding):
    provider: str | None = None
    account_id: str | None = None
    account_name: str | None = None
    principal_id: str | None = None
    principal_name: str | None = None
    principal_type: str | None = None
    issue: str | None = None
    current_value: str | None = None


_cloudflare_account_2fa_not_enforced = Fact(
    id="cloudflare_account_2fa_not_enforced",
    name="Cloudflare accounts do not enforce two-factor authentication",
    description=(
        "Detects Cloudflare accounts where the account-level two-factor "
        "authentication enforcement setting is disabled."
    ),
    cypher_query="""
    MATCH (account:CloudflareAccount)
    WHERE account.enforce_twofactor = false
    RETURN
        'cloudflare' AS provider,
        account.id AS account_id,
        account.name AS account_name,
        account.id AS principal_id,
        account.name AS principal_name,
        'account' AS principal_type,
        'two_factor_not_enforced' AS issue,
        toString(account.enforce_twofactor) AS current_value
    """,
    cypher_visual_query="""
    MATCH (account:CloudflareAccount)
    WHERE account.enforce_twofactor = false
    RETURN account
    """,
    cypher_count_query="""
    MATCH (account:CloudflareAccount)
    RETURN COUNT(account) AS count
    """,
    asset_id_field="account_id",
    module=Module.CLOUDFLARE,
    maturity=Maturity.EXPERIMENTAL,
)


_lastpass_user_mfa_missing = Fact(
    id="lastpass_user_mfa_missing",
    name="Active LastPass users without multifactor authentication",
    description=(
        "Detects active LastPass users whose multifactor field is explicitly "
        "false. NULL values are treated as unknown and are not flagged."
    ),
    cypher_query="""
    MATCH (tenant:LastpassTenant)-[:RESOURCE]->(user:LastpassUser)
    WHERE coalesce(user.disabled, false) = false
      AND (
        user.multifactor = false
        OR toLower(toString(user.multifactor)) IN ['false', '0']
      )
    RETURN
        'lastpass' AS provider,
        tenant.id AS account_id,
        tenant.id AS account_name,
        user.id AS principal_id,
        coalesce(user.email, user.name, user.id) AS principal_name,
        CASE WHEN coalesce(user.admin, false) = true THEN 'admin' ELSE 'user' END AS principal_type,
        'mfa_not_configured' AS issue,
        toString(user.multifactor) AS current_value
    """,
    cypher_visual_query="""
    MATCH p=(tenant:LastpassTenant)-[:RESOURCE]->(user:LastpassUser)
    WHERE coalesce(user.disabled, false) = false
      AND (
        user.multifactor = false
        OR toLower(toString(user.multifactor)) IN ['false', '0']
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (user:LastpassUser)
    WHERE coalesce(user.disabled, false) = false
    RETURN COUNT(user) AS count
    """,
    asset_id_field="principal_id",
    module=Module.LASTPASS,
    maturity=Maturity.EXPERIMENTAL,
)


_jumpcloud_user_mfa_missing = Fact(
    id="jumpcloud_user_mfa_missing",
    name="Active JumpCloud users without multifactor authentication",
    description=(
        "Detects active JumpCloud users whose mfa_configured field is explicitly "
        "false."
    ),
    cypher_query="""
    MATCH (tenant:JumpCloudTenant)-[:RESOURCE]->(user:JumpCloudUser)
    WHERE coalesce(user.activated, true) = true
      AND coalesce(user.suspended, false) = false
      AND (
        user.mfa_configured = false
        OR toLower(toString(user.mfa_configured)) IN ['false', '0']
      )
    RETURN
        'jumpcloud' AS provider,
        tenant.id AS account_id,
        tenant.id AS account_name,
        user.id AS principal_id,
        coalesce(user.email, user.username, user.displayname, user.id) AS principal_name,
        'user' AS principal_type,
        'mfa_not_configured' AS issue,
        toString(user.mfa_configured) AS current_value
    """,
    cypher_visual_query="""
    MATCH p=(tenant:JumpCloudTenant)-[:RESOURCE]->(user:JumpCloudUser)
    WHERE coalesce(user.activated, true) = true
      AND coalesce(user.suspended, false) = false
      AND (
        user.mfa_configured = false
        OR toLower(toString(user.mfa_configured)) IN ['false', '0']
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (user:JumpCloudUser)
    WHERE coalesce(user.activated, true) = true
      AND coalesce(user.suspended, false) = false
    RETURN COUNT(user) AS count
    """,
    asset_id_field="principal_id",
    module=Module.JUMPCLOUD,
    maturity=Maturity.EXPERIMENTAL,
)


_duo_user_not_enrolled = Fact(
    id="duo_user_not_enrolled",
    name="Active Duo users not enrolled in MFA",
    description=(
        "Detects active Duo users whose is_enrolled field is explicitly false."
    ),
    cypher_query="""
    MATCH (api_host:DuoApiHost)-[:RESOURCE]->(user:DuoUser)
    WHERE coalesce(user.status, 'active') <> 'disabled'
      AND (
        user.is_enrolled = false
        OR toLower(toString(user.is_enrolled)) IN ['false', '0']
      )
    RETURN
        'duo' AS provider,
        api_host.id AS account_id,
        api_host.id AS account_name,
        user.id AS principal_id,
        coalesce(user.email, user.username, user.realname, user.id) AS principal_name,
        'user' AS principal_type,
        'mfa_not_enrolled' AS issue,
        toString(user.is_enrolled) AS current_value
    """,
    cypher_visual_query="""
    MATCH p=(api_host:DuoApiHost)-[:RESOURCE]->(user:DuoUser)
    WHERE coalesce(user.status, 'active') <> 'disabled'
      AND (
        user.is_enrolled = false
        OR toLower(toString(user.is_enrolled)) IN ['false', '0']
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (user:DuoUser)
    WHERE coalesce(user.status, 'active') <> 'disabled'
    RETURN COUNT(user) AS count
    """,
    asset_id_field="principal_id",
    module=Module.DUO,
    maturity=Maturity.EXPERIMENTAL,
)


identity_mfa_gaps = Rule(
    id="identity_mfa_gaps",
    name="Identity MFA Gaps",
    description=(
        "Detects provider-specific MFA enforcement and enrollment gaps for "
        "Cloudflare, LastPass, JumpCloud, and Duo."
    ),
    output_model=IdentityMfaGapOutput,
    facts=(
        _cloudflare_account_2fa_not_enforced,
        _lastpass_user_mfa_missing,
        _jumpcloud_user_mfa_missing,
        _duo_user_not_enrolled,
    ),
    tags=("identity", "mfa", "compliance", "stride:spoofing"),
    version="0.1.0",
    frameworks=(iso27001_annex_a("8.5"),),
)
