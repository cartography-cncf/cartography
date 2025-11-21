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
    module=Module.AWS,
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
    facts=(_aws_policy_manipulation_capabilities,),
    tags=("iam", "privilege_escalation"),
    version="0.1.0",
)
