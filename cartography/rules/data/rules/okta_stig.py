"""
DISA Okta IDaaS STIG Checks

Implements checks from the DISA Okta Identity as a Service (IDaaS) Security
Technical Implementation Guide, Version 1 Release 2.

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.

STIG coverage (V1R2, 29 checks):

| V-ID     | Status      | Reason when not covered                                              |
| -------- | ----------- | -------------------------------------------------------------------- |
| V-273186 | Covered     |                                                                      |
| V-273187 | Covered     |                                                                      |
| V-273188 | Covered     |                                                                      |
| V-273189 | Covered     |                                                                      |
| V-273190 | Covered     |                                                                      |
| V-273191 | Covered     |                                                                      |
| V-273192 | Not covered | DoD-only: DoD Notice and Consent Banner, not exposed by the Okta API |
| V-273193 | Covered     |                                                                      |
| V-273194 | Covered     |                                                                      |
| V-273195 | Covered     |                                                                      |
| V-273196 | Covered     |                                                                      |
| V-273197 | Covered     |                                                                      |
| V-273198 | Covered     |                                                                      |
| V-273199 | Covered     |                                                                      |
| V-273200 | Covered     |                                                                      |
| V-273201 | Covered     |                                                                      |
| V-273202 | Covered     |                                                                      |
| V-273203 | Covered     |                                                                      |
| V-273204 | Not covered | DoD-only: PIV/CAC smart card authenticator                           |
| V-273205 | Covered     |                                                                      |
| V-273206 | Covered     |                                                                      |
| V-273207 | Not covered | DoD-only: DoD-approved certificate authorities for smart card IdPs   |
| V-273208 | Covered     |                                                                      |
| V-273209 | Covered     |                                                                      |
| V-279689 | Covered     |                                                                      |
| V-279690 | Covered     |                                                                      |
| V-279691 | Covered     |                                                                      |
| V-279692 | Covered     |                                                                      |
| V-279693 | Covered     |                                                                      |

Fidelity notes (every Fact is EXPERIMENTAL until validated on synced orgs):

- Global session checks (V-273186, V-273203, V-273206) evaluate the highest-priority
  active rule of every active global session policy. The STIG only inspects the
  default policy and also asks for that rule not to be the "Default Rule"; the
  settings, not the rule name, are what limit the session.
- Admin Console and Dashboard checks (V-273190, V-273191, V-273193, V-273194)
  evaluate the highest-priority active rule that allows access in the
  authentication policy assigned to the app, as the STIG's "top rule" does.
- Password checks (V-273189, V-273195 to V-273201, V-273208, V-273209) cover active
  password policies for Okta-sourced users. Policies for Active Directory or LDAP
  users are skipped: the STIG marks them not applicable. Okta's lockout counts
  consecutive failures and has no configurable 15-minute window.
- V-273202 cannot see a SIEM that pulls the System Log through the API, which the
  STIG also accepts.
- V-279690 flags tokens owned by a super administrator. Whether an account was
  created solely for its token is organizational and is not checked.
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


# =============================================================================
# Global session policy checks (V-273186, V-273203, V-273206)
# Main node: OktaPolicy (type OKTA_SIGN_ON)
# =============================================================================
class OktaGlobalSessionRuleOutput(Finding):
    """Output model for global session policies whose top rule is too permissive."""

    policy_id: str | None = None
    policy_name: str | None = None
    rule_id: str | None = None
    rule_name: str | None = None
    session_max_idle_minutes: int | None = None
    session_max_lifetime_minutes: int | None = None
    session_use_persistent_cookie: bool | None = None
    org_id: str | None = None


# Binds each active global session policy to its highest-priority active rule.
_GLOBAL_SESSION_TOP_RULE = """
    MATCH (o:OktaOrganization)-[:RESOURCE]->(p:OktaPolicy)
    WHERE p.type = 'OKTA_SIGN_ON' AND p.status = 'ACTIVE'
    MATCH (p)-[:HAS_RULE]->(r:OktaPolicyRule)
    WHERE r.status = 'ACTIVE'
    WITH o, p, r
    ORDER BY r.priority
    WITH o, p, collect(r)[0] AS top_rule
"""

_GLOBAL_SESSION_COUNT = """
    MATCH (p:OktaPolicy)
    WHERE p.type = 'OKTA_SIGN_ON' AND p.status = 'ACTIVE'
    RETURN COUNT(p) AS count
