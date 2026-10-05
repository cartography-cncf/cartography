"""
DISA Okta IDaaS STIG Checks

Implements checks from the DISA Okta Identity as a Service (IDaaS) Security
Technical Implementation Guide, Version 1 Release 2.

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.

STIG coverage (V1R2, 29 checks):

| V-ID     | Status      | Reason when not covered                                              |
| -------- | ----------- | -------------------------------------------------------------------- |
| V-273186 | Not covered | Missing datamodel: global session policy rules (idle timeout)        |
| V-273187 | Not covered | Missing datamodel: Admin Console app session settings                |
| V-273188 | Covered     |                                                                      |
| V-273189 | Not covered | Missing datamodel: password policy lockout settings                  |
| V-273190 | Not covered | Missing datamodel: authentication policy rules (phishing resistance) |
| V-273191 | Not covered | Missing datamodel: authentication policy rules (phishing resistance) |
| V-273192 | Not covered | DoD-only: DoD Notice and Consent Banner, not exposed by the Okta API |
| V-273193 | Not covered | Missing datamodel: authentication policy rules (factor requirements) |
| V-273194 | Not covered | Missing datamodel: authentication policy rules (factor requirements) |
| V-273195 | Not covered | Missing datamodel: password policy complexity settings               |
| V-273196 | Not covered | Missing datamodel: password policy complexity settings               |
| V-273197 | Not covered | Missing datamodel: password policy complexity settings               |
| V-273198 | Not covered | Missing datamodel: password policy complexity settings               |
| V-273199 | Not covered | Missing datamodel: password policy complexity settings               |
| V-273200 | Not covered | Missing datamodel: password policy age settings                      |
| V-273201 | Not covered | Missing datamodel: password policy age settings                      |
| V-273202 | Not covered | Missing datamodel: log streams                                       |
| V-273203 | Not covered | Missing datamodel: global session policy rules (session lifetime)    |
| V-273204 | Not covered | DoD-only: PIV/CAC smart card authenticator                           |
| V-273205 | Covered     |                                                                      |
| V-273206 | Not covered | Missing datamodel: global session policy rules (persistent cookies)  |
| V-273207 | Not covered | DoD-only: DoD-approved certificate authorities for smart card IdPs   |
| V-273208 | Not covered | Missing datamodel: password policy common-password check             |
| V-273209 | Not covered | Missing datamodel: password policy history settings                  |
| V-279689 | Not covered | Missing datamodel: API tokens and network zones                      |
| V-279690 | Not covered | Missing datamodel: API tokens                                        |
| V-279691 | Not covered | Missing datamodel: global session policy network conditions          |
| V-279692 | Not covered | Missing datamodel: network zones                                     |
| V-279693 | Not covered | Missing datamodel: authentication policy network conditions          |
"""

from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.data.frameworks.stig import stig_okta
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

STIG_REFERENCES = [
    RuleReference(
        text="DISA Okta Identity as a Service (IDaaS) STIG V1R2",
        url="https://public.cyber.mil/stigs/downloads/",
    ),
]

# Okta lifecycle states in which the account can still be used to sign in, or be
# recovered into a signed-in state without an administrator re-enabling it.
# SUSPENDED and DEPROVISIONED are the "disabled" states the STIG asks for;
# STAGED and PROVISIONED accounts have never been activated.
_OKTA_ENABLED_USER_STATUSES = "['ACTIVE', 'PASSWORD_EXPIRED', 'LOCKED_OUT', 'RECOVERY']"


# =============================================================================
# DISA Okta STIG V-273188: Accounts inactive for more than 35 days are not disabled
# Main node: OktaUser
# =============================================================================
class OktaInactiveUserNotDisabledOutput(Finding):
    """Output model for enabled Okta users with no sign-in for over 35 days."""

    user_id: str | None = None
    login: str | None = None
    email: str | None = None
    status: str | None = None
    last_login: str | None = None
    created: str | None = None
    days_inactive: int | None = None
    org_id: str | None = None


