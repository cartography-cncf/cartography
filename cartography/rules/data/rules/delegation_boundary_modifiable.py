from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS
_aws_trust_relationship_manipulation = Fact(
    id="aws_trust_relationship_manipulation",
    name="Roles with Cross-Account Trust Relationship Modification Capabilities",
    description=(
        "AWS IAM principals with permissions to modify role trust policies "
        "(specifically AssumeRolePolicyDocuments)."
    ),
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        MATCH (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement {effect:"Allow"})
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND principal.name <> 'OrganizationAccountAccessRole'
        WITH a, principal, policy, stmt,
            [label IN labels(principal) WHERE label <> 'AWSPrincipal'][0] AS principal_type,
            ['iam:UpdateAssumeRolePolicy', 'iam:CreateRole'] AS patterns
        // Filter for matching Allow actions
        WITH a, principal, principal_type, stmt, policy,
            [action IN stmt.action
                WHERE ANY(p IN patterns WHERE action = p)
                OR action = 'iam:*'
                OR action = '*'
            ] AS matched_allow_actions
        WHERE size(matched_allow_actions) > 0
        // Look for any explicit Deny statement on same principal that matches those actions
        OPTIONAL MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(deny_stmt:AWSPolicyStatement {effect:"Deny"})
        WHERE ANY(action IN deny_stmt.action
                WHERE action IN matched_allow_actions
                    OR action = 'iam:*'
                    OR action = '*')
        // Exclude principals with an explicit Deny that overlaps
        WITH a, principal, principal_type, policy, stmt, matched_allow_actions, deny_stmt
        WHERE deny_stmt IS NULL
        UNWIND matched_allow_actions AS action
        RETURN DISTINCT
            a.name AS account,
            a.id AS account_id,
            principal.name AS principal_name,
            principal.arn AS principal_identifier,
            policy.name AS policy_name,
            principal_type,
            collect(DISTINCT action) AS actions,
            stmt.resource AS resources
        ORDER BY account, principal_name
    """,
    cypher_visual_query="""
        MATCH p = (a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        MATCH p1 = (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement {effect:"Allow"})
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND principal.name <> 'OrganizationAccountAccessRole'
        WITH a, principal, policy, stmt,
            ['iam:UpdateAssumeRolePolicy', 'iam:CreateRole'] AS patterns
        WITH a, principal, policy, stmt,
            [action IN stmt.action
                WHERE ANY(p IN patterns WHERE action = p)
                OR action = 'iam:*'
                OR action = '*'
            ] AS matched_allow_actions
        WHERE size(matched_allow_actions) > 0
        OPTIONAL MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(deny_stmt:AWSPolicyStatement {effect:"Deny"})
        WHERE ANY(action IN deny_stmt.action
                WHERE action IN matched_allow_actions
                    OR action = 'iam:*'
                    OR action = '*')
        WITH a, principal, policy, stmt, deny_stmt
        WHERE deny_stmt IS NULL
        RETURN *
    """,
    cypher_count_query="""
    MATCH (principal:AWSPrincipal)
    RETURN COUNT(principal) AS count
    """,
    asset_id_field="principal_identifier",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# GCP
_gcp_trust_relationship_manipulation = Fact(
    id="gcp_trust_relationship_manipulation",
    name="GCP Principals with Service Account Impersonation Permissions",
    description=(
        "GCP principals bound to a role granting `iam.serviceAccounts.actAs` "
        "(impersonate any service account in the project), "
        "`iam.serviceAccounts.implicitDelegation` (chain SA tokens), or "
        "`iam.serviceAccountKeys.create` (mint long-lived SA keys). All "
        "three open lateral identity-takeover paths analogous to AWS "
        "AssumeRolePolicy modification."
    ),
    cypher_query="""
    MATCH (binding:GCPPolicyBinding)-[:APPLIES_TO]->(scope)
    WHERE any(label IN labels(scope)
              WHERE label IN ['GCPProject', 'GCPFolder', 'GCPOrganization'])
    MATCH (principal:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(binding)
    MATCH (binding)-[:GRANTS_ROLE]->(role:GCPRole)
    WITH scope, principal, role,
        [
            'iam.serviceAccounts.actAs',
            'iam.serviceAccounts.implicitDelegation',
            'iam.serviceAccounts.getAccessToken',
            'iam.serviceAccounts.signBlob',
            'iam.serviceAccounts.signJwt',
            'iam.serviceAccountKeys.create'
        ] AS patterns
    WITH scope, principal, role, patterns,
         [perm IN coalesce(role.permissions, [])
            WHERE perm IN patterns OR perm = 'iam.*' OR perm = '*'] AS matched
    WHERE size(matched) > 0
    RETURN DISTINCT
        scope.id AS account,
        scope.id AS account_id,
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
            'iam.serviceAccounts.actAs',
            'iam.serviceAccounts.implicitDelegation',
            'iam.serviceAccounts.getAccessToken',
            'iam.serviceAccounts.signBlob',
            'iam.serviceAccounts.signJwt',
            'iam.serviceAccountKeys.create'
        ]
        OR perm = 'iam.*' OR perm = '*'
    )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (principal:GCPPrincipal)
    RETURN COUNT(principal) AS count
    """,
    asset_id_field="principal_identifier",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


# Azure
_azure_trust_relationship_manipulation = Fact(
    id="azure_trust_relationship_manipulation",
    name="Azure Principals with Managed Identity Assignment Permissions",
    description=(
        "Entra principals holding a role assignment whose role definition "
        "grants `Microsoft.ManagedIdentity/userAssignedIdentities/.../"
        "assign/action` (attach a UAMI to a workload, the closest analog "
        "to AWS UpdateAssumeRolePolicy) or "
        "`Microsoft.Authorization/roleAssignments/write` (grant arbitrary "
        "role assignments to other principals)."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(ra:AzureRoleAssignment)
    MATCH (ra)-[:ROLE_ASSIGNED]->(rd:AzureRoleDefinition)-[:HAS_PERMISSIONS]->(perm:AzurePermissions)
    MATCH (principal)-[:HAS_ROLE_ASSIGNMENT]->(ra)
    WHERE any(label IN labels(principal)
              WHERE label IN ['EntraUser', 'EntraGroup', 'EntraServicePrincipal'])
    // Treat each action / not_action as a case-insensitive glob: `.` is
    // escaped to the regex char class `[.]`, `*` becomes `.*`. A `*`
    // anywhere now correctly matches; Contributor (actions=['*'],
    // not_actions including `Microsoft.Authorization/*/Write`) is
    // shadowed for the role-assignment write pattern.
    WITH sub, ra, rd, perm, principal,
         coalesce(perm.actions, []) AS role_actions,
         coalesce(perm.not_actions, []) AS role_not_actions,
        [
            'Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action',
            'Microsoft.Authorization/roleAssignments/write'
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
    RETURN DISTINCT
        sub.id AS account,
        sub.id AS account_id,
        coalesce(principal.user_principal_name,
                 principal.display_name,
                 principal.id) AS principal_name,
        principal.id AS principal_identifier,
        [label IN labels(principal)
            WHERE label IN ['EntraUser', 'EntraGroup', 'EntraServicePrincipal']][0] AS principal_type,
        rd.role_name AS policy_name,
        matched AS actions,
        [ra.scope] AS resources
    ORDER BY account, principal_name
    """,
    cypher_visual_query="""
    MATCH p1=(sub:AzureSubscription)-[:RESOURCE]->(ra:AzureRoleAssignment)
    MATCH p2=(ra)-[:ROLE_ASSIGNED]->(rd:AzureRoleDefinition)-[:HAS_PERMISSIONS]->(perm:AzurePermissions)
    MATCH p3=(principal)-[:HAS_ROLE_ASSIGNMENT]->(ra)
    WHERE any(label IN labels(principal)
              WHERE label IN ['EntraUser', 'EntraGroup', 'EntraServicePrincipal'])
      // Mirror the finding query: at least one searched pattern is granted
      // by actions AND not shadowed by not_actions.
      AND ANY(p IN [
            'Microsoft.ManagedIdentity/userAssignedIdentities/*/assign/action',
            'Microsoft.Authorization/roleAssignments/write'
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
    asset_id_field="principal_identifier",
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class DelegationBoundaryModifiable(Finding):
    principal_name: str | None = None
    principal_identifier: str | None = None
    principal_type: str | None = None
    account: str | None = None
    account_id: str | None = None
    policy_name: str | None = None
    actions: list[str] = []
    resources: list[str] = []


delegation_boundary_modifiable = Rule(
    id="delegation_boundary_modifiable",
    name="Delegation Boundary Modifiable",
    description=(
        "Principals can edit role trust/assume policies or create roles with arbitrary trust—"
        "allowing cross-account or lateral impersonation paths."
    ),
    output_model=DelegationBoundaryModifiable,
    facts=(
        _aws_trust_relationship_manipulation,
        _azure_trust_relationship_manipulation,
        _gcp_trust_relationship_manipulation,
    ),
    tags=(
        "iam",
        "stride:elevation_of_privilege",
        "stride:spoofing",
        "stride:tampering",
    ),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("5.18"),
        iso27001_annex_a("8.2"),
    ),
)
