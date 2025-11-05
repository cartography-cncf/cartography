from cartography.rules.spec.model import Fact, Module, FindingOutput, Finding

# Facts
_missing_mfa_slack = Fact(
    id="missing-mfa-slack",
    name="Slack users with disabled MFA",
    description="Finds Slack user accounts that have Multi-Factor Authentication disabled.",
    module=Module.SLACK,
    cypher_query="""
    MATCH (u:SlackUser)
    WHERE COALESCE(u.mfa_enabled, false) = false
    RETURN u.id AS id, u.email AS email, u.first_name AS firstname, u.last_name AS lastname, u._module_name AS _source
    """,
    cypher_visual_query="""
    MATCH (u:SlackUser)
    WHERE COALESCE(u.mfa_enabled, false) = false
    RETURN u
    """,
)
_missing_mfa_cloudflare = Fact(
    id="missing-mfa-cloudflare",
    name="Cloudflare members with disabled MFA",
    description="Finds Cloudflare member accounts that have Multi-Factor Authentication disabled.",
    module=Module.CLOUDFLARE,
    cypher_query="""
    MATCH (m:CloudflareMember)
    WHERE m.two_factor_authentication_enabled = false
    RETURN m.id AS id, m.email AS email, m.firstname AS firstname, m.lastname AS lastname, m._module_name AS _source, m.status AS status
    """,
    cypher_visual_query="""
    MATCH (m:CloudflareMember)
    WHERE m.two_factor_authentication_enabled = false
    RETURN m
    """,
)

# Finding
class MFAFindingOutput(FindingOutput):
    id: str | None = None
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None


missing_mfa_finding = Finding(
    id="mfa-missing",
    name="User accounts missing MFA",
    description="Detects user accounts that do not have Multi-Factor Authentication enabled.",
    tags=("identity",),
    facts=(
        _missing_mfa_slack,
        _missing_mfa_cloudflare,
    ),
    output_model=MFAFindingOutput,
)
