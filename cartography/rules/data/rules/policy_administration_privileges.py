from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# AWS
_aws_policy_manipulation_capabilities = Fact(
    id="aws_policy_manipulation_capabilities",
    name="AWS IAM Principals with Policy Administration Permissions",
    description=(
        "Finds AWS IAM principals with Allow permissions for policy administration actions (iam:CreatePolicy, "
        "iam:CreatePolicyVersion, iam:AttachUserPolicy, iam:AttachRolePolicy, iam:AttachGroupPolicy, "
        "iam:PutUserPolicy, iam:PutRolePolicy, iam:PutGroupPolicy, or wildcards) that are not explicitly denied. "
        "Returns action-resource pairs to show which specific permissions apply to which resources. Excludes AWS "
        "service-linked roles and common automation roles."
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
    name="Principals with Policy Administration Privileges",
    description=(
        "Detects principals (users, roles, service accounts) with permissions to create, modify, attach, or "
        "detach authorization policies. Policy administration privileges represent a critical privilege escalation "
        "vector and indirect path to administrative access. Attackers or malicious insiders with these permissions "
        "can create new policies with elevated permissions and attach them to their own principals, modify existing "
        "policies to grant additional capabilities, attach existing administrator policies to compromised identities, "
        "create backdoor policies that grant cross-account access, and bypass intended least-privilege access controls. "
        "Unlike direct identity administration (which modifies users/roles), policy administration achieves privilege "
        "escalation by changing the permissions available to existing principals. Organizations should severely limit "
        "policy administration permissions to dedicated security/platform teams, require multi-person approval for "
        "policy changes, monitor all policy modification API calls for anomalies, and regularly audit which principals "
        "have policy administration capabilities."
    ),
    output_model=PolicyAdministrationPrivileges,
    facts=(_aws_policy_manipulation_capabilities,),
    tags=("iam", "privilege_escalation"),
    version="0.2.0",
    references=[
        RuleReference(
            text="AWS - IAM Best Practices",
            url="https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html",
        ),
        RuleReference(
            text="Azure - IAM Best Practices",
            url="https://learn.microsoft.com/en-us/azure/active-directory/identity-protection/identity-protection-best-practices",
        ),
        RuleReference(
            text="Google Cloud - IAM Best Practices",
            url="https://cloud.google.com/iam/docs/iam-best-practices",
        ),
    ],
)