"""


def _global_session_fact(fact_id: str, name: str, description: str, violation: str):
    return Fact(
        id=fact_id,
        name=name,
        description=description,
        cypher_query=f"""
        {_GLOBAL_SESSION_TOP_RULE}
        WHERE {violation}
        RETURN
            p.id AS policy_id,
            p.name AS policy_name,
            top_rule.id AS rule_id,
            top_rule.name AS rule_name,
            top_rule.session_max_idle_minutes AS session_max_idle_minutes,
            top_rule.session_max_lifetime_minutes AS session_max_lifetime_minutes,
            top_rule.session_use_persistent_cookie AS session_use_persistent_cookie,
            o.id AS org_id
        """,
        cypher_visual_query=f"""
        {_GLOBAL_SESSION_TOP_RULE}
        WHERE {violation}
        MATCH path=(o)-[:RESOURCE]->(p)-[:HAS_RULE]->(top_rule)
        RETURN path
        """,
        cypher_count_query=_GLOBAL_SESSION_COUNT,
        asset_id_field="policy_id",
        asset_label="OktaPolicy",
        identity_fields=("policy_id",),
        module=Module.OKTA,
        maturity=Maturity.EXPERIMENTAL,
    )


_GLOBAL_SESSION_REFERENCES = STIG_REFERENCES + [
    RuleReference(
        text="Okta Help: Global session policies",
        url="https://help.okta.com/okta_help.htm?type=oie&id=ext-about-okta-sign-on-policies",
    ),
]

okta_global_session_idle_timeout_too_long = Rule(
    id="okta_global_session_idle_timeout_too_long",
    name="Global Session Idle Timeout Too Long",
    description=(
        "Okta global sessions should end after at most 15 minutes of inactivity so an "
        "unattended browser cannot be reused to reach every connected app."
    ),
    output_model=OktaGlobalSessionRuleOutput,
    facts=(
        _global_session_fact(
            "okta_global_session_idle_timeout_over_15_minutes",
            "Okta global session policies allowing more than 15 idle minutes",
            "Detects active global session policies whose highest-priority active rule "
            "keeps sessions alive for more than 15 idle minutes.",
            "coalesce(top_rule.session_max_idle_minutes, 120) > 15",
        ),
    ),
    tags=("iam", "authentication", "session_management", "stride:spoofing"),
    version="1.0.0",
    references=_GLOBAL_SESSION_REFERENCES,
    frameworks=(
        stig_okta("V-273186"),
        iso27001_annex_a("8.5"),
        soc2_tsc("CC6.1"),
    ),
)

okta_global_session_lifetime_too_long = Rule(
    id="okta_global_session_lifetime_too_long",
    name="Global Session Lifetime Too Long",
    description=(
        "Okta global sessions should last at most 18 hours so users re-authenticate "
        "at least daily. A lifetime of 0 means sessions never expire."
    ),
    output_model=OktaGlobalSessionRuleOutput,
    facts=(
        _global_session_fact(
            "okta_global_session_lifetime_over_18_hours",
            "Okta global session policies allowing sessions longer than 18 hours",
            "Detects active global session policies whose highest-priority active rule "
            "allows sessions longer than 18 hours (1080 minutes) or without a limit.",
            "(coalesce(top_rule.session_max_lifetime_minutes, 0) = 0 "
            "OR top_rule.session_max_lifetime_minutes > 1080)",
        ),
    ),
    tags=("iam", "authentication", "session_management", "stride:spoofing"),
    version="1.0.0",
    references=_GLOBAL_SESSION_REFERENCES,
    frameworks=(
        stig_okta("V-273203"),
        iso27001_annex_a("8.5"),
        soc2_tsc("CC6.1"),
    ),
)

okta_global_session_persistent_cookies = Rule(
    id="okta_global_session_persistent_cookies",
    name="Persistent Global Session Cookies",
    description=(
        "Okta global session cookies should not persist across browser restarts, so "
        "closing the browser ends the session."
    ),
    output_model=OktaGlobalSessionRuleOutput,
    facts=(
        _global_session_fact(
            "okta_global_session_persistent_cookie_enabled",
            "Okta global session policies with persistent session cookies",
            "Detects active global session policies whose highest-priority active rule "
            "keeps session cookies across browser sessions.",
            "coalesce(top_rule.session_use_persistent_cookie, false) = true",
        ),
    ),
    tags=("iam", "authentication", "session_management", "stride:spoofing"),
    version="1.0.0",
    references=_GLOBAL_SESSION_REFERENCES,
    frameworks=(
        stig_okta("V-273206"),
        iso27001_annex_a("8.5"),
        soc2_tsc("CC6.1"),
    ),
)


# =============================================================================
# V-279691: Global session policy without an IP-based network condition
# Main node: OktaPolicy (type OKTA_SIGN_ON)
# =============================================================================
class OktaGlobalSessionNetworkOutput(Finding):
    """Output model for global session policies without network zone conditions."""

    policy_id: str | None = None
    policy_name: str | None = None
    org_id: str | None = None


_GLOBAL_SESSION_WITHOUT_ZONE = """
    MATCH (o:OktaOrganization)-[:RESOURCE]->(p:OktaPolicy)
    WHERE p.type = 'OKTA_SIGN_ON' AND p.status = 'ACTIVE'
      AND NOT EXISTS {
          MATCH (p)-[:HAS_RULE]->(r:OktaPolicyRule)
          WHERE r.status = 'ACTIVE' AND r.network_connection = 'ZONE'
      }