_okta_user_inactive_35_days = Fact(
    id="okta_user_inactive_35_days",
    name="Enabled Okta users inactive for more than 35 days",
    description=(
        "Detects Okta users in an enabled lifecycle state whose last sign-in is more than "
        "35 days ago, or who have never signed in and were created more than 35 days ago. "
        "Okta should suspend these accounts automatically (for example with an Okta "
        "Workflows automation). Not applicable when users are sourced from an external "
        "directory that enforces inactivity itself."
    ),
    cypher_query=f"""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(u:OktaUser)
    WHERE u.status IN {_OKTA_ENABLED_USER_STATUSES}
      AND datetime(coalesce(u.last_login, u.created)) < datetime() - duration('P35D')
    RETURN
        u.id AS user_id,
        u.login AS login,
        u.email AS email,
        u.status AS status,
        toString(u.last_login) AS last_login,
        toString(u.created) AS created,
        duration.inDays(datetime(coalesce(u.last_login, u.created)), datetime()).days AS days_inactive,
        o.id AS org_id
    ORDER BY days_inactive DESC
    """,
    cypher_visual_query=f"""
    MATCH p=(o:OktaOrganization)-[:RESOURCE]->(u:OktaUser)
    WHERE u.status IN {_OKTA_ENABLED_USER_STATUSES}
      AND datetime(coalesce(u.last_login, u.created)) < datetime() - duration('P35D')
    RETURN *
    """,
    cypher_count_query=f"""
    MATCH (u:OktaUser)
    WHERE u.status IN {_OKTA_ENABLED_USER_STATUSES}
    RETURN COUNT(u) AS count
    """,
    asset_id_field="user_id",
    asset_label="OktaUser",
    identity_fields=("user_id",),
    module=Module.OKTA,
    maturity=Maturity.EXPERIMENTAL,
)

okta_inactive_users_not_disabled = Rule(
    id="okta_inactive_users_not_disabled",
    name="Inactive Users Not Disabled",
    description=(
        "Okta accounts with no sign-in for more than 35 days should be suspended. "
        "Dormant accounts are attractive to attackers because their owners will not "
        "notice unauthorized use."
    ),
    output_model=OktaInactiveUserNotDisabledOutput,
    facts=(_okta_user_inactive_35_days,),
    tags=("iam", "identity", "stale_account", "stride:spoofing"),
    version="1.0.0",
    references=STIG_REFERENCES
    + [
        RuleReference(
            text="Okta Help: Automations",
            url="https://help.okta.com/okta_help.htm?type=oie&id=ext-automations-main",
        ),
    ],
    frameworks=(
        stig_okta("V-273188"),
        iso27001_annex_a("5.18"),
        soc2_tsc("CC6.2"),
    ),
)


# =============================================================================
# DISA Okta STIG V-273205: Okta Verify does not require FIPS-compliant devices
# Main node: OktaAuthenticator
# =============================================================================
class OktaVerifyFipsNotRequiredOutput(Finding):
    """Output model for Okta Verify authenticators that do not require FIPS devices."""

    authenticator_id: str | None = None
    authenticator_name: str | None = None
    status: str | None = None
    compliance_settings: str | None = None
    org_id: str | None = None


_okta_verify_fips_not_required = Fact(
    id="okta_verify_fips_not_required",
    name="Okta Verify authenticators without required FIPS compliance",
    description=(
        "Detects active Okta Verify authenticators whose FIPS compliance setting is not "
        "REQUIRED, which lets users enroll Okta Verify on devices without a FIPS 140-2 "
        "validated cryptographic module."
    ),
    cypher_query="""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(a:OktaAuthenticator)
    WHERE a.key = 'okta_verify'
      AND a.status = 'ACTIVE'
      AND NOT coalesce(a.settings_compliance, '') =~ '.*"fips"\\\\s*:\\\\s*"REQUIRED".*'
    RETURN
        a.id AS authenticator_id,
        a.name AS authenticator_name,
        a.status AS status,
        a.settings_compliance AS compliance_settings,
        o.id AS org_id
    """,
    cypher_visual_query="""
    MATCH p=(o:OktaOrganization)-[:RESOURCE]->(a:OktaAuthenticator)
    WHERE a.key = 'okta_verify'
      AND a.status = 'ACTIVE'
      AND NOT coalesce(a.settings_compliance, '') =~ '.*"fips"\\\\s*:\\\\s*"REQUIRED".*'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (a:OktaAuthenticator)
    WHERE a.key = 'okta_verify' AND a.status = 'ACTIVE'
    RETURN COUNT(a) AS count
    """,
    asset_id_field="authenticator_id",
    asset_label="OktaAuthenticator",
    identity_fields=("authenticator_id",),
    module=Module.OKTA,
    maturity=Maturity.EXPERIMENTAL,
)

okta_verify_fips_compliance_not_required = Rule(
    id="okta_verify_fips_compliance_not_required",
    name="Okta Verify Allows Non-FIPS Devices",
    description=(
        "Okta Verify should only enroll devices with FIPS-validated cryptography so "
        "that authenticator keys are protected by an approved module."
    ),
    output_model=OktaVerifyFipsNotRequiredOutput,
    facts=(_okta_verify_fips_not_required,),
    tags=("iam", "authentication", "cryptography", "stride:spoofing"),
    version="1.0.0",
    references=STIG_REFERENCES
    + [
        RuleReference(
            text="Okta Help: Configure Okta Verify options",
            url="https://help.okta.com/okta_help.htm?type=oie&id=ext-config-okta-verify-options",
        ),
    ],
    frameworks=(
        stig_okta("V-273205"),
        iso27001_annex_a("8.5"),
        iso27001_annex_a("8.24"),
        soc2_tsc("CC6.1"),
    ),
)
