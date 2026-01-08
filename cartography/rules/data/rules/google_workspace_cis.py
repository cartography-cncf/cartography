"""Google Workspace CIS benchmark-aligned rules.

These rules mirror the CIS Google Workspace Foundations Benchmark where possible
with the data currently ingested by Cartography.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference


class GoogleWorkspaceCISFinding(Finding):
    """Shared finding model for Google Workspace CIS checks."""

    cis_id: str | None = None
    control_name: str | None = None
    severity: str | None = None
    target_label: str | None = None
    target_id: str | None = None
    target_email: str | None = None
    property_check: str | None = None
    remediation: str | None = None
    reference: str | None = None


_google_workspace_cis_reference = RuleReference(
    text="CIS Google Workspace Foundations Benchmark v1.4.0",
    url="https://www.cisecurity.org/benchmark/google_workspace",
)

# Control 1.1 – Enforce 2-Step Verification for all users
_cis_1_1_2sv_not_enforced = Fact(
    id="gw-cis-1-1-2sv-not-enforced",
    name="Users without enforced 2-Step Verification",
    description=(
        "Identifies Google Workspace users that do not have 2-Step Verification enforcement enabled. "
        "Requires Google Workspace user ingestion (admin.directory.user.security scope)."
    ),
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
    cypher_query="""
    MATCH (u:GoogleWorkspaceUser)
    WHERE coalesce(u.isEnforcedIn2Sv, false) = false
    RETURN
        u.id AS target_id,
        u.primaryEmail AS target_email,
        'Control 1.1 - Enforce 2-Step Verification for all users' AS control_name,
        u.isAdmin AS is_admin,
        u.orgUnitPath AS org_unit_path,
        u.isEnrolledIn2Sv AS is_enrolled_in_2sv,
        'GoogleWorkspaceUser' AS target_label,
        '1.1' AS cis_id,
        'HIGH' AS severity,
        'isEnforcedIn2Sv=false' AS property_check,
        'Enforce 2-Step Verification for all user org units.' AS remediation,
        'CIS 1.1 - Enforce 2-Step Verification' AS reference
    """,
    cypher_visual_query="""
    MATCH p=(u:GoogleWorkspaceUser)-[:RESOURCE]->(:GoogleWorkspaceTenant)
    WHERE coalesce(u.isEnforcedIn2Sv, false) = false
    RETURN p
    """,
)

# Control 1.2 – Ensure super admins are enrolled in 2-Step Verification
_cis_1_2_admin_not_enrolled = Fact(
    id="gw-cis-1-2-admin-2sv-not-enrolled",
    name="Admin accounts without enrolled 2-Step Verification",
    description=(
        "Finds Google Workspace super admin accounts that are not enrolled in 2-Step Verification. "
        "Requires Google Workspace user ingestion (admin.directory.user.security scope)."
    ),
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
    cypher_query="""
    MATCH (u:GoogleWorkspaceUser)
    WHERE u.isAdmin = true AND coalesce(u.isEnrolledIn2Sv, false) = false
    RETURN
        u.id AS target_id,
        u.primaryEmail AS target_email,
        'Control 1.2 - Super admins enrolled in 2-Step Verification' AS control_name,
        u.isEnforcedIn2Sv AS is_enforced_in_2sv,
        u.orgUnitPath AS org_unit_path,
        'GoogleWorkspaceUser' AS target_label,
        '1.2' AS cis_id,
        'CRITICAL' AS severity,
        'isAdmin=true AND isEnrolledIn2Sv=false' AS property_check,
        'Enroll super admins in 2-Step Verification with enforcement.' AS remediation,
        'CIS 1.2 - Ensure super admin accounts use 2-Step Verification' AS reference
    """,
    cypher_visual_query="""
    MATCH p=(u:GoogleWorkspaceUser)-[:RESOURCE]->(:GoogleWorkspaceTenant)
    WHERE u.isAdmin = true AND coalesce(u.isEnrolledIn2Sv, false) = false
    RETURN p
    """,
)


# Control 2.1 – Review high-risk third-party OAuth access
_cis_2_1_high_risk_oauth_scopes = Fact(
    id="gw-cis-2-1-high-risk-oauth-scopes",
    name="OAuth apps with high-risk scopes",
    description=(
        "Detects third-party OAuth apps authorized with high-risk scopes such as Admin SDK or full Drive access. "
        "Requires OAuth token ingestion with scopes. TODO: extend coverage once device management and context-aware "
        "access scopes are ingested."
    ),
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
    cypher_query="""
    WITH [
        'https://www.googleapis.com/auth/admin.directory.user',
        'https://www.googleapis.com/auth/admin.directory.group',
        'https://www.googleapis.com/auth/admin.directory.device.mobile.action',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/drive'
    ] AS high_risk_scopes
    MATCH (u:GoogleWorkspaceUser)-[auth:AUTHORIZED]->(app:GoogleWorkspaceOAuthApp)
    WHERE any(scope IN auth.scopes WHERE scope IN high_risk_scopes)
    WITH u, app, auth, high_risk_scopes,
        [scope IN auth.scopes WHERE scope IN high_risk_scopes] AS violating_scopes
    RETURN
        app.client_id AS target_id,
        app.display_text AS app_name,
        u.primaryEmail AS target_email,
        violating_scopes AS violating_scopes,
        'Control 2.1 - Review high-risk OAuth access' AS control_name,
        'GoogleWorkspaceOAuthApp' AS target_label,
        '2.1' AS cis_id,
        'MEDIUM' AS severity,
        'AUTHORIZED scopes include admin or broad data access permissions' AS property_check,
        'Restrict or trust-list third-party apps before granting high-risk OAuth scopes.' AS remediation,
        'CIS 2.1 - Limit API access to trusted OAuth apps' AS reference
    """,
    cypher_visual_query="""
    WITH [
        'https://www.googleapis.com/auth/admin.directory.user',
        'https://www.googleapis.com/auth/admin.directory.group',
        'https://www.googleapis.com/auth/admin.directory.device.mobile.action',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/drive'
    ] AS high_risk_scopes
    MATCH p=(u:GoogleWorkspaceUser)-[auth:AUTHORIZED]->(app:GoogleWorkspaceOAuthApp)
    WHERE any(scope IN auth.scopes WHERE scope IN high_risk_scopes)
    RETURN p
    """,
)


google_workspace_cis_1_1_enforce_2sv = Rule(
    id="google_workspace_cis_1_1_enforce_2sv",
    name="CIS 1.1 - Enforce 2-Step Verification",
    description=(
        "Detect users without enforced 2-Step Verification. Requires Google Workspace user ingestion "
        "with security fields (admin.directory.user.security scope)."
    ),
    tags=("cis", "googleworkspace", "identity", "compliance"),
    version="0.1.0",
    facts=(_cis_1_1_2sv_not_enforced,),
    output_model=GoogleWorkspaceCISFinding,
    references=[_google_workspace_cis_reference],
)

google_workspace_cis_1_2_admins_enrolled_2sv = Rule(
    id="google_workspace_cis_1_2_admins_enrolled_2sv",
    name="CIS 1.2 - Super admins enrolled in 2-Step Verification",
    description=(
        "Detect super admin accounts not enrolled in 2-Step Verification. Requires Google Workspace user "
        "ingestion with security fields (admin.directory.user.security scope)."
    ),
    tags=("cis", "googleworkspace", "identity", "compliance"),
    version="0.1.0",
    facts=(_cis_1_2_admin_not_enrolled,),
    output_model=GoogleWorkspaceCISFinding,
    references=[_google_workspace_cis_reference],
)

google_workspace_cis_2_1_high_risk_oauth = Rule(
    id="google_workspace_cis_2_1_high_risk_oauth",
    name="CIS 2.1 - Review high-risk OAuth access",
    description=(
        "Detect third-party OAuth apps authorized with high-risk scopes (Admin SDK, Drive, Gmail). "
        "Requires OAuth token ingestion with scopes for users."
    ),
    tags=("cis", "googleworkspace", "identity", "compliance"),
    version="0.1.0",
    facts=(_cis_2_1_high_risk_oauth_scopes,),
    output_model=GoogleWorkspaceCISFinding,
    references=[_google_workspace_cis_reference],
)