"""

okta_global_session_without_network_zones = Rule(
    id="okta_global_session_without_network_zones",
    name="Global Session Policy Without IP Restrictions",
    description=(
        "Okta global session policies should allow or deny sign-in by network zone, "
        "so sessions can only be established from the networks the access control "
        "policy permits."
    ),
    output_model=OktaGlobalSessionNetworkOutput,
    facts=(
        Fact(
            id="okta_global_session_policy_without_zone_condition",
            name="Okta global session policies without network zone conditions",
            description=(
                "Detects active global session policies in which no active rule has a "
                "network zone condition."
            ),
            cypher_query=f"""
            {_GLOBAL_SESSION_WITHOUT_ZONE}
            RETURN p.id AS policy_id, p.name AS policy_name, o.id AS org_id
            """,
            cypher_visual_query=f"""
            {_GLOBAL_SESSION_WITHOUT_ZONE}
            OPTIONAL MATCH path=(o)-[:RESOURCE]->(p)-[:HAS_RULE]->(:OktaPolicyRule)
            RETURN p, path
            """,
            cypher_count_query=_GLOBAL_SESSION_COUNT,
            asset_id_field="policy_id",
            asset_label="OktaPolicy",
            identity_fields=("policy_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=("iam", "network", "access_control", "stride:spoofing"),
    version="1.0.0",
    references=_GLOBAL_SESSION_REFERENCES,
    frameworks=(
        stig_okta("V-279691"),
        iso27001_annex_a("5.15"),
        soc2_tsc("CC6.6"),
    ),
)


# =============================================================================
# V-273187: Okta Admin Console idle timeout longer than 15 minutes
# Main node: OktaOrganization
# =============================================================================
class OktaAdminConsoleSessionOutput(Finding):
    """Output model for orgs whose Admin Console sessions idle too long."""

    org_id: str | None = None
    admin_console_session_idle_timeout_minutes: int | None = None
    admin_console_session_max_lifetime_minutes: int | None = None


okta_admin_console_idle_timeout_too_long = Rule(
    id="okta_admin_console_idle_timeout_too_long",
    name="Admin Console Idle Timeout Too Long",
    description=(
        "Okta Admin Console sessions should end after at most 15 minutes of "
        "inactivity to limit the use of an unattended administrator session."
    ),
    output_model=OktaAdminConsoleSessionOutput,
    facts=(
        Fact(
            id="okta_admin_console_idle_timeout_over_15_minutes",
            name="Okta Admin Console sessions idle longer than 15 minutes",
            description=(
                "Detects Okta orgs whose Admin Console session idle timeout is longer "
                "than 15 minutes. Orgs whose setting could not be read are not "
                "evaluated."
            ),
            cypher_query="""
            MATCH (o:OktaOrganization)
            WHERE o.admin_console_session_idle_timeout_minutes > 15
            RETURN
                o.id AS org_id,
                o.admin_console_session_idle_timeout_minutes AS admin_console_session_idle_timeout_minutes,
                o.admin_console_session_max_lifetime_minutes AS admin_console_session_max_lifetime_minutes
            """,
            cypher_visual_query="""
            MATCH (o:OktaOrganization)
            WHERE o.admin_console_session_idle_timeout_minutes > 15
            RETURN o
            """,
            cypher_count_query="""
            MATCH (o:OktaOrganization)
            WHERE o.admin_console_session_idle_timeout_minutes IS NOT NULL
            RETURN COUNT(o) AS count
            """,
            asset_id_field="org_id",
            asset_label="OktaOrganization",
            identity_fields=("org_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=("iam", "privileged_access", "session_management", "stride:spoofing"),
    version="1.0.0",
    references=STIG_REFERENCES
    + [
        RuleReference(
            text="Okta Help: Configure the Okta Admin Console session",
            url="https://help.okta.com/okta_help.htm?type=oie&id=ext-admin-console-session",
        ),
    ],
    frameworks=(
        stig_okta("V-273187"),
        iso27001_annex_a("8.5"),
        iso27001_annex_a("8.2"),
        soc2_tsc("CC6.1"),
    ),
)


# =============================================================================
# Okta Admin Console and Dashboard authentication policies
# (V-273190, V-273191, V-273193, V-273194)
# Main node: OktaPolicy (type ACCESS_POLICY)
# =============================================================================
class OktaFirstPartyAppPolicyOutput(Finding):
    """Output model for weak Okta Admin Console or Dashboard authentication policies."""

    policy_id: str | None = None
    policy_name: str | None = None
    rule_id: str | None = None
    rule_name: str | None = None
    factor_mode: str | None = None
    phishing_resistant_required: bool | None = None
    org_id: str | None = None


# Okta has shipped both names for the preset Dashboard policy.
_DASHBOARD_POLICY_NAMES = ("Okta Dashboard", "Okta Dashboard Policy")
_ADMIN_CONSOLE_POLICY_NAMES = ("Okta Admin Console",)


def _first_party_app_policy(
    app_name: str,
    default_policy_names: tuple[str, ...],
) -> str:
    # The policy is identified by the first-party app it is assigned to. If that
    # app could not be resolved during sync (read-only admins cannot read Okta's
    # own apps), fall back to the preset policy names.
    names = ", ".join(f"'{name}'" for name in default_policy_names)
    return f"""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(p:OktaPolicy)
    WHERE p.type = 'ACCESS_POLICY' AND p.status = 'ACTIVE'
      AND (
          '{app_name}' IN coalesce(p.first_party_app_names, [])
          OR (
              size(coalesce(p.first_party_app_names, [])) = 0
              AND p.name IN [{names}]
          )
      )
    """


def _first_party_app_fact(
    fact_id: str,
    name: str,
    description: str,
    app_name: str,
    default_policy_names: tuple[str, ...],
    violation: str,
) -> Fact:
    policy = _first_party_app_policy(app_name, default_policy_names)
    top_allow_rule = f"""
    {policy}
    MATCH (p)-[:HAS_RULE]->(r:OktaPolicyRule)
    WHERE r.status = 'ACTIVE' AND r.access = 'ALLOW'
    WITH o, p, r
    ORDER BY r.priority
    WITH o, p, collect(r)[0] AS top_rule
    WHERE {violation}
    """
    return Fact(
        id=fact_id,
        name=name,
        description=description,
        cypher_query=f"""
        {top_allow_rule}
        RETURN
            p.id AS policy_id,
            p.name AS policy_name,
            top_rule.id AS rule_id,
            top_rule.name AS rule_name,
            top_rule.factor_mode AS factor_mode,
            top_rule.phishing_resistant_required AS phishing_resistant_required,
            o.id AS org_id
        """,
        cypher_visual_query=f"""
        {top_allow_rule}
        MATCH path=(o)-[:RESOURCE]->(p)-[:HAS_RULE]->(top_rule)
        RETURN path
        """,
        cypher_count_query=f"""
        {policy}
        RETURN COUNT(p) AS count
        """,
        asset_id_field="policy_id",
        asset_label="OktaPolicy",
        identity_fields=("policy_id",),
        module=Module.OKTA,
        maturity=Maturity.EXPERIMENTAL,
    )


_AUTHENTICATION_POLICY_REFERENCES = STIG_REFERENCES + [
    RuleReference(
        text="Okta Help: Authentication policies",
        url="https://help.okta.com/okta_help.htm?type=oie&id=ext-about-asop",
    ),
]
_PHISHING_RESISTANT_VIOLATION = (
    "coalesce(top_rule.phishing_resistant_required, false) = false"
)
_MFA_VIOLATION = "coalesce(top_rule.factor_mode, '1FA') <> '2FA'"

okta_dashboard_phishing_resistant_not_required = Rule(
    id="okta_dashboard_phishing_resistant_not_required",
    name="Dashboard Allows Phishable Authenticators",
    description=(
        "Sign-in to the Okta Dashboard should require a phishing-resistant "
        "authenticator, such as FIDO2/WebAuthn or Okta FastPass."
    ),
    output_model=OktaFirstPartyAppPolicyOutput,
    facts=(
        _first_party_app_fact(
            "okta_dashboard_policy_phishing_resistant_not_required",
            "Okta Dashboard authentication policies without phishing resistance",
            "Detects Okta Dashboard authentication policies whose highest-priority "
            "allow rule does not require a phishing-resistant possession factor.",
            "okta_enduser",
            _DASHBOARD_POLICY_NAMES,
            _PHISHING_RESISTANT_VIOLATION,
        ),
    ),
    tags=("iam", "authentication", "mfa", "phishing", "stride:spoofing"),
    version="1.0.0",
    references=_AUTHENTICATION_POLICY_REFERENCES,
    frameworks=(
        stig_okta("V-273190"),
        iso27001_annex_a("8.5"),
        soc2_tsc("CC6.1"),
    ),
)

okta_admin_console_phishing_resistant_not_required = Rule(
    id="okta_admin_console_phishing_resistant_not_required",
    name="Admin Console Allows Phishable Authenticators",
    description=(
        "Sign-in to the Okta Admin Console should require a phishing-resistant "
        "authenticator, such as FIDO2/WebAuthn or Okta FastPass."
    ),
    output_model=OktaFirstPartyAppPolicyOutput,
    facts=(
        _first_party_app_fact(
            "okta_admin_console_policy_phishing_resistant_not_required",
            "Okta Admin Console authentication policies without phishing resistance",
            "Detects Okta Admin Console authentication policies whose highest-priority "
            "allow rule does not require a phishing-resistant possession factor.",
            "saasure",
            _ADMIN_CONSOLE_POLICY_NAMES,
            _PHISHING_RESISTANT_VIOLATION,
        ),
    ),
    tags=(
        "iam",
        "authentication",
        "mfa",
        "phishing",
        "privileged_access",
        "stride:spoofing",
    ),
    version="1.0.0",
    references=_AUTHENTICATION_POLICY_REFERENCES,
    frameworks=(
        stig_okta("V-273191"),
        iso27001_annex_a("8.5"),
        iso27001_annex_a("8.2"),
        soc2_tsc("CC6.1"),
    ),
)

okta_admin_console_mfa_not_required = Rule(
    id="okta_admin_console_mfa_not_required",
    name="Admin Console Does Not Require MFA",
    description=(
        "Sign-in to the Okta Admin Console should require two factor types "
        '("Password/IdP + Another factor" or "Any 2 factor types").'
    ),
    output_model=OktaFirstPartyAppPolicyOutput,
    facts=(
        _first_party_app_fact(
            "okta_admin_console_policy_single_factor",
            "Okta Admin Console authentication policies allowing one factor",
            "Detects Okta Admin Console authentication policies whose highest-priority "
            "allow rule accepts a single factor type.",
            "saasure",
            _ADMIN_CONSOLE_POLICY_NAMES,
            _MFA_VIOLATION,
        ),
    ),
    tags=("iam", "authentication", "mfa", "privileged_access", "stride:spoofing"),
    version="1.0.0",
    references=_AUTHENTICATION_POLICY_REFERENCES,
    frameworks=(
        stig_okta("V-273193"),
        iso27001_annex_a("8.5"),
        iso27001_annex_a("8.2"),
        soc2_tsc("CC6.1"),
    ),
)

okta_dashboard_mfa_not_required = Rule(
    id="okta_dashboard_mfa_not_required",
    name="Dashboard Does Not Require MFA",
    description=(
        "Sign-in to the Okta Dashboard should require two factor types "
        '("Password/IdP + Another factor" or "Any 2 factor types").'
    ),
    output_model=OktaFirstPartyAppPolicyOutput,
    facts=(
        _first_party_app_fact(
            "okta_dashboard_policy_single_factor",
            "Okta Dashboard authentication policies allowing one factor",
            "Detects Okta Dashboard authentication policies whose highest-priority "
            "allow rule accepts a single factor type.",
            "okta_enduser",
            _DASHBOARD_POLICY_NAMES,
            _MFA_VIOLATION,
        ),
    ),
    tags=("iam", "authentication", "mfa", "stride:spoofing"),
    version="1.0.0",
    references=_AUTHENTICATION_POLICY_REFERENCES,
    frameworks=(
        stig_okta("V-273194"),
        iso27001_annex_a("8.5"),
        soc2_tsc("CC6.1"),
    ),
)


# =============================================================================
# Password policy checks (V-273189, V-273195 to V-273201, V-273208, V-273209)
# Main node: OktaPolicy (type PASSWORD)
# =============================================================================
class OktaPasswordPolicyOutput(Finding):
    """Output model for Okta password policies that miss a STIG setting."""

    policy_id: str | None = None
    policy_name: str | None = None
    priority: int | None = None
    password_min_length: int | None = None
    password_min_lowercase: int | None = None
    password_min_uppercase: int | None = None
    password_min_number: int | None = None
    password_min_symbol: int | None = None
    password_common_password_check: bool | None = None
    password_min_age_minutes: int | None = None
    password_max_age_days: int | None = None
    password_history_count: int | None = None
    lockout_max_attempts: int | None = None
    org_id: str | None = None


# Password policies for users whose credentials Okta manages. Policies for
# Active Directory or LDAP users defer to the directory and are out of scope.
_OKTA_PASSWORD_POLICY = """
    MATCH (o:OktaOrganization)-[:RESOURCE]->(p:OktaPolicy)
    WHERE p.type = 'PASSWORD' AND p.status = 'ACTIVE'
      AND coalesce(p.auth_provider, 'OKTA') = 'OKTA'
