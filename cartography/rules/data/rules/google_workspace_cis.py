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

# Control 1.1 – Enforce 2-Step Verification for all users (CIS 4.1.1.3)
_cis_1_1_2sv_not_enforced = Fact(
    id="gw-cis-1-1-2sv-not-enforced",
    name="Users without enforced 2-Step Verification",
    description=(
        "Identifies Google Workspace users that do not have 2-Step Verification enforcement enabled. "
        "Aligns with CIS 4.1.1.3. Uses coalesce to treat missing security data as non-compliant. "
        "Requires admin.directory.user.security scope."
    ),
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
    cypher_query="""
    MATCH (u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN
        u.id AS target_id,
        u.primary_email AS target_email,
        'Control 1.1 - Users without enforced 2-Step Verification' AS control_name,
        u.is_admin AS is_admin,
        u.org_unit_path AS org_unit_path,
        u.is_enrolled_in_2_sv AS is_enrolled_in_2sv,
        'GoogleWorkspaceUser' AS target_label,
        '1.1' AS cis_id,
        'HIGH' AS severity,
        'is_enforced_in_2_sv=false' AS property_check,
        'Enforce 2-Step Verification for all user org units via Security > 2-Step Verification.' AS remediation,
        'CIS 4.1.1.3 - Ensure 2-Step Verification is enforced for all users' AS reference
    """,
    cypher_visual_query="""
    MATCH p=(t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN p
    """,
    cypher_count_query="""
    MATCH (u:GoogleWorkspaceUser)
    RETURN COUNT(u) AS count
    """,
)

# Control 1.2 – Ensure super admins have 2-Step Verification enforced (CIS 4.1.1.1)
_cis_1_2_admin_2sv_not_enforced = Fact(
    id="gw-cis-1-2-admin-2sv-not-enforced",
    name="Admin accounts without enforced 2-Step Verification",
    description=(
        "Finds Google Workspace admin accounts that do not have 2-Step Verification enforced. "
        "Admins who are enrolled but not enforced can still disable 2SV, which is a security risk. "
        "Aligns with CIS 4.1.1.1. Requires admin.directory.user.security scope."
    ),
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
    cypher_query="""
    MATCH (u:GoogleWorkspaceUser)
    WHERE u.is_admin = true AND coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN
        u.id AS target_id,
        u.primary_email AS target_email,
        'Control 1.2 - Admin accounts without enforced 2-Step Verification' AS control_name,
        u.is_enrolled_in_2_sv AS is_enrolled_in_2sv,
        u.is_enforced_in_2_sv AS is_enforced_in_2sv,
        u.org_unit_path AS org_unit_path,
        'GoogleWorkspaceUser' AS target_label,
        '1.2' AS cis_id,
        'CRITICAL' AS severity,
        'is_admin=true AND is_enforced_in_2_sv=false' AS property_check,
        'Enforce 2-Step Verification for all admin accounts via Security > 2-Step Verification.' AS remediation,
        'CIS 4.1.1.1 - Ensure 2-Step Verification is enforced for all users in administrative roles' AS reference
    """,
    cypher_visual_query="""
    MATCH p=(t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE u.is_admin = true AND coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN p
    """,
    cypher_count_query="""
    MATCH (u:GoogleWorkspaceUser)
    WHERE u.is_admin = true
    RETURN COUNT(u) AS count
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
        u.primary_email AS target_email,
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
    cypher_count_query="""
    MATCH (app:GoogleWorkspaceOAuthApp)
    RETURN COUNT(app) AS count
    """,
    asset_id_field="target_id",
)


google_workspace_cis_1_1_enforce_2sv = Rule(
    id="google_workspace_cis_1_1_enforce_2sv",
    name="CIS Google Workspace 1.1: Enforce 2-Step Verification",
    description=(
        "Detect users without enforced 2-Step Verification. Requires Google Workspace user ingestion "
        "with security fields (admin.directory.user.security scope)."
    ),
    tags=(
        "cis:1.1",
        "cis:googleworkspace-1.4",
        "identity",
        "authentication",
        "stride:spoofing",
    ),
    version="0.1.0",
    facts=(_cis_1_1_2sv_not_enforced,),
    output_model=GoogleWorkspaceCISFinding,
    references=[_google_workspace_cis_reference],
)

google_workspace_cis_1_2_admins_enforced_2sv = Rule(
    id="google_workspace_cis_1_2_admins_enforced_2sv",
    name="CIS Google Workspace 1.2: Admin 2-Step Verification Enforcement",
    description=(
        "Detect admin accounts without enforced 2-Step Verification. Enrolled but not enforced is "
        "non-compliant per CIS 4.1.1.1. Requires admin.directory.user.security scope."
    ),
    tags=(
        "cis:1.2",
        "cis:googleworkspace-1.4",
        "identity",
        "authentication",
        "stride:spoofing",
    ),
    version="0.1.0",
    facts=(_cis_1_2_admin_2sv_not_enforced,),
    output_model=GoogleWorkspaceCISFinding,
    references=[_google_workspace_cis_reference],
)

google_workspace_cis_2_1_high_risk_oauth = Rule(
    id="google_workspace_cis_2_1_high_risk_oauth",
    name="CIS Google Workspace 2.1: High-Risk OAuth Access",
    description=(
        "Detect third-party OAuth apps authorized with high-risk scopes (Admin SDK, Drive, Gmail). "
        "Requires OAuth token ingestion with scopes for users."
    ),
    tags=(
        "cis:2.1",
        "cis:googleworkspace-1.4",
        "identity",
        "oauth",
        "stride:information_disclosure",
    ),
    version="0.1.0",
    facts=(_cis_2_1_high_risk_oauth_scopes,),
    output_model=GoogleWorkspaceCISFinding,
    references=[_google_workspace_cis_reference],
)
