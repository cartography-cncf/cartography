from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_missing_mfa_ontology = Fact(
    id="missing-mfa-ontology",
    name="UserAccount nodes with MFA explicitly disabled",
    description=(
        "Active user accounts whose `_ont_has_mfa` ontology field is "
        "explicitly false. Built on the cross-cloud `UserAccount` "
        "semantic label so it covers every provider that maps the "
        "`has_mfa` ontology field, currently: Cloudflare, Slack, "
        "GitHub, GSuite / Google Workspace, JumpCloud, Keycloak, "
        "LastPass, OCI, Scaleway, Sentry. Providers that do not "
        "expose an MFA flag are intentionally skipped (NULL means "
        "unknown, not missing). AWS uses a separate fact since it "
        "models MFA via the `:MFA_DEVICE` edge instead of an ontology "
        "boolean."
    ),
    module=Module.CROSS_CLOUD,
    cypher_query="""
    MATCH (a:UserAccount)
    WHERE a._ont_has_mfa = false
      AND COALESCE(a._ont_active, true)
      AND NOT COALESCE(a._ont_inactive, false)
    RETURN
        a.id AS id,
        a._ont_email AS email,
        a._ont_firstname AS firstname,
        a._ont_lastname AS lastname,
        a._ont_source AS status
    ORDER BY id
    """,
    cypher_visual_query="""
    MATCH (a:UserAccount)
    WHERE a._ont_has_mfa = false
      AND COALESCE(a._ont_active, true)
      AND NOT COALESCE(a._ont_inactive, false)
    RETURN a
    """,
    cypher_count_query="""
    MATCH (a:UserAccount)
    WHERE a._ont_has_mfa IS NOT NULL
      AND COALESCE(a._ont_active, true)
      AND NOT COALESCE(a._ont_inactive, false)
    RETURN COUNT(a) AS count
    """,
    asset_id_field="id",
    maturity=Maturity.EXPERIMENTAL,
)


_missing_mfa_aws = Fact(
    id="missing-mfa-aws",
    name="AWS IAM users without an MFA device",
    description=(
        "AWS IAM users that are not associated with any MFA device. The "
        "check looks for the absence of a `:MFA_DEVICE` relationship from "
        "an AWSMfaDevice. Console access (passwordlastused_dt IS NOT NULL) "
        "is surfaced via the `firstname` field so callers can prioritise "
        "users who have actually signed in via the console. The string "
        "`passwordlastused` is left empty rather than NULL by the AWS "
        "intel transform, so the typed `_dt` field is the reliable signal. "
        "AWS is handled outside the cross-cloud ontology fact because the "
        "AWSUser ontology mapping does not carry an MFA boolean."
    ),
    module=Module.AWS,
    cypher_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(user:AWSUser)
    WHERE NOT (user)-[:MFA_DEVICE]->(:AWSMfaDevice)
    RETURN
        user.arn AS id,
        user.name AS email,
        CASE WHEN user.passwordlastused_dt IS NOT NULL
             THEN 'console-active'
             ELSE 'programmatic-only' END AS firstname,
        account.name AS lastname,
        'no-mfa' AS status
    ORDER BY id
    """,
    cypher_visual_query="""
    MATCH p=(account:AWSAccount)-[:RESOURCE]->(user:AWSUser)
    WHERE NOT (user)-[:MFA_DEVICE]->(:AWSMfaDevice)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (user:AWSUser)
    RETURN COUNT(user) AS count
    """,
    asset_id_field="id",
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
    description=(
        "Detects user accounts that do not have Multi-Factor Authentication "
        "enabled. The cross-cloud ontology fact covers any provider that "
        "exposes the `has_mfa` UserAccount ontology field; AWS is handled "
        "separately via the `:MFA_DEVICE` edge."
    ),
    output_model=MFARuleOutput,
    tags=("identity",),
    facts=(
        _missing_mfa_aws,
        _missing_mfa_ontology,
    ),
    version="0.2.0",
)