"""

_PASSWORD_REFERENCES = STIG_REFERENCES + [
    RuleReference(
        text="Okta Help: Configure a password policy",
        url="https://help.okta.com/okta_help.htm?type=oie&id=ext-configure-password",
    ),
]


def _password_policy_rule(
    rule_id: str,
    vuln_id: str,
    name: str,
    description: str,
    fact_id: str,
    fact_name: str,
    violation: str,
    iso_requirements: tuple[str, ...] = ("5.17",),
) -> Rule:
    return Rule(
        id=rule_id,
        name=name,
        description=description,
        output_model=OktaPasswordPolicyOutput,
        facts=(
            Fact(
                id=fact_id,
                name=fact_name,
                description=f"Detects active Okta password policies where {fact_name[0].lower()}{fact_name[1:]}.",
                cypher_query=f"""
                {_OKTA_PASSWORD_POLICY}
                  AND ({violation})
                RETURN
                    p.id AS policy_id,
                    p.name AS policy_name,
                    p.priority AS priority,
                    p.password_min_length AS password_min_length,
                    p.password_min_lowercase AS password_min_lowercase,
                    p.password_min_uppercase AS password_min_uppercase,
                    p.password_min_number AS password_min_number,
                    p.password_min_symbol AS password_min_symbol,
                    p.password_common_password_check AS password_common_password_check,
                    p.password_min_age_minutes AS password_min_age_minutes,
                    p.password_max_age_days AS password_max_age_days,
                    p.password_history_count AS password_history_count,
                    p.lockout_max_attempts AS lockout_max_attempts,
                    o.id AS org_id
                """,
                cypher_visual_query=f"""
                {_OKTA_PASSWORD_POLICY}
                  AND ({violation})
                MATCH path=(o)-[:RESOURCE]->(p)
                RETURN path
                """,
                cypher_count_query=f"""
                {_OKTA_PASSWORD_POLICY}
                RETURN COUNT(p) AS count
                """,
                asset_id_field="policy_id",
                asset_label="OktaPolicy",
                identity_fields=("policy_id",),
                module=Module.OKTA,
                maturity=Maturity.EXPERIMENTAL,
            ),
        ),
        tags=("iam", "authentication", "password_policy", "stride:spoofing"),
        version="1.0.0",
        references=_PASSWORD_REFERENCES,
        frameworks=(
            stig_okta(vuln_id),
            *(iso27001_annex_a(requirement) for requirement in iso_requirements),
            soc2_tsc("CC6.1"),
        ),
    )


okta_password_lockout_threshold_too_high = _password_policy_rule(
    "okta_password_lockout_threshold_too_high",
    "V-273189",
    "Password Lockout Threshold Too High",
    "Okta should lock an account after at most three consecutive failed sign-in "
    "attempts to slow down password guessing.",
    "okta_password_policy_lockout_over_3_attempts",
    "Lockout is disabled or allows more than 3 failed attempts",
    "coalesce(p.lockout_max_attempts, 0) = 0 OR p.lockout_max_attempts > 3",
    iso_requirements=("8.5",),
)

okta_password_min_length_too_short = _password_policy_rule(
    "okta_password_min_length_too_short",
    "V-273195",
    "Password Minimum Length Too Short",
    "Okta passwords should be at least 15 characters long.",
    "okta_password_policy_min_length_under_15",
    "The minimum password length is under 15 characters",
    "coalesce(p.password_min_length, 0) < 15",
)

okta_password_uppercase_not_required = _password_policy_rule(
    "okta_password_uppercase_not_required",
    "V-273196",
    "Password Uppercase Character Not Required",
    "Okta passwords should contain at least one uppercase character.",
    "okta_password_policy_uppercase_not_required",
    "An uppercase character is not required",
    "coalesce(p.password_min_uppercase, 0) < 1",
)

okta_password_lowercase_not_required = _password_policy_rule(
    "okta_password_lowercase_not_required",
    "V-273197",
    "Password Lowercase Character Not Required",
    "Okta passwords should contain at least one lowercase character.",
    "okta_password_policy_lowercase_not_required",
    "A lowercase character is not required",
    "coalesce(p.password_min_lowercase, 0) < 1",
)

okta_password_number_not_required = _password_policy_rule(
    "okta_password_number_not_required",
    "V-273198",
    "Password Number Not Required",
    "Okta passwords should contain at least one numeric character.",
    "okta_password_policy_number_not_required",
    "A numeric character is not required",
    "coalesce(p.password_min_number, 0) < 1",
)

okta_password_symbol_not_required = _password_policy_rule(
    "okta_password_symbol_not_required",
    "V-273199",
    "Password Symbol Not Required",
    "Okta passwords should contain at least one special character.",
    "okta_password_policy_symbol_not_required",
    "A special character is not required",
    "coalesce(p.password_min_symbol, 0) < 1",
)

okta_password_min_age_too_short = _password_policy_rule(
    "okta_password_min_age_too_short",
    "V-273200",
    "Password Minimum Age Too Short",
    "Okta passwords should be kept for at least 24 hours before they can be changed, "
    "so users cannot cycle through their password history immediately.",
    "okta_password_policy_min_age_under_24_hours",
    "The minimum password age is under 24 hours",
    "coalesce(p.password_min_age_minutes, 0) < 1440",
)

okta_password_max_age_too_long = _password_policy_rule(
    "okta_password_max_age_too_long",
    "V-273201",
    "Password Maximum Age Too Long",
    "Okta passwords should expire after at most 60 days.",
    "okta_password_policy_max_age_over_60_days",
    "Passwords never expire or expire after more than 60 days",
    "coalesce(p.password_max_age_days, 0) = 0 OR p.password_max_age_days > 60",
)

okta_password_common_password_check_disabled = _password_policy_rule(
    "okta_password_common_password_check_disabled",
    "V-273208",
    "Common Password Check Disabled",
    "Okta should reject passwords found in its list of commonly used and "
    "compromised passwords.",
    "okta_password_policy_common_password_check_disabled",
    "The common password check is disabled",
    "coalesce(p.password_common_password_check, false) = false",
)

okta_password_history_too_short = _password_policy_rule(
    "okta_password_history_too_short",
    "V-273209",
    "Password History Too Short",
    "Okta should prevent reuse of at least the last five passwords.",
    "okta_password_policy_history_under_5",
    "Fewer than 5 previous passwords are remembered",
    "coalesce(p.password_history_count, 0) < 5",
)


# =============================================================================
# V-273202: System Log is not streamed to a central log server
# Main node: OktaOrganization
# =============================================================================
class OktaLogStreamMissingOutput(Finding):
    """Output model for Okta orgs without an active log stream."""

    org_id: str | None = None
    log_stream_count: int | None = None


# Orgs whose log streams were read in their latest sync. Without this, an org
# whose token lacks okta.logStreams.read would look like one with no streams.
_ORG_WITH_SYNCED_LOG_STREAMS = """
    MATCH (o:OktaOrganization)
    WHERE EXISTS {
        MATCH (m:ModuleSyncMetadata)
        WHERE m.grouptype = 'OktaOrganization'
          AND m.syncedtype = 'OktaLogStream'
          AND m.groupid = o.id
          AND m.lastupdated = o.lastupdated
    }
