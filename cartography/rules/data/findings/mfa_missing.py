from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

# Facts
_missing_mfa_cloudflare = Fact(
    id="missing-mfa-cloudflare",
    name="Cloudflare members with disabled MFA",
    description="Finds Cloudflare member accounts that have Multi-Factor Authentication disabled.",
    module=Module.CLOUDFLARE,
    cypher_query="""
    MATCH (m:CloudflareMember)
    WHERE m.two_factor_authentication_enabled = false
    RETURN m
    """,
    maturity=Maturity.EXPERIMENTAL,
)


# Finding
missing_mfa_finding = Finding(
    id="mfa-missing",
    name="User accounts missing MFA",
    description="Detects user accounts that do not have Multi-Factor Authentication enabled.",
    tags=("identity",),
    facts=(
        # TODO: _missing_mfa_slack,
        _missing_mfa_cloudflare,
    ),
    version="0.1.0",
)
