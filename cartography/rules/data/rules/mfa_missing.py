from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_missing_mfa_aws = Fact(
    id="missing-mfa-aws",
    name="AWS IAM users without an MFA device",
    description=(
        "AWS IAM users that are not associated with any MFA device. The "
        "check looks for the absence of a `:MFA_DEVICE` relationship from "
        "an AWSMfaDevice. Console access (passwordlastused IS NOT NULL) is "
        "surfaced via the `firstname` field so callers can prioritise "
        "users who have actually signed in via the console."
    ),
    module=Module.AWS,
    cypher_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(user:AWSUser)
    WHERE NOT (user)<-[:MFA_DEVICE]-(:AWSMfaDevice)
    RETURN
        user.arn AS id,
        user.name AS email,
        CASE WHEN user.passwordlastused IS NOT NULL
             THEN 'console-active'
             ELSE 'programmatic-only' END AS firstname,
        account.name AS lastname,
        'no-mfa' AS status
    ORDER BY id
    """,
    cypher_visual_query="""
    MATCH p=(account:AWSAccount)-[:RESOURCE]->(user:AWSUser)
    WHERE NOT (user)<-[:MFA_DEVICE]-(:AWSMfaDevice)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (user:AWSUser)
    RETURN COUNT(user) AS count
    """,
    asset_id_field="id",
    maturity=Maturity.EXPERIMENTAL,
)


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
    cypher_count_query="""
    MATCH (m:CloudflareMember)
    RETURN COUNT(m) AS count
    """,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class MFARuleOutput(Finding):
    email: str | None = None
    id: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    status: str | None = None


missing_mfa_rule = Rule(
    id="mfa-missing",
    name="User accounts missing MFA",
    description="Detects user accounts that do not have Multi-Factor Authentication enabled.",
    output_model=MFARuleOutput,
    tags=("identity",),
    facts=(
        # TODO: _missing_mfa_slack,
        _missing_mfa_aws,
        _missing_mfa_cloudflare,
    ),
    version="0.1.0",
)