"""

okta_system_log_not_streamed = Rule(
    id="okta_system_log_not_streamed",
    name="System Log Not Streamed",
    description=(
        "Okta System Log events should be offloaded to a central log server or SIEM "
        "so they are retained and monitored outside Okta."
    ),
    output_model=OktaLogStreamMissingOutput,
    facts=(
        Fact(
            id="okta_org_without_active_log_stream",
            name="Okta orgs without an active log stream",
            description=(
                "Detects Okta orgs with no active log stream. Orgs whose log streams "
                "were not synced are not evaluated. A SIEM that pulls the System Log "
                "through the API instead also satisfies the control and is not "
                "visible here."
            ),
            cypher_query=f"""
            {_ORG_WITH_SYNCED_LOG_STREAMS}
              AND NOT (o)-[:RESOURCE]->(:OktaLogStream {{status: 'ACTIVE'}})
            OPTIONAL MATCH (o)-[:RESOURCE]->(s:OktaLogStream)
            RETURN o.id AS org_id, count(s) AS log_stream_count
            """,
            cypher_visual_query=f"""
            {_ORG_WITH_SYNCED_LOG_STREAMS}
              AND NOT (o)-[:RESOURCE]->(:OktaLogStream {{status: 'ACTIVE'}})
            OPTIONAL MATCH path=(o)-[:RESOURCE]->(:OktaLogStream)
            RETURN o, path
            """,
            cypher_count_query=f"""
            {_ORG_WITH_SYNCED_LOG_STREAMS}
            RETURN COUNT(o) AS count
            """,
            asset_id_field="org_id",
            asset_label="OktaOrganization",
            identity_fields=("org_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=("logging", "monitoring", "stride:repudiation"),
    version="1.0.0",
    references=STIG_REFERENCES
    + [
        RuleReference(
            text="Okta Help: Log streaming",
            url="https://help.okta.com/okta_help.htm?type=oie&id=ext-log-streaming",
        ),
    ],
    frameworks=(
        stig_okta("V-273202"),
        iso27001_annex_a("8.15"),
        soc2_tsc("CC7.2"),
    ),
)


# =============================================================================
# API token checks (V-279689, V-279690)
# Main node: OktaApiToken
# =============================================================================
class OktaApiTokenOutput(Finding):
    """Output model for Okta API tokens that miss a STIG setting."""

    token_id: str | None = None
    token_name: str | None = None
    network_connection: str | None = None
    user_id: str | None = None
    owner_login: str | None = None
    org_id: str | None = None


_API_TOKEN_REFERENCES = STIG_REFERENCES + [
    RuleReference(
        text="Okta Developer: Manage Okta API tokens",
        url="https://developer.okta.com/docs/guides/create-an-api-token/main/",
    ),
]

# A token has exactly one owner; a pattern comprehension reads it without fanning out.
_TOKEN_OWNER_LOGIN = "head([(t)-[:OWNED_BY]->(owner:OktaUser) | owner.login])"

_API_TOKEN_WITHOUT_ZONE = """
    MATCH (o:OktaOrganization)-[:RESOURCE]->(t:OktaApiToken)
    WHERE NOT (
        coalesce(t.network_connection, 'ANYWHERE') = 'ZONE'
        AND EXISTS { (t)-[:ALLOWED_FROM]->(:OktaNetworkZone) }
    )
