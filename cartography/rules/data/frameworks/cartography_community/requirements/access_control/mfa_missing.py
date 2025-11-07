from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import FindingOutput
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
        # TODO: _missing_mfa_slack,
        _missing_mfa_cloudflare,
    ),
    output_model=MFAFindingOutput,
)
