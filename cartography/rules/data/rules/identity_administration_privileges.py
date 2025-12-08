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
                WHERE ANY(prefix IN patterns WHERE action STARTS WITH prefix)
                OR action = 'iam:*'
                OR action = '*'
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
        UNWIND matched_allow_actions AS action
        RETURN DISTINCT
            a.name AS account,
            a.id AS account_id,
            principal.name AS principal_name,
            principal.arn AS principal_identifier,
            principal_type,
            policy.name AS policy_name,
            collect(DISTINCT action) AS actions,
            stmt.resource AS resources
        ORDER BY account, principal_name
    """,
    cypher_visual_query="""
        MATCH p = (a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        MATCH p1 = (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND NOT principal.name = 'OrganizationAccountAccessRole'
        AND stmt.effect = 'Allow'
        AND ANY(action IN stmt.action WHERE
            action STARTS WITH 'iam:Create'
            OR action STARTS WITH 'iam:Attach'
            OR action STARTS WITH 'iam:Put'
            OR action STARTS WITH 'iam:Update'
            OR action STARTS WITH 'iam:Add'
            OR action = 'iam:*'
            OR action = '*'
        )
        RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class IdentityAdministrationPrivileges(Finding):
    principal_name: str | None = None
    principal_identifier: str | None = None
    account: str | None = None
    account_id: str | None = None
    principal_type: str | None = None
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
    facts=(_aws_account_manipulation_permissions,),
    tags=("iam", "privilege_escalation"),
    version="0.1.0",
)