"""

okta_api_token_without_network_zone = Rule(
    id="okta_api_token_without_network_zone",
    name="API Token Usable From Any Network",
    description=(
        "Okta API tokens should only be accepted from the network zones of the "
        "systems that call the API, so a leaked token is useless elsewhere."
    ),
    output_model=OktaApiTokenOutput,
    facts=(
        Fact(
            id="okta_api_token_not_restricted_to_zone",
            name="Okta API tokens not restricted to a network zone",
            description=(
                "Detects Okta API tokens that can be used from any network instead of "
                "only from specific network zones."
            ),
            cypher_query=f"""
            {_API_TOKEN_WITHOUT_ZONE}
            RETURN
                t.id AS token_id,
                t.name AS token_name,
                t.network_connection AS network_connection,
                t.user_id AS user_id,
                {_TOKEN_OWNER_LOGIN} AS owner_login,
                o.id AS org_id
            """,
            cypher_visual_query=f"""
            {_API_TOKEN_WITHOUT_ZONE}
            OPTIONAL MATCH path=(t)-[:OWNED_BY]->(:OktaUser)
            RETURN t, path
            """,
            cypher_count_query="""
            MATCH (t:OktaApiToken)
            RETURN COUNT(t) AS count
            """,
            asset_id_field="token_id",
            asset_label="OktaApiToken",
            identity_fields=("token_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=("iam", "credentials", "network", "stride:spoofing"),
    version="1.0.0",
    references=_API_TOKEN_REFERENCES,
    frameworks=(
        stig_okta("V-279689"),
        iso27001_annex_a("5.17"),
        soc2_tsc("CC6.1"),
    ),
)

# A user is a super administrator through a direct role assignment, a group role
# assignment, or the legacy administration role model.
# Reading admin roles needs more than a read-only token. Only evaluate orgs whose
# user and group roles were synced, so a missing role is not mistaken for none.
_ORG_WITH_SYNCED_ADMIN_ROLES = """
    MATCH (o:OktaOrganization)
    WHERE all(synced_type IN ['OktaUserRole', 'OktaGroupRole'] WHERE EXISTS {
        MATCH (m:ModuleSyncMetadata)
        WHERE m.grouptype = 'OktaOrganization'
          AND m.syncedtype = synced_type
          AND m.groupid = o.id
          AND m.lastupdated = o.lastupdated
    })
