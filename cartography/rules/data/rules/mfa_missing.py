from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_missing_mfa_cloudflare = Fact(
    id="missing-mfa-cloudflare",
    name="Cloudflare members with disabled MFA",
    description="Finds Cloudflare member accounts that have Multi-Factor Authentication disabled.",
    module=Module.CLOUDFLARE,
    cypher_query="""
    MATCH (m:CloudflareMember)
    WHERE m.two_factor_authentication_enabled = false
    RETURN m.id AS id, m.email AS email, m.firstname AS firstname, m.lastname AS lastname, m.status AS status
    """,
    cypher_visual_query="""
    MATCH (m:CloudflareMember)
    WHERE m.two_factor_authentication_enabled = false
    RETURN m
    """,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class MFARuleOutput(Finding):
    email: str | None = None
    id: str | None = None
    firstname: str | None = None
    lastname: str | None = None


missing_mfa_rule = Rule(
    id="mfa-missing",
    name="User accounts missing MFA",
    description="Detects user accounts that do not have Multi-Factor Authentication enabled.",
    output_model=MFARuleOutput,
    tags=("identity",),
    facts=(
        # TODO: _missing_mfa_slack,
        _missing_mfa_cloudflare,
    ),
    version="0.1.0",
)
