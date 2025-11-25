from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# Facts
_missing_mfa_ontology = Fact(
    id="missing-mfa-ontology",
    name="User Accounts Without Multi-Factor Authentication",
    description=(
        "Finds user accounts where Multi-Factor Authentication is not configured for the account."
    ),
    module=Module.CROSS_CLOUD,
    cypher_query="""
    MATCH (a:UserAccount)
    WHERE COALESCE(a.has_mfa, True) = False
    RETURN a._ont_email AS email, a._ont_firstname AS firstname, a._ont_lastname AS lastname, a._has_mfa AS has_mfa, a._ont_source AS source
    """,
    cypher_visual_query="""
    MATCH (a:UserAccount)
    WHERE COALESCE(a.has_mfa, True) = False
    RETURN a
    """,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class MFARuleOutput(Finding):
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    has_mfa: bool | None = None
    source: str | None = None


missing_mfa_rule = Rule(
    id="mfa-missing",
    name="User Accounts Without Multi-Factor Authentication",
    description=(
        "Detects user accounts across cloud platforms, SaaS services, and identity providers that do not have "
        "Multi-Factor Authentication (MFA) enabled. Accounts without MFA rely solely on password-based authentication, "
        "making them highly vulnerable to credential theft, phishing attacks, password reuse, brute-force attacks, "
        "and credential stuffing. Compromised credentials are one of the leading causes of security breaches, and "
        "MFA provides a critical second layer of defense even when passwords are compromised. This is especially "
        "critical for accounts with privileged or administrative access, access to sensitive data, or external/remote "
        "access capabilities. Organizations should enforce mandatory MFA through identity provider policies, implement "
        "phishing-resistant MFA methods (WebAuthn, FIDO2, hardware security keys) for privileged accounts, and regularly "
        "audit compliance with MFA requirements."
    ),
    output_model=MFARuleOutput,
    tags=("identity", "authentication", "mfa"),
    facts=(_missing_mfa_ontology,),
    version="0.1.0",
)