"""

_API_TOKEN_OWNED_BY_SUPER_ADMIN = (
    _ORG_WITH_SYNCED_ADMIN_ROLES
    + """
    MATCH (o)-[:RESOURCE]->(t:OktaApiToken)
    WHERE EXISTS {
        MATCH (t)-[:OWNED_BY]->(u:OktaUser)
        WHERE EXISTS {
            MATCH (u)-[:HAS_ROLE]->(role:OktaUserRole)
            WHERE role.role_type = 'SUPER_ADMIN'
        } OR EXISTS {
            MATCH (u)-[:MEMBER_OF_OKTA_GROUP|MEMBER_OF]->(:OktaGroup)-[:HAS_ROLE]->(role:OktaGroupRole)
            WHERE role.role_type = 'SUPER_ADMIN'
        } OR EXISTS {
            MATCH (u)-[:MEMBER_OF_OKTA_ROLE]->(role:OktaAdministrationRole)
            WHERE role.type = 'SUPER_ADMIN'
        }
    }
"""
)

okta_api_token_owned_by_super_admin = Rule(
    id="okta_api_token_owned_by_super_admin",
    name="API Token Owned by Super Administrator",
    description=(
        "Okta API tokens act with the roles of the user who owns them. Tokens should "
        "be created under dedicated accounts holding only the admin roles the "
        "integration needs, never a super administrator."
    ),
    output_model=OktaApiTokenOutput,
    facts=(
        Fact(
            id="okta_api_token_owner_is_super_admin",
            name="Okta API tokens owned by super administrators",
            description=(
                "Detects Okta API tokens whose owner holds the Super Administrator "
                "role directly or through a group. Only evaluates orgs whose admin "
                "roles were synced, which needs a token that can read admin roles."
            ),
            cypher_query=f"""
            {_API_TOKEN_OWNED_BY_SUPER_ADMIN}
            RETURN
                t.id AS token_id,
                t.name AS token_name,
                t.network_connection AS network_connection,
                t.user_id AS user_id,
                {_TOKEN_OWNER_LOGIN} AS owner_login,
                o.id AS org_id
            """,
            cypher_visual_query=f"""
            {_API_TOKEN_OWNED_BY_SUPER_ADMIN}
            MATCH path=(t)-[:OWNED_BY]->(:OktaUser)
            RETURN path
            """,
            cypher_count_query=f"""
            {_ORG_WITH_SYNCED_ADMIN_ROLES}
            MATCH (o)-[:RESOURCE]->(t:OktaApiToken)
            RETURN COUNT(t) AS count
            """,
            asset_id_field="token_id",
            asset_label="OktaApiToken",
            identity_fields=("token_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=("iam", "credentials", "privileged_access", "stride:elevation_of_privilege"),
    version="1.0.0",
    references=_API_TOKEN_REFERENCES,
    frameworks=(
        stig_okta("V-279690"),
        iso27001_annex_a("8.2"),
        soc2_tsc("CC6.3"),
    ),
)


# =============================================================================
# V-279692: No network zone blocks anonymizing proxies
# Main node: OktaOrganization
# =============================================================================
class OktaAnonymizerBlocklistMissingOutput(Finding):
    """Output model for Okta orgs without an anonymizer blocklist zone."""

    org_id: str | None = None
    zone_count: int | None = None


# Orgs with at least one synced zone: every org has system zones, so an org
# without any was not synced with okta.networkZones.read and is not evaluated.
_ORG_WITHOUT_ANONYMIZER_BLOCKLIST = """
    MATCH (o:OktaOrganization)-[:RESOURCE]->(zone:OktaNetworkZone)
    WITH o, count(zone) AS zone_count
    WHERE NOT EXISTS {
        MATCH (o)-[:RESOURCE]->(z:OktaNetworkZone)
        WHERE z.status = 'ACTIVE' AND z.usage = 'BLOCKLIST'
          AND (
              (
                  z.type = 'DYNAMIC_V2'
                  AND any(
                      category IN coalesce(z.ip_service_categories_include, [])
                      WHERE category IN ['ALL_ANONYMIZERS', 'ALL_IP_SERVICES']
                         OR category CONTAINS 'ANONYMIZER'
                  )
              )
              OR (z.type = 'DYNAMIC' AND z.proxy_type IN ['TorAnonymizer', 'Any'])
              OR (z.type = 'IP' AND size(coalesce(z.gateways, [])) > 0)
          )
    }
