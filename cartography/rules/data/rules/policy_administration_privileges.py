from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS
_aws_policy_manipulation_capabilities = Fact(
    id="aws_policy_manipulation_capabilities",
    name="Principals with IAM Policy Creation and Modification Capabilities",
    description=(
        "AWS IAM principals that can create, modify, or attach IAM policies to other principals. "
    ),
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        MATCH (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(allow_stmt:AWSPolicyStatement {effect:"Allow"})
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND principal.name <> 'OrganizationAccountAccessRole'
        WITH a, principal, policy, allow_stmt,
            [label IN labels(principal) WHERE label <> 'AWSPrincipal'][0] AS principal_type,
            [
            'iam:CreatePolicy','iam:CreatePolicyVersion',
            'iam:AttachUserPolicy','iam:AttachRolePolicy','iam:AttachGroupPolicy',
            'iam:DetachUserPolicy','iam:DetachRolePolicy','iam:DetachGroupPolicy',
            'iam:PutUserPolicy','iam:PutRolePolicy','iam:PutGroupPolicy'
            ] AS patterns
        // Step 1 - Collect (action, resource) pairs for allowed statements
        UNWIND allow_stmt.action AS allow_action
            WITH a, principal, principal_type, policy, allow_stmt, allow_action, patterns
            WHERE ANY(p IN patterns WHERE allow_action = p)
            OR allow_action = 'iam:*'
            OR allow_action = '*'
        WITH a, principal, principal_type, policy, allow_stmt, allow_action, allow_stmt.resource AS allow_resources
        // Step 2 - Gather all Deny statements for the same principal
        OPTIONAL MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(deny_stmt:AWSPolicyStatement {effect:"Deny"})
        WITH a, principal, principal_type, policy, allow_action, allow_resources,
            REDUCE(acc = [], ds IN collect(deny_stmt.action) | acc + ds) AS all_deny_actions
        // Step 3 - Filter out denied actions (handles *, iam:*, exact, and prefix wildcards)
        WHERE NOT (
            '*' IN all_deny_actions OR
            'iam:*' IN all_deny_actions OR
            allow_action IN all_deny_actions OR
            ANY(d IN all_deny_actions WHERE d ENDS WITH('*') AND allow_action STARTS WITH split(d,'*')[0])
        )
        // Step 4 - Preserve (action, resource) mapping
        UNWIND allow_resources AS resource
        RETURN DISTINCT
            a.name AS account,
            a.id   AS account_id,
            principal.name AS principal_name,
            principal.arn  AS principal_identifier,
            principal_type,
            policy.name    AS policy_name,
            allow_action   AS action,
            resource
        ORDER BY account, principal_name, action, resource
    """,
    cypher_visual_query="""
    MATCH p1=(a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
    MATCH p2=(principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
    WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
    AND NOT principal.name CONTAINS 'QuickSetup'
    AND principal.name <> 'OrganizationAccountAccessRole'
    AND stmt.effect = 'Allow'
    AND ANY(action IN stmt.action WHERE
        action CONTAINS 'iam:CreatePolicy' OR action CONTAINS 'iam:CreatePolicyVersion'
        OR action CONTAINS 'iam:AttachUserPolicy' OR action CONTAINS 'iam:AttachRolePolicy'
        OR action CONTAINS 'iam:AttachGroupPolicy' OR action CONTAINS 'iam:DetachUserPolicy'
        OR action CONTAINS 'iam:DetachRolePolicy' OR action CONTAINS 'iam:DetachGroupPolicy'
        OR action CONTAINS 'iam:PutUserPolicy' OR action CONTAINS 'iam:PutRolePolicy'
        OR action CONTAINS 'iam:PutGroupPolicy' OR action = 'iam:*' OR action = '*'
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
    asset_id_field="principal_identifier",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# GCP
_gcp_policy_manipulation_capabilities = Fact(
    id="gcp_policy_manipulation_capabilities",
    name="GCP Principals with Policy Administration Permissions",
    description=(
        "GCP principals bound to a role that grants `setIamPolicy` on a "
        "project, folder, or organization, or that grants role / "
        "permission management. Indirect privilege escalation surface."
    ),
    cypher_query="""
    MATCH (binding:GCPPolicyBinding)-[:APPLIES_TO]->(scope)
    WHERE any(label IN labels(scope)
              WHERE label IN ['GCPProject', 'GCPFolder', 'GCPOrganization'])
    MATCH (principal:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(binding)
    MATCH (binding)-[:GRANTS_ROLE]->(role:GCPRole)
    WITH scope, principal, role,
        [
            'resourcemanager.projects.setIamPolicy',
            'resourcemanager.folders.setIamPolicy',
            'resourcemanager.organizations.setIamPolicy',
            'iam.roles.create',
            'iam.roles.update',
            'iam.roles.delete'
        ] AS patterns
    WITH scope, principal, role, patterns,
         [perm IN coalesce(role.permissions, [])
            WHERE perm IN patterns OR perm = 'iam.*' OR perm = 'resourcemanager.*' OR perm = '*'] AS matched
    WHERE size(matched) > 0
    UNWIND matched AS action
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
        action,
        scope.id AS resource
    ORDER BY account, principal_name, action
    """,
    cypher_visual_query="""
    MATCH p1=(principal:GCPPrincipal)-[:HAS_ALLOW_POLICY]->(binding:GCPPolicyBinding)-[:APPLIES_TO]->(scope)
    WHERE any(label IN labels(scope)
              WHERE label IN ['GCPProject', 'GCPFolder', 'GCPOrganization'])
    MATCH p2=(binding)-[:GRANTS_ROLE]->(role:GCPRole)
    WHERE ANY(perm IN coalesce(role.permissions, []) WHERE
        perm IN [
            'resourcemanager.projects.setIamPolicy',
            'resourcemanager.folders.setIamPolicy',
            'resourcemanager.organizations.setIamPolicy',
            'iam.roles.create',
            'iam.roles.update',
            'iam.roles.delete'
        ]
        OR perm = 'iam.*' OR perm = 'resourcemanager.*' OR perm = '*'
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
_azure_policy_manipulation_capabilities = Fact(
    id="azure_policy_manipulation_capabilities",
    name="Azure Principals with Policy Administration Permissions",
    description=(
        "Entra principals holding a role assignment whose role definition "
        "grants permissions to manage role definitions or write at the "
        "Microsoft.Authorization scope. Indirect privilege escalation "
        "surface (creating roles, granting them, etc.)."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(ra:AzureRoleAssignment)
    MATCH (ra)-[:ROLE_ASSIGNED]->(rd:AzureRoleDefinition)-[:HAS_PERMISSIONS]->(perm:AzurePermissions)
    MATCH (principal)-[:HAS_ROLE_ASSIGNMENT]->(ra)
    WHERE any(label IN labels(principal)
              WHERE label IN ['EntraUser', 'EntraGroup', 'EntraServicePrincipal'])
    // Treat each action / not_action as a case-insensitive glob: `.` is
    // escaped to the regex char class `[.]`, `*` becomes `.*`. A `*`
    // anywhere now correctly matches; built-in Contributor with
    // not_actions like `Microsoft.Authorization/*/Write` drops the
    // matching patterns instead of letting them flag.
    WITH sub, ra, rd, perm, principal,
         coalesce(perm.actions, []) AS role_actions,
         coalesce(perm.not_actions, []) AS role_not_actions,
        [
            'Microsoft.Authorization/roleDefinitions/write',
            'Microsoft.Authorization/roleDefinitions/delete',
            'Microsoft.Authorization/policyDefinitions/write',
            'Microsoft.Authorization/policyAssignments/write'
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
    UNWIND matched AS action
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
        action,
        ra.scope AS resource
    ORDER BY account, principal_name, action
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
            'Microsoft.Authorization/roleDefinitions/write',
            'Microsoft.Authorization/roleDefinitions/delete',
            'Microsoft.Authorization/policyDefinitions/write',
            'Microsoft.Authorization/policyAssignments/write'
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


# Findings
class PolicyAdministrationPrivileges(Finding):
    principal_name: str | None = None
    principal_identifier: str | None = None
    account: str | None = None
    account_id: str | None = None
    principal_type: str | None = None
    policy_name: str | None = None
    action: str | None = None
    resource: str | None = None


policy_administration_privileges = Rule(
    id="policy_administration_privileges",
    name="Policy Administration Privileges",
    description=(
        "Principals can create, attach/detach, or write IAM policies—often enabling "
        "indirect privilege escalation."
    ),
    output_model=PolicyAdministrationPrivileges,
    facts=(
        _aws_policy_manipulation_capabilities,
        _azure_policy_manipulation_capabilities,
        _gcp_policy_manipulation_capabilities,
    ),
    tags=(
        "iam",
        "stride:elevation_of_privilege",
        "stride:spoofing",
        "stride:tampering",
    ),
    version="0.1.0",
)
