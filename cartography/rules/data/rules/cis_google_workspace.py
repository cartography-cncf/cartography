"""
CIS Google Workspace Identity Security Checks

Implements CIS Google Workspace Foundations Benchmark Section 4: Identity and Access Management
Based on CIS Google Workspace Foundations Benchmark v1.3.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.data.frameworks.cis import cis_google_workspace
from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS Google Workspace Foundations Benchmark v1.3.0",
        url="https://www.cisecurity.org/benchmark/google_workspace",
    ),
    RuleReference(
        text="Google Workspace Admin Help: 2-Step Verification",
        url="https://support.google.com/a/answer/175197",
    ),
]


# =============================================================================
# CIS Google Workspace 4.1.1.3: Users without enforced 2-Step Verification
# Main node: GoogleWorkspaceUser
# =============================================================================
class UserWithout2SVOutput(Finding):
    """Output model for users without enforced 2-Step Verification."""

    user_id: str | None = None
    primary_email: str | None = None
    is_admin: bool | None = None
    org_unit_path: str | None = None
    is_enrolled_in_2sv: bool | None = None
    is_enforced_in_2sv: bool | None = None
    tenant_id: str | None = None


_gw_user_2sv_not_enforced = Fact(
    id="gw_user_2sv_not_enforced",
    name="Google Workspace users without enforced 2-Step Verification",
    description=(
        "Detects Google Workspace users that do not have 2-Step Verification enforcement enabled. "
        "Users who are enrolled but not enforced can disable 2SV at any time, which is a security risk. "
        "Requires admin.directory.user.security scope."
    ),
    cypher_query="""
    MATCH (t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN
        u.id AS user_id,
        u.primary_email AS primary_email,
        u.is_admin AS is_admin,
        u.org_unit_path AS org_unit_path,
        u.is_enrolled_in_2_sv AS is_enrolled_in_2sv,
        u.is_enforced_in_2_sv AS is_enforced_in_2sv,
        t.id AS tenant_id
    """,
    cypher_visual_query="""
    MATCH p=(t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (u:GoogleWorkspaceUser)
    RETURN COUNT(u) AS count
    """,
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gw_4_1_1_3_user_2sv_not_enforced = Rule(
    id="cis_gw_4_1_1_3_user_2sv_not_enforced",
    name="CIS Google Workspace 4.1.1.3: Users Without Enforced 2-Step Verification",
    description=(
        "2-Step Verification should be enforced for all users to prevent unauthorized access. "
        "Enrolled but not enforced users can disable 2SV at any time."
    ),
    output_model=UserWithout2SVOutput,
    facts=(_gw_user_2sv_not_enforced,),
    tags=("iam", "authentication", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_google_workspace("4.1.1.3"),
        iso27001_annex_a("8.5"),
    ),
)

# =============================================================================
# TODO: CIS Google Workspace 4.1.1.3: Partial control coverage
# Missing datamodel: tenant or OU-scoped 2SV policy settings for enrollment period, trusted-device allowance, and allowed 2SV methods
# =============================================================================


# =============================================================================
# CIS Google Workspace 4.1.1.1: Admin accounts without enforced 2-Step Verification
# Main node: GoogleWorkspaceUser
# =============================================================================
class AdminWithout2SVOutput(Finding):
    """Output model for admin accounts without enforced 2-Step Verification."""

    user_id: str | None = None
    primary_email: str | None = None
    org_unit_path: str | None = None
    is_admin: bool | None = None
    is_delegated_admin: bool | None = None
    is_enrolled_in_2sv: bool | None = None
    is_enforced_in_2sv: bool | None = None
    tenant_id: str | None = None


_gw_admin_2sv_not_enforced = Fact(
    id="gw_admin_2sv_not_enforced",
    name="Google Workspace admin accounts without enforced 2-Step Verification",
    description=(
        "Detects Google Workspace admin accounts that do not have 2-Step Verification enforced. "
        "Admin accounts have elevated privileges and are high-value targets for attackers. "
        "Requires admin.directory.user.security scope."
    ),
    cypher_query="""
    MATCH (t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE
        (coalesce(u.is_admin, false) = true OR coalesce(u.is_delegated_admin, false) = true)
        AND coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN
        u.id AS user_id,
        u.primary_email AS primary_email,
        u.org_unit_path AS org_unit_path,
        u.is_admin AS is_admin,
        u.is_delegated_admin AS is_delegated_admin,
        u.is_enrolled_in_2_sv AS is_enrolled_in_2sv,
        u.is_enforced_in_2_sv AS is_enforced_in_2sv,
        t.id AS tenant_id
    """,
    cypher_visual_query="""
    MATCH p=(t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE
        (coalesce(u.is_admin, false) = true OR coalesce(u.is_delegated_admin, false) = true)
        AND coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_admin, false) = true OR coalesce(u.is_delegated_admin, false) = true
    RETURN COUNT(u) AS count
    """,
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gw_4_1_1_1_admin_2sv_not_enforced = Rule(
    id="cis_gw_4_1_1_1_admin_2sv_not_enforced",
    name="CIS Google Workspace 4.1.1.1: Admins Without Enforced 2-Step Verification",
    description=(
        "Admin accounts should have 2-Step Verification enforced due to their elevated privileges. "
        "Enrolled but not enforced admins can disable 2SV, creating a significant security risk."
    ),
    output_model=AdminWithout2SVOutput,
    facts=(_gw_admin_2sv_not_enforced,),
    tags=("iam", "authentication", "privileged_access", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_google_workspace("4.1.1.1"),
        iso27001_annex_a("8.5"),
        iso27001_annex_a("8.2"),
    ),
)

# =============================================================================
# TODO: CIS Google Workspace 4.1.1.1: Partial control coverage
# Missing datamodel: tenant or OU-scoped 2SV policy settings for enrollment period, trusted-device allowance, and allowed 2SV methods
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.1.1.2: Hardware security keys for admins and high-value accounts
# Missing datamodel: security key enrollment or requirement state per user or group, plus 2SV policy fields for security-key-only methods, suspension grace period, and security-code generation
# =============================================================================


# =============================================================================
# CIS Google Workspace 1.1.1: More than one Super Admin account exists
# Main node: GoogleWorkspaceTenant
# =============================================================================
class SuperAdminCoverageOutput(Finding):
    """Output model for tenant-level Super Admin coverage findings."""

    tenant_id: str | None = None
    tenant_domain: str | None = None
    super_admin_count: int | None = None


class SuperAdminExcessOutput(Finding):
    """Output model for tenants with excessive Super Admin coverage."""

    tenant_id: str | None = None
    tenant_domain: str | None = None
    super_admin_count: int | None = None


_gw_super_admin_count_too_low = Fact(
    id="gw_super_admin_count_too_low",
    name="Google Workspace tenants with fewer than two Super Admin accounts",
    description=(
        "Detects tenants with zero or one Super Admin account. Google Workspace "
        "user.is_admin maps directly to the Super Admin role in this data model."
    ),
    cypher_query="""
    MATCH (t:GoogleWorkspaceTenant)
    OPTIONAL MATCH (t)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_admin, false) = true
    WITH t, count(DISTINCT u) AS super_admin_count
    WHERE super_admin_count <= 1
    RETURN
        t.id AS tenant_id,
        t.domain AS tenant_domain,
        super_admin_count
    """,
    cypher_visual_query="""
    MATCH (t:GoogleWorkspaceTenant)
    OPTIONAL MATCH p=(t)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_admin, false) = true
    WITH t, collect(p) AS paths, count(DISTINCT u) AS super_admin_count
    WHERE super_admin_count <= 1
    UNWIND paths AS p
    RETURN t, p
    """,
    cypher_count_query="""
    MATCH (t:GoogleWorkspaceTenant)
    RETURN COUNT(t) AS count
    """,
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gw_1_1_1_super_admin_count_too_low = Rule(
    id="cis_gw_1_1_1_super_admin_count_too_low",
    name="CIS Google Workspace 1.1.1: More Than One Super Admin Account Exists",
    description=(
        "Google Workspace tenants should maintain at least two Super Admin accounts "
        "to avoid a single point of failure for privileged administration."
    ),
    output_model=SuperAdminCoverageOutput,
    facts=(_gw_super_admin_count_too_low,),
    tags=("iam", "privileged_access", "resilience"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_google_workspace("1.1.1"),
        iso27001_annex_a("8.2"),
    ),
)


# =============================================================================
# CIS Google Workspace 1.1.2: No more than 4 Super Admin accounts exist
# Main node: GoogleWorkspaceTenant
# =============================================================================
_gw_super_admin_count_too_high = Fact(
    id="gw_super_admin_count_too_high",
    name="Google Workspace tenants with more than four Super Admin accounts",
    description=(
        "Detects tenants with more than four Super Admin accounts. Google Workspace "
        "user.is_admin maps directly to the Super Admin role in this data model."
    ),
    cypher_query="""
    MATCH (t:GoogleWorkspaceTenant)
    OPTIONAL MATCH (t)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_admin, false) = true
    WITH t, count(DISTINCT u) AS super_admin_count
    WHERE super_admin_count > 4
    RETURN
        t.id AS tenant_id,
        t.domain AS tenant_domain,
        super_admin_count
    """,
    cypher_visual_query="""
    MATCH (t:GoogleWorkspaceTenant)
    OPTIONAL MATCH p=(t)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_admin, false) = true
    WITH t, collect(p) AS paths, count(DISTINCT u) AS super_admin_count
    WHERE super_admin_count > 4
    UNWIND paths AS p
    RETURN t, p
    """,
    cypher_count_query="""
    MATCH (t:GoogleWorkspaceTenant)
    RETURN COUNT(t) AS count
    """,
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gw_1_1_2_super_admin_count_too_high = Rule(
    id="cis_gw_1_1_2_super_admin_count_too_high",
    name="CIS Google Workspace 1.1.2: No More Than 4 Super Admin Accounts Exist",
    description=(
        "Google Workspace tenants should limit the number of Super Admin accounts "
        "to reduce the privileged attack surface."
    ),
    output_model=SuperAdminExcessOutput,
    facts=(_gw_super_admin_count_too_high,),
    tags=("iam", "privileged_access", "least_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_google_workspace("1.1.2"),
        iso27001_annex_a("8.2"),
        iso27001_annex_a("5.18"),
    ),
)


# =============================================================================
# CIS Google Workspace 1.1.3: Super Admin accounts are used only for super admin activities
# Main node: GoogleWorkspaceUser
# =============================================================================
class SuperAdminDualRoleOutput(Finding):
    """Output model for Super Admins that also hold delegated admin roles."""

    user_id: str | None = None
    primary_email: str | None = None
    org_unit_path: str | None = None
    tenant_id: str | None = None


_gw_super_admin_with_delegated_admin_role = Fact(
    id="gw_super_admin_with_delegated_admin_role",
    name="Google Workspace Super Admin accounts also marked as delegated admins",
    description=(
        "Finds accounts that are simultaneously Super Admins and delegated admins, "
        "which violates the benchmark's dedicated-admin-account guidance."
    ),
    cypher_query="""
    MATCH (t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_admin, false) = true AND coalesce(u.is_delegated_admin, false) = true
    RETURN
        u.id AS user_id,
        u.primary_email AS primary_email,
        u.org_unit_path AS org_unit_path,
        t.id AS tenant_id
    """,
    cypher_visual_query="""
    MATCH p=(t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_admin, false) = true AND coalesce(u.is_delegated_admin, false) = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (u:GoogleWorkspaceUser)
    WHERE coalesce(u.is_admin, false) = true
    RETURN COUNT(u) AS count
    """,
    module=Module.GOOGLEWORKSPACE,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gw_1_1_3_super_admin_used_for_daily_admin = Rule(
    id="cis_gw_1_1_3_super_admin_used_for_daily_admin",
    name="CIS Google Workspace 1.1.3: Super Admin Accounts Used Only for Super Admin Activities",
    description=(
        "Super Admin accounts should remain dedicated to top-level administration "
        "and not also be used as delegated admin accounts."
    ),
    output_model=SuperAdminDualRoleOutput,
    facts=(_gw_super_admin_with_delegated_admin_role,),
    tags=("iam", "privileged_access", "least_privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_google_workspace("1.1.3"),
        iso27001_annex_a("8.2"),
    ),
)


# =============================================================================
# TODO: CIS Google Workspace 1.1.3: Partial control coverage
# Missing datamodel: evidence of daily end-user activity or sign-in purpose; current graph can only detect dual Super Admin and delegated-admin assignment
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 1.2.1.1: Directory data access is externally restricted
# Missing datamodel: tenant-level Directory settings for external directory sharing mode
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.1.1.1: External sharing options for primary calendars are configured
# Missing datamodel: Calendar policy settings at tenant or OU scope for external sharing on primary calendars
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.1.1.2: Internal sharing options for primary calendars are configured
# Missing datamodel: Calendar policy settings at tenant or OU scope for internal sharing on primary calendars
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.1.1.3: External invitation warnings for Google Calendar are configured
# Missing datamodel: Calendar invitation warning setting at tenant or OU scope
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.1.2.1: External sharing options for secondary calendars are configured
# Missing datamodel: Calendar policy settings at tenant or OU scope for external sharing on secondary calendars
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.1.2.2: Internal sharing options for secondary calendars are configured
# Missing datamodel: Calendar policy settings at tenant or OU scope for internal sharing on secondary calendars
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.1.3.1: Calendar web offline is disabled
# Missing datamodel: Calendar advanced settings for offline access at tenant or OU scope
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.1.1: Users are warned when they share a file outside their domain
# Missing datamodel: Drive sharing settings for external-share warning behavior
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.1.2: Users cannot publish files to the web or make visible to the world
# Missing datamodel: Drive sharing settings controlling public or unlisted publication
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.1.3: Document sharing is controlled by domain with allowlists
# Missing datamodel: Drive external-sharing mode and compatible allowlisted domain settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.1.4: Users are warned when they share a file with users in an allowlisted domain
# Missing datamodel: Drive allowlisted-domain warning settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.1.5: Access Checker is configured to limit file access
# Missing datamodel: Drive Access Checker configuration state
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.1.6: Only users inside your organization can distribute content externally
# Missing datamodel: Drive content-distribution settings for cross-org shared-drive distribution
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.2.1: Users can create new shared drives
# Missing datamodel: Drive shared-drive creation policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.2.2: Manager access members cannot modify shared drive settings
# Missing datamodel: Drive shared-drive manager override settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.2.3: Shared drive file access is restricted to members only
# Missing datamodel: Drive shared-drive member-only file access settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.1.2.4: Viewers and commenters cannot download, print, and copy files
# Missing datamodel: Drive shared-drive viewer and commenter restriction settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.2.1: Offline access to documents is disabled
# Missing datamodel: Drive offline-access policy settings and managed-device policy linkage
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.2.2: Desktop access to Drive is disabled
# Missing datamodel: Drive for desktop enablement settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.2.2.3: Add-Ons is disabled
# Missing datamodel: Docs Add-On access settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.1.1: Users cannot delegate access to their mailbox
# Missing datamodel: Gmail mail-delegation policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.1.2: Offline access to Gmail is disabled
# Missing datamodel: Gmail web-offline settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.2.1: DKIM is enabled for all mail-enabled domains
# Missing datamodel: mail-enabled domain inventory plus DKIM selector and authentication state per domain
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.2.2: SPF record is configured for all mail-enabled domains
# Missing datamodel: mail-enabled domain inventory plus DNS TXT records or normalized SPF status per domain
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.2.3: DMARC record is configured for all mail-enabled domains
# Missing datamodel: mail-enabled domain inventory plus DNS TXT records or normalized DMARC status per domain
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.3.1: Quarantine admin notifications for Gmail are enabled
# Missing datamodel: Gmail quarantine configuration and notification settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.1.1: Protection against encrypted attachments from untrusted senders is enabled
# Missing datamodel: Gmail safety attachment-policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.1.2: Protection against attachments with scripts from untrusted senders is enabled
# Missing datamodel: Gmail safety attachment-policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.1.3: Protection against anomalous attachment types in emails is enabled
# Missing datamodel: Gmail safety attachment-policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.2.1: Link identification behind shortened URLs is enabled
# Missing datamodel: Gmail safety link-protection settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.2.2: Scan linked images for malicious content is enabled
# Missing datamodel: Gmail linked-image scanning settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.2.3: Warning prompt is shown for clicks on links to untrusted domains
# Missing datamodel: Gmail untrusted-link warning settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.3.1: Protection against domain spoofing based on similar domain names is enabled
# Missing datamodel: Gmail spoofing-protection settings and configured action state
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.3.2: Protection against spoofing of employee names is enabled
# Missing datamodel: Gmail employee-name spoofing settings and configured action state
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.3.3: Protection against inbound emails spoofing your domain is enabled
# Missing datamodel: Gmail inbound-domain-spoofing settings and configured action state
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.3.4: Protection against any unauthenticated emails is enabled
# Missing datamodel: Gmail unauthenticated-email protection settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.4.3.5: Groups are protected from inbound emails spoofing your domain
# Missing datamodel: Gmail group-spoofing settings and configured action state
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.5.1: POP and IMAP access is disabled for all users
# Missing datamodel: Gmail POP and IMAP policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.5.2: Automatic forwarding options are disabled
# Missing datamodel: Gmail automatic-forwarding policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.5.3: Per-user outbound gateways is disabled
# Missing datamodel: Gmail outbound-gateway policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.5.4: External recipient warnings are enabled
# Missing datamodel: Gmail external-recipient warning settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.6.1: Enhanced pre-delivery message scanning is enabled
# Missing datamodel: Gmail spam, phishing, and malware scanning settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.6.2: Spam filters are not bypassed for internal senders
# Missing datamodel: Gmail spam-filter bypass settings for internal senders
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.7.1: Comprehensive mail storage is enabled
# Missing datamodel: Gmail compliance settings for comprehensive mail storage
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.3.7.2: Send email over a secure TLS connection is enabled
# Missing datamodel: Gmail TLS compliance settings for inbound and outbound mail
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.4.1.1: External filesharing in Google Chat and Hangouts is disabled
# Missing datamodel: Google Chat file-sharing policy settings for external sharing
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.4.1.2: Internal filesharing in Google Chat and Hangouts is disabled
# Missing datamodel: Google Chat file-sharing policy settings for internal sharing
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.4.2.1: Google Chat externally is restricted to allowed domains
# Missing datamodel: Google Chat external-chat settings and allowlisted domains
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.4.3.1: External spaces in Google Chat and Hangouts are restricted
# Missing datamodel: Google Chat external-spaces settings and allowlisted domains
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.4.4.1: Allow users to install Chat apps is disabled
# Missing datamodel: Google Chat app-install policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.4.4.2: Allow users to add and use incoming webhooks is disabled
# Missing datamodel: Google Chat incoming-webhook policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.6.1: Accessing groups from outside this organization is private
# Missing datamodel: Groups for Business sharing settings for external access
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.6.2: Creating groups is restricted
# Missing datamodel: Groups for Business creation-policy settings and external-member controls
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.6.3: Default permission to view conversations is restricted
# Missing datamodel: Groups for Business default conversation-visibility settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.7.1: Service status for Google Sites is set to off
# Missing datamodel: Sites service-status settings at tenant or OU scope
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.8.1: Access to external Google Groups is off for everyone
# Missing datamodel: Additional Google services status for external Google Groups
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 3.1.9.1.1: Users access to Google Workspace Marketplace apps is restricted
# Missing datamodel: Marketplace app-install policy settings and allowlist mode
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.1.2.1: Super Admin account recovery is disabled
# Missing datamodel: Super Admin account-recovery settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.1.2.2: User account recovery is enabled
# Missing datamodel: user account-recovery settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.1.3.1: Advanced Protection Program is configured
# Missing datamodel: Advanced Protection enrollment and security-code policy settings per user, group, or OU
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.1.4.1: Login challenges are enforced
# Missing datamodel: post-SSO verification and login-challenge policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.1.5.1: Password policy is configured for enhanced security
# Missing datamodel: password policy settings for strong-password enforcement, minimum length, reuse, and expiration
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.1.1: Application access to Google services is restricted
# Missing datamodel: API control settings for Google service access restrictions and trusted-app state
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.1.2: Third-party applications are reviewed periodically
# Missing datamodel: review evidence for third-party app access, such as review timestamp, reviewer, or disposition
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.1.3: Internal apps can access Google Workspace APIs
# Missing datamodel: API control settings for trusting internal domain-owned apps
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.1.4: Domain-wide delegation for applications is reviewed periodically
# Missing datamodel: domain-wide delegation grants plus review evidence such as review timestamp, reviewer, or disposition
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.2.1: Blocking access from unapproved geographic locations
# Missing datamodel: Context-Aware Access levels, geographic conditions, and app-to-access-level assignments
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.3.1: DLP policies for Google Drive are configured
# Missing datamodel: Drive DLP rule inventory, enabled state, and scope
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.4.1: Google session control is configured
# Missing datamodel: Google web session-duration settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.5.1: Google Cloud session control is configured
# Missing datamodel: Google Cloud reauthentication policy settings, method, and trusted-app exemption state
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.2.6.1: Less secure app access is disabled
# Missing datamodel: less-secure-app access policy settings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.3.1: Dashboard is reviewed regularly for anomalies
# Missing datamodel: review evidence for Security Center dashboard checks, such as review timestamp, reviewer, or findings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 4.3.2: Security health is reviewed regularly for anomalies
# Missing datamodel: review evidence for Security health checks, such as review timestamp, reviewer, or findings
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 5.1.1.1: App Usage Report is reviewed regularly for anomalies
# Missing datamodel: imported report snapshots or review evidence for App Usage reports
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 5.1.1.2: Security Report is reviewed regularly for anomalies
# Missing datamodel: imported report snapshots or review evidence for Security reports
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 6.1: User's password changed rule is configured
# Missing datamodel: Google-provided alert-rule configuration with enabled state, severity, email notifications, and recipients
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 6.2: Government-backed attacks rule is configured
# Missing datamodel: Google-provided alert-rule configuration with enabled state, severity, email notifications, and recipients
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 6.3: User suspended due to suspicious activity rule is configured
# Missing datamodel: Google-provided alert-rule configuration with enabled state, severity, email notifications, and recipients
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 6.4: User granted Admin privilege rule is configured
# Missing datamodel: Google-provided alert-rule configuration with enabled state, severity, email notifications, and recipients
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 6.5: Suspicious programmatic login rule is configured
# Missing datamodel: Google-provided alert-rule configuration with enabled state, severity, email notifications, and recipients
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 6.6: Suspicious login rule is configured
# Missing datamodel: Google-provided alert-rule configuration with enabled state, severity, email notifications, and recipients
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 6.7: Leaked password rule is configured
# Missing datamodel: Google-provided alert-rule configuration with enabled state, severity, email notifications, and recipients
# =============================================================================

# =============================================================================
# TODO: CIS Google Workspace 6.8: Gmail potential employee spoofing rule is configured
# Missing datamodel: Google-provided alert-rule configuration with enabled state, severity, email notifications, and recipients
# =============================================================================