"""

okta_anonymizer_blocklist_missing = Rule(
    id="okta_anonymizer_blocklist_missing",
    name="Anonymizing Proxies Not Blocked",
    description=(
        "Okta should block sign-in from anonymizing proxies and Tor, either with the "
        "enhanced dynamic zone blocklist or an IP blocklist of known anonymizers."
    ),
    output_model=OktaAnonymizerBlocklistMissingOutput,
    facts=(
        Fact(
            id="okta_org_without_anonymizer_blocklist_zone",
            name="Okta orgs without an active anonymizer blocklist zone",
            description=(
                "Detects Okta orgs with no active blocklist zone that blocks "
                "anonymizers: an enhanced dynamic zone matching anonymizer IP service "
                "categories, a dynamic zone matching Tor or any proxy, or an IP zone "
                "with blocked gateway addresses."
            ),
            cypher_query=f"""
            {_ORG_WITHOUT_ANONYMIZER_BLOCKLIST}
            RETURN o.id AS org_id, zone_count
            """,
            cypher_visual_query=f"""
            {_ORG_WITHOUT_ANONYMIZER_BLOCKLIST}
            MATCH path=(o)-[:RESOURCE]->(:OktaNetworkZone)
            RETURN path
            """,
            cypher_count_query="""
            MATCH (o:OktaOrganization)
            WHERE (o)-[:RESOURCE]->(:OktaNetworkZone)
            RETURN COUNT(o) AS count
            """,
            asset_id_field="org_id",
            asset_label="OktaOrganization",
            identity_fields=("org_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=("network", "access_control", "stride:spoofing"),
    version="1.0.0",
    references=STIG_REFERENCES
    + [
        RuleReference(
            text="Okta Help: Enhanced dynamic zones",
            url="https://help.okta.com/okta_help.htm?type=oie&id=ext-dynamic-network-zones",
        ),
    ],
    frameworks=(
        stig_okta("V-279692"),
        iso27001_annex_a("8.20"),
        soc2_tsc("CC6.6"),
    ),
)


# =============================================================================
# V-279693: Application authentication policy without network zones
# Main node: OktaApplication
# =============================================================================
class OktaAppPolicyWithoutZoneOutput(Finding):
    """Output model for app authentication policies that have no network zones."""

    policy_id: str | None = None
    policy_name: str | None = None
    app_count: int | None = None
    app_labels: list[str] | None = None
    org_id: str | None = None


# One finding per policy, not per app: the fix is a zone rule on the policy, and
# an org's default policy often covers most of its apps.
_APP_POLICY_WITHOUT_ZONE = """
    MATCH (o:OktaOrganization)-[:RESOURCE]->(p:OktaPolicy)-[:APPLIES_TO]->(app:OktaApplication)
    WHERE p.type = 'ACCESS_POLICY'
      AND coalesce(app.status, 'ACTIVE') = 'ACTIVE'
      AND NOT EXISTS {
          MATCH (p)-[:HAS_RULE]->(r:OktaPolicyRule)
          WHERE r.status = 'ACTIVE' AND r.network_connection = 'ZONE'
      }
    WITH o, p, collect(DISTINCT coalesce(app.label, app.name, app.id)) AS app_labels
"""

okta_app_policy_without_network_zones = Rule(
    id="okta_app_policy_without_network_zones",
    name="App Authentication Policy Without Network Zones",
    description=(
        "Each app authentication policy should allow or deny access by network "
        "zone according to the access control policy of the apps it covers."
    ),
    output_model=OktaAppPolicyWithoutZoneOutput,
    facts=(
        Fact(
            id="okta_app_authentication_policy_without_zone_condition",
            name="Okta app authentication policies with no network zone condition",
            description=(
                "Detects Okta app authentication policies that cover active apps but "
                "have no active rule with a network zone condition."
            ),
            cypher_query=f"""
            {_APP_POLICY_WITHOUT_ZONE}
            RETURN
                p.id AS policy_id,
                p.name AS policy_name,
                size(app_labels) AS app_count,
                app_labels[0..20] AS app_labels,
                o.id AS org_id
            """,
            cypher_visual_query=f"""
            {_APP_POLICY_WITHOUT_ZONE}
            MATCH path=(p)-[:APPLIES_TO]->(:OktaApplication)
            RETURN path
            """,
            cypher_count_query="""
            MATCH (p:OktaPolicy)-[:APPLIES_TO]->(app:OktaApplication)
            WHERE p.type = 'ACCESS_POLICY' AND coalesce(app.status, 'ACTIVE') = 'ACTIVE'
            RETURN COUNT(DISTINCT p) AS count
            """,
            asset_id_field="policy_id",
            asset_label="OktaPolicy",
            identity_fields=("policy_id",),
            module=Module.OKTA,
            maturity=Maturity.EXPERIMENTAL,
        ),
    ),
    tags=("iam", "network", "access_control", "stride:spoofing"),
    version="1.0.0",
    references=_AUTHENTICATION_POLICY_REFERENCES,
    frameworks=(
        stig_okta("V-279693"),
        iso27001_annex_a("5.15"),
        soc2_tsc("CC6.6"),
    ),
)
