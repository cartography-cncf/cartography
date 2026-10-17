from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS
_aws_account_manipulation_permissions = Fact(
    id="aws_account_manipulation_permissions",
    name="IAM Principals with Account Creation and Modification Permissions",
    description=(
        "AWS IAM users and roles with permissions to create, modify, or delete IAM "
        "accounts and their associated policies."
    ),
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        MATCH (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND principal.name <> 'OrganizationAccountAccessRole'
        AND stmt.effect = 'Allow'
        WITH a, principal, stmt, policy,
            [label IN labels(principal) WHERE label <> 'AWSPrincipal'][0] AS principal_type,
            [p IN ['iam:Create','iam:Attach','iam:Put','iam:Update','iam:Add'] | p] AS patterns
        // Match only Allow statements whose actions fit the patterns
        WITH a, principal, principal_type, stmt, policy,
            [action IN stmt.action
                WHERE (ANY(prefix IN patterns WHERE action STARTS WITH prefix)
                    OR action = 'iam:*'
                    OR action = '*')
                AND NOT action IN ['iam:CreateServiceLinkedRole', 'iam:DeleteServiceLinkedRole']
            ] AS matched_allow_actions
        WHERE size(matched_allow_actions) > 0
        // Find explicit Deny statements for the same principal that overlap
        OPTIONAL MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(deny_stmt:AWSPolicyStatement {effect:"Deny"})
        WHERE ANY(deny_action IN deny_stmt.action
                    WHERE deny_action IN matched_allow_actions
                    OR deny_action = 'iam:*'
                    OR deny_action = '*')
        // If a deny exists, exclude those principals
        WITH a, principal, principal_type, policy, stmt, matched_allow_actions, deny_stmt
        WHERE deny_stmt IS NULL
        // Aggregate one row per (account, principal, policy). Substitute a single-null
        // list when stmt.resource is missing so NotResource-only statements still emit
        // (the principal stays visible; resources just won't include those entries).
        UNWIND matched_allow_actions AS action
        UNWIND coalesce(stmt.resource, [null]) AS resource
        WITH a, principal, principal_type, policy,
             collect(DISTINCT action) AS actions,
             [r IN collect(DISTINCT resource) WHERE r IS NOT NULL] AS resources
        // Drop principals whose only matched action is iam:CreateServiceLinkedRole;
        // it is scoped (included in PowerUserAccess) and not real identity-admin capability.
        WHERE NOT (size(actions) = 1 AND actions[0] = 'iam:CreateServiceLinkedRole')
        RETURN
            a.name AS account,
            a.id AS account_id,
            principal.name AS principal_name,
            principal.arn AS principal_identifier,
            principal_type,
            policy.id AS policy_id,
            policy.name AS policy_name,
            actions,
            resources
        ORDER BY account, principal_name, policy_name
    """,
    cypher_visual_query="""
        MATCH p = (a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        MATCH p1 = (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND NOT principal.name = 'OrganizationAccountAccessRole'
        AND stmt.effect = 'Allow'
        AND ANY(action IN stmt.action WHERE
            (action STARTS WITH 'iam:Create'
                OR action STARTS WITH 'iam:Attach'
                OR action STARTS WITH 'iam:Put'
                OR action STARTS WITH 'iam:Update'
                OR action STARTS WITH 'iam:Add'
                OR action = 'iam:*'
                OR action = '*')
            AND NOT action IN ['iam:CreateServiceLinkedRole', 'iam:DeleteServiceLinkedRole']
        )
        RETURN *
    """,
    cypher_count_query="""
    MATCH (principal:AWSPrincipal)
    WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
    AND NOT principal.name CONTAINS 'QuickSetup'
    AND principal.name <> 'OrganizationAccountAccessRole'
    RETURN COUNT(principal) AS count
    """,
    asset_label="AWSPrincipal",
    asset_id_field="principal_identifier",
    identity_fields=("account_id", "principal_identifier", "policy_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# GCP
_gcp_account_manipulation_permissions = Fact(
    id="gcp_account_manipulation_permissions",
    name="GCP Principals with Identity Administration Permissions",
    description=(
        "GCP principals (service accounts, users, groups) bound to a role "
        "that grants permissions to create, update, or impersonate IAM "
        "identities. Includes role wildcards (`iam.*`, `*`) and the most "
        "common identity-administration permissions: "
        "iam.serviceAccounts.create / actAs / setIamPolicy / "
        "iam.serviceAccountKeys.create / iam.roles.create / iam.roles.update."
    ),
    cypher_query="""
    MATCH (binding:GCPPolicyBinding)-[:APPLIES_TO]->(scope)
    WHERE any(label IN labels(scope)
              WHERE label IN ['GCPProject', 'GCPFolder', 'GCPOrganization'])
    MATCH (principal:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(binding)
    MATCH (binding)-[:GRANTS_ROLE]->(role:GCPRole)
    WITH scope, principal, role,
        [
            'iam.serviceAccounts.create',
            'iam.serviceAccounts.actAs',
            'iam.serviceAccounts.setIamPolicy',
            'iam.serviceAccounts.update',
            'iam.serviceAccountKeys.create',
            'iam.roles.create',
            'iam.roles.update',
            'resourcemanager.projects.setIamPolicy',
            'resourcemanager.folders.setIamPolicy',
            'resourcemanager.organizations.setIamPolicy'
        ] AS patterns
    WITH scope, principal, role, patterns,
         [perm IN coalesce(role.permissions, [])
            WHERE perm IN patterns
               OR perm = 'iam.*'
               OR perm = 'resourcemanager.*'
               OR perm = '*'] AS matched
    WHERE size(matched) > 0
    RETURN DISTINCT
        scope.id AS account_id,
        scope.id AS account,
        coalesce(principal.email, principal.id) AS principal_name,
        principal.id AS principal_identifier,
        coalesce(
            head([l IN ['GCPServiceAccount', 'GoogleWorkspaceUser', 'GoogleWorkspaceGroup']
                  WHERE l IN labels(principal)]),
            head([l IN ['ServiceAccount', 'UserAccount', 'UserGroup']
                  WHERE l IN labels(principal)])
        ) AS principal_type,
        role.name AS policy_name,
        matched AS actions,
        [scope.id] AS resources
    ORDER BY account, principal_name
    """,
    cypher_visual_query="""
    MATCH p1=(principal:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(binding:GCPPolicyBinding)-[:APPLIES_TO]->(scope)
    WHERE any(label IN labels(scope)
              WHERE label IN ['GCPProject', 'GCPFolder', 'GCPOrganization'])
    MATCH p2=(binding)-[:GRANTS_ROLE]->(role:GCPRole)
    WHERE ANY(perm IN coalesce(role.permissions, []) WHERE
        perm IN [
            'iam.serviceAccounts.create',
            'iam.serviceAccounts.actAs',
            'iam.serviceAccounts.setIamPolicy',
            'iam.serviceAccounts.update',
            'iam.serviceAccountKeys.create',
            'iam.roles.create',
            'iam.roles.update',
            'resourcemanager.projects.setIamPolicy',
            'resourcemanager.folders.setIamPolicy',
            'resourcemanager.organizations.setIamPolicy'
        ]
        OR perm = 'iam.*'
        OR perm = 'resourcemanager.*'
        OR perm = '*'
    )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (principal:GCPPrincipal)
    RETURN COUNT(principal) AS count
    """,
    asset_label="GCPPrincipal",
    asset_id_field="principal_identifier",
    identity_fields=("account_id", "principal_identifier", "policy_name"),
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


# Azure
_azure_account_manipulation_permissions = Fact(
    id="azure_account_manipulation_permissions",
    name="Azure Principals with Identity Administration Permissions",
    description=(
        "Entra principals (users, groups, service principals) holding a role "
        "assignment whose role definition grants permissions to manage role "
        "assignments, role definitions, or directory-level identities. "
        "Matches `Microsoft.Authorization/*/write`, "
        "`Microsoft.Authorization/roleAssignments/write`, "
        "`Microsoft.Authorization/roleDefinitions/write`, "
        "`Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action`, "
        "and the broader `*` wildcard. Excludes assignments shadowed by "
        "matching `not_actions`."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(ra:AzureRoleAssignment)
    MATCH (ra)-[:ROLE_ASSIGNED]->(rd:AzureRoleDefinition)-[:HAS_PERMISSIONS]->(perm:AzurePermissions)
    // EntraPrincipal is the umbrella label carried by EntraUser, EntraGroup and
    // EntraServicePrincipal. Matching it directly keeps the returned rows aligned
    // with the declared asset_label and lets Neo4j use the label index.
    MATCH (principal:EntraPrincipal)-[:HAS_ROLE_ASSIGNMENT]->(ra)
    // For each literal RBAC pattern, treat each action / not_action as a
    // case-insensitive glob: replace `.` with the regex char class `[.]`
    // (so dots are literal), then `*` with `.*`. A `*` anywhere in the
    // entry now correctly matches. This makes the built-in Contributor
    // role (actions=['*'], not_actions=['Microsoft.Authorization/*/Write',
    // 'Microsoft.Authorization/*/Delete', ...]) drop the role-assignment
    // / role-definition / managed-identity patterns rather than flag.
    WITH sub, ra, rd, perm, principal,
         coalesce(perm.actions, []) AS role_actions,
         coalesce(perm.not_actions, []) AS role_not_actions,
        [
            'Microsoft.Authorization/roleAssignments/write',
            'Microsoft.Authorization/roleAssignments/delete',
            'Microsoft.Authorization/roleDefinitions/write',
            'Microsoft.Authorization/roleDefinitions/delete',
            'Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action'
        ] AS patterns
    WITH sub, ra, rd, perm, principal, role_not_actions,
        [
            p IN patterns
            WHERE ANY(a IN role_actions WHERE
                toLower(p) =~ replace(replace(toLower(a), '.', '[.]'), '*', '.*')
            )
        ] AS granted
    WITH sub, ra, rd, perm, principal,
        [
            p IN granted
            WHERE NOT ANY(na IN role_not_actions WHERE
                toLower(p) =~ replace(replace(toLower(na), '.', '[.]'), '*', '.*')
            )
        ] AS matched
    WHERE size(matched) > 0
    // Aggregate across multiple AzurePermissions blocks on the same role definition
    // (and across multiple role assignments of the same role) so we emit one row per
    // (principal, role definition).
    UNWIND matched AS action
    WITH sub, principal, rd, action, ra
    WITH sub, principal, rd,
         collect(DISTINCT action) AS actions,
         collect(DISTINCT ra.scope) AS resources
    RETURN
        sub.id AS account_id,
        sub.id AS account,
        coalesce(principal.user_principal_name,
                 principal.display_name,
                 principal.id) AS principal_name,
        principal.id AS principal_identifier,
        [label IN labels(principal)
            WHERE label IN ['EntraUser', 'EntraGroup', 'EntraServicePrincipal']][0] AS principal_type,
        rd.id AS policy_id,
        rd.role_name AS policy_name,
        actions,
        resources
    ORDER BY account, principal_name, policy_name
    """,
    cypher_visual_query="""
    MATCH p1=(sub:AzureSubscription)-[:RESOURCE]->(ra:AzureRoleAssignment)
    MATCH p2=(ra)-[:ROLE_ASSIGNED]->(rd:AzureRoleDefinition)-[:HAS_PERMISSIONS]->(perm:AzurePermissions)
    MATCH p3=(principal:EntraPrincipal)-[:HAS_ROLE_ASSIGNMENT]->(ra)
    // Mirror the finding: at least one searched pattern is granted by
    // actions and is NOT shadowed by not_actions (Contributor-style
    // not_actions like `Microsoft.Authorization/*/Write` correctly drop
    // the matching patterns from the visual too).
    WHERE ANY(p IN [
            'Microsoft.Authorization/roleAssignments/write',
            'Microsoft.Authorization/roleAssignments/delete',
            'Microsoft.Authorization/roleDefinitions/write',
            'Microsoft.Authorization/roleDefinitions/delete',
            'Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action'
        ]
        WHERE ANY(a IN coalesce(perm.actions, []) WHERE
                  toLower(p) =~ replace(replace(toLower(a), '.', '[.]'), '*', '.*'))
          AND NOT ANY(na IN coalesce(perm.not_actions, []) WHERE
                  toLower(p) =~ replace(replace(toLower(na), '.', '[.]'), '*', '.*'))
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ra:AzureRoleAssignment)
    RETURN COUNT(ra) AS count
    """,
    asset_label="EntraPrincipal",
    asset_id_field="principal_identifier",
    identity_fields=("account_id", "principal_identifier", "policy_id"),
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


# Okta
# Standard admin roles that can create or change users and group membership, or
# reset users' credentials. Custom roles are not evaluated: their permissions are
# not synced.
_OKTA_IDENTITY_ADMIN_ROLE_TYPES = (
    "['SUPER_ADMIN', 'ORG_ADMIN', 'USER_ADMIN', 'GROUP_MEMBERSHIP_ADMIN', "
    "'HELP_DESK_ADMIN']"
)
# Okta API scopes that let a service app write users, groups, or role
# assignments. A service app can act only within both its role and its scopes.
_OKTA_IDENTITY_MANAGE_SCOPES = (
    "['okta.users.manage', 'okta.groups.manage', 'okta.roles.manage']"
)
# Lifecycle states in which an Okta user can still sign in.
_OKTA_ENABLED_USER_STATUSES = "['ACTIVE', 'PASSWORD_EXPIRED', 'LOCKED_OUT', 'RECOVERY']"

_OKTA_USER_IDENTITY_ADMINS = f"""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(principal:OktaUser)
    WHERE o.admin_roles_synced = true
      AND principal.status IN {_OKTA_ENABLED_USER_STATUSES}
    MATCH (principal)-[:HAS_ROLE]->(role:OktaUserRole)
    WHERE role.role_type IN {_OKTA_IDENTITY_ADMIN_ROLE_TYPES}
      AND coalesce(role.status, 'ACTIVE') = 'ACTIVE'
"""

_okta_user_identity_admin_roles = Fact(
    id="okta_user_identity_admin_roles",
    name="Okta Users with Identity Administration Roles",
    description=(
        "Enabled Okta users directly assigned a standard admin role that can "
        "create or change users and group membership, or reset users' "
        "credentials: Super, Org, Group, Group Membership, or Help Desk "
        "Administrator. Only evaluates orgs whose admin roles were synced."
    ),
    cypher_query=f"""
    {_OKTA_USER_IDENTITY_ADMINS}
    RETURN
        o.id AS account_id,
        o.id AS account,
        coalesce(principal.login, principal.email, principal.id) AS principal_name,
        principal.id AS principal_identifier,
        'OktaUser' AS principal_type,
        role.id AS policy_id,
        role.label AS policy_name,
        [role.role_type] AS actions,
        [o.id] AS resources
    ORDER BY account, principal_name, policy_name
    """,
    cypher_visual_query=f"""
    {_OKTA_USER_IDENTITY_ADMINS}
    MATCH p=(o)-[:RESOURCE]->(principal)-[:HAS_ROLE]->(role)
    RETURN p
    """,
    cypher_count_query="""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(principal:OktaUser)
    WHERE o.admin_roles_synced = true
    RETURN COUNT(principal) AS count
    """,
    asset_label="OktaUser",
    asset_id_field="principal_identifier",
    identity_fields=("account_id", "principal_identifier", "policy_id"),
    module=Module.OKTA,
    maturity=Maturity.EXPERIMENTAL,
)


_OKTA_GROUP_IDENTITY_ADMINS = f"""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(principal:OktaGroup)
    WHERE o.admin_roles_synced = true
    MATCH (principal)-[:HAS_ROLE]->(role:OktaGroupRole)
    WHERE role.role_type IN {_OKTA_IDENTITY_ADMIN_ROLE_TYPES}
      AND coalesce(role.status, 'ACTIVE') = 'ACTIVE'
"""

_okta_group_identity_admin_roles = Fact(
    id="okta_group_identity_admin_roles",
    name="Okta Groups with Identity Administration Roles",
    description=(
        "Okta groups assigned a standard admin role that can create or change "
        "users and group membership, or reset users' credentials, which every "
        "member of the group holds. Only evaluates orgs whose admin roles were "
        "synced."
    ),
    cypher_query=f"""
    {_OKTA_GROUP_IDENTITY_ADMINS}
    RETURN
        o.id AS account_id,
        o.id AS account,
        coalesce(principal.name, principal.id) AS principal_name,
        principal.id AS principal_identifier,
        'OktaGroup' AS principal_type,
        role.id AS policy_id,
        role.label AS policy_name,
        [role.role_type] AS actions,
        [o.id] AS resources
    ORDER BY account, principal_name, policy_name
    """,
    cypher_visual_query=f"""
    {_OKTA_GROUP_IDENTITY_ADMINS}
    MATCH p=(o)-[:RESOURCE]->(principal)-[:HAS_ROLE]->(role)
    RETURN p
    """,
    cypher_count_query="""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(principal:OktaGroup)
    WHERE o.admin_roles_synced = true
    RETURN COUNT(principal) AS count
    """,
    asset_label="OktaGroup",
    asset_id_field="principal_identifier",
    identity_fields=("account_id", "principal_identifier", "policy_id"),
    module=Module.OKTA,
    maturity=Maturity.EXPERIMENTAL,
)


_OKTA_APP_IDENTITY_ADMINS = f"""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(principal:OktaApplication)
    WHERE o.application_roles_synced = true
      AND o.app_grants_synced = true
      AND principal.status = 'ACTIVE'
    MATCH (principal)-[:HAS_ROLE]->(role:OktaApplicationRole)
    WHERE role.role_type IN {_OKTA_IDENTITY_ADMIN_ROLE_TYPES}
      AND role.status = 'ACTIVE'
    WITH o, principal, role,
        [scope IN coalesce(principal.granted_scopes, [])
            WHERE scope IN {_OKTA_IDENTITY_MANAGE_SCOPES}] AS actions
    WHERE size(actions) > 0
"""

_okta_application_identity_admin_roles = Fact(
    id="okta_application_identity_admin_roles",
    name="Okta Service Apps with Identity Administration Access",
    description=(
        "Active Okta OAuth service apps assigned a standard admin role that can "
        "administer identities and granted `okta.users.manage`, "
        "`okta.groups.manage`, or `okta.roles.manage`, so the app can change "
        "identities with no person or MFA in the loop. Only evaluates orgs "
        "whose app admin roles and scope grants were synced."
    ),
    cypher_query=f"""
    {_OKTA_APP_IDENTITY_ADMINS}
    RETURN
        o.id AS account_id,
        o.id AS account,
        coalesce(principal.label, principal.id) AS principal_name,
        principal.id AS principal_identifier,
        'OktaApplication' AS principal_type,
        role.id AS policy_id,
        role.label AS policy_name,
        actions,
        [o.id] AS resources
    ORDER BY account, principal_name, policy_name
    """,
    cypher_visual_query=f"""
    {_OKTA_APP_IDENTITY_ADMINS}
    MATCH p=(o)-[:RESOURCE]->(principal)-[:HAS_ROLE]->(role)
    RETURN p
    """,
    cypher_count_query="""
    MATCH (o:OktaOrganization)-[:RESOURCE]->(principal:OktaApplication)
    WHERE o.application_roles_synced = true AND o.app_grants_synced = true
    RETURN COUNT(principal) AS count
    """,
    asset_label="OktaApplication",
    asset_id_field="principal_identifier",
    identity_fields=("account_id", "principal_identifier", "policy_id"),
    module=Module.OKTA,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class IdentityAdministrationPrivileges(Finding):
    principal_name: str | None = None
    principal_identifier: str | None = None
    account: str | None = None
    account_id: str | None = None
    principal_type: str | None = None
    policy_id: str | None = None
    policy_name: str | None = None
    actions: list[str] = []
    resources: list[str] = []


identity_administration_privileges = Rule(
    id="identity_administration_privileges",
    name="Identity Administration Privileges",
    description=(
        "Principals can create, attach, update, or otherwise administer identities "
        "(users/roles/groups) and their bindings—classic escalation surface."
    ),
    output_model=IdentityAdministrationPrivileges,
    facts=(
        _aws_account_manipulation_permissions,
        _azure_account_manipulation_permissions,
        _gcp_account_manipulation_permissions,
        _okta_user_identity_admin_roles,
        _okta_group_identity_admin_roles,
        _okta_application_identity_admin_roles,
    ),
    tags=(
        "iam",
        "stride:elevation_of_privilege",
        "stride:spoofing",
        "stride:tampering",
    ),
    version="0.2.0",
    frameworks=(
        iso27001_annex_a("5.18"),
        iso27001_annex_a("8.2"),
        soc2_tsc("CC6.3"),
    ),
)
