"""
CIS Google Workspace Identity Security Checks

Implements CIS Google Workspace Foundations Benchmark Section 4: Identity and Access Management
Based on CIS Google Workspace Foundations Benchmark v1.4.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Framework
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS Google Workspace Foundations Benchmark v1.4.0",
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
        Framework(
            name="CIS Google Workspace Foundations Benchmark",
            short_name="CIS",
            scope="googleworkspace",
            revision="1.4",
            requirement="4.1.1.3",
        ),
    ),
)


# =============================================================================
# CIS Google Workspace 4.1.1.1: Admin accounts without enforced 2-Step Verification
# Main node: GoogleWorkspaceUser
# =============================================================================
class AdminWithout2SVOutput(Finding):
    """Output model for admin accounts without enforced 2-Step Verification."""

    user_id: str | None = None
    primary_email: str | None = None
    org_unit_path: str | None = None
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
    WHERE u.is_admin = true AND coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN
        u.id AS user_id,
        u.primary_email AS primary_email,
        u.org_unit_path AS org_unit_path,
        u.is_enrolled_in_2_sv AS is_enrolled_in_2sv,
        u.is_enforced_in_2_sv AS is_enforced_in_2sv,
        t.id AS tenant_id
    """,
    cypher_visual_query="""
    MATCH p=(t:GoogleWorkspaceTenant)-[:RESOURCE]->(u:GoogleWorkspaceUser)
    WHERE u.is_admin = true AND coalesce(u.is_enforced_in_2_sv, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (u:GoogleWorkspaceUser)
    WHERE u.is_admin = true
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
        Framework(
            name="CIS Google Workspace Foundations Benchmark",
            short_name="CIS",
            scope="googleworkspace",
            revision="1.4",
            requirement="4.1.1.1",
        ),
    ),
)
