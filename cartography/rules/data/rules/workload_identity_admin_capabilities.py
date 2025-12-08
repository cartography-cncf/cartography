from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS
_aws_service_account_manipulation_via_ec2 = Fact(
    id="aws_service_account_manipulation_via_ec2",
    name="Service Resources with Account Manipulation Through Instance Profiles",
    description=(
        "AWS EC2 instances with attached IAM roles that can manipulate other AWS accounts. "
        "Also indicates whether the instance is internet-exposed."
    ),
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
        MATCH (ec2)-[:INSTANCE_PROFILE]->(profile:AWSInstanceProfile)
        MATCH (profile)-[:ASSOCIATED_WITH]->(role:AWSRole)
        MATCH (role)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(allow_stmt:AWSPolicyStatement {effect:"Allow"})
        WITH a, ec2, role, allow_stmt,
            ['iam:Create','iam:Attach','iam:Put','iam:Update','iam:Add'] AS patterns
        // Step 1: Collect allowed actions that match IAM modification patterns
        WITH a, ec2, role, patterns,
            [action IN allow_stmt.action
                WHERE ANY(p IN patterns WHERE action STARTS WITH p)
                OR action = 'iam:*'
                OR action = '*'
            ] AS matched_allow_actions
        WHERE size(matched_allow_actions) > 0
        // Step 2: Collect deny statements for the same role
        OPTIONAL MATCH (role)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(deny_stmt:AWSPolicyStatement {effect:"Deny"})
        WITH a, ec2, role, patterns, matched_allow_actions,
            // Flatten the deny action lists manually
            REDUCE(acc = [], ds IN collect(deny_stmt.action) | acc + ds) AS all_deny_actions
        // Step 3: Compute effective = allows minus denies
        WITH a, ec2, role, matched_allow_actions, all_deny_actions,
            [action IN matched_allow_actions
                WHERE NOT (
                    // Full wildcard Deny *
                    '*' IN all_deny_actions OR
                    // IAM category wildcard Deny iam:*
                    'iam:*' IN all_deny_actions OR
                    // Exact match deny
                    action IN all_deny_actions OR
                    // Prefix wildcards like Deny iam:Update*
                    ANY(d IN all_deny_actions WHERE d ENDS WITH('*') AND action STARTS WITH split(d,'*')[0])
                )
            ] AS effective_actions
        WHERE size(effective_actions) > 0
        // Step 4: Optional internet exposure context
        OPTIONAL MATCH (ec2 {exposed_internet: True})
            -[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
            <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(ip:IpPermissionInbound)
        UNWIND effective_actions AS action
        WITH a, ec2, role, sg, ip, COLLECT(DISTINCT action) AS actions
        RETURN DISTINCT
            ec2.id AS workload_id,
            a.name AS account,
            a.id AS account_id,
            role.name AS role_name,
            actions,
            ec2.exposed_internet AS internet_accessible,
            ec2.publicipaddress AS public_ip_address,
            ip.fromport AS from_port,
            ip.toport AS to_port
        ORDER BY account, workload_id, internet_accessible, from_port
    """,
    cypher_visual_query="""
        MATCH p = (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
        MATCH p1 = (ec2)-[:INSTANCE_PROFILE]->(profile:AWSInstanceProfile)
        MATCH p2 = (profile)-[:ASSOCIATED_WITH]->(role:AWSRole)
        MATCH p3 = (role)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE stmt.effect = 'Allow'
        AND ANY(action IN stmt.action WHERE
            action STARTS WITH 'iam:Create'
            OR action STARTS WITH 'iam:Attach'
            OR action STARTS WITH 'iam:Put'
            OR action STARTS WITH 'iam:Update'
            OR action STARTS WITH 'iam:Add'
            OR action = 'iam:*'
            OR action = '*'
        )
        WITH p, p1, p2, p3, ec2
        // Include the SG and rules for the instances that are internet open
        MATCH p4=(ec2{exposed_internet: true})-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(ip:IpPermissionInbound)
        RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)

_aws_service_account_manipulation_via_lambda = Fact(
    id="aws_service_account_manipulation",
    name="Service Resources with Account Manipulation Through Lambda Roles",
    description=(
        "AWS Lambda functions with IAM roles that can manipulate other AWS accounts."
    ),
    cypher_query="""
        // Find Lambda functions with IAM modification or account manipulation capabilities
        MATCH (a:AWSAccount)-[:RESOURCE]->(lambda:AWSLambda)
        MATCH (lambda)-[:STS_ASSUMEROLE_ALLOW]->(role:AWSRole)
        MATCH (role)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(allow_stmt:AWSPolicyStatement {effect:"Allow"})
        WITH a, lambda, role, allow_stmt,
            ['iam:Create','iam:Attach','iam:Put','iam:Update','iam:Add'] AS patterns
        // Step 1: Gather allowed actions that match IAM modification patterns
        WITH a, lambda, role, patterns,
            [action IN allow_stmt.action
                WHERE ANY(p IN patterns WHERE action STARTS WITH p)
                OR action = 'iam:*'
                OR action = '*'
            ] AS matched_allow_actions
        WHERE size(matched_allow_actions) > 0
        // Step 2: Gather all deny actions from the same role
        OPTIONAL MATCH (role)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(deny_stmt:AWSPolicyStatement {effect:"Deny"})
        WITH a, lambda, role, patterns, matched_allow_actions,
            REDUCE(acc = [], ds IN collect(deny_stmt.action) | acc + ds) AS all_deny_actions
        // Step 3: Subtract Deny actions from Allow actions
        WITH a, lambda, role, matched_allow_actions, all_deny_actions,
            [action IN matched_allow_actions
                WHERE NOT (
                    // Global wildcard deny
                    '*' IN all_deny_actions OR
                    // IAM wildcard deny
                    'iam:*' IN all_deny_actions OR
                    // Exact match deny
                    action IN all_deny_actions OR
                    // Prefix wildcards like Deny iam:Update*
                    ANY(d IN all_deny_actions WHERE d ENDS WITH('*') AND action STARTS WITH split(d,'*')[0])
                )
            ] AS effective_actions
        WHERE size(effective_actions) > 0
        // Step 4: Return only Lambdas with effective IAM modification capabilities
        UNWIND effective_actions AS action
        WITH a, lambda, role, COLLECT(DISTINCT action) AS actions
        RETURN DISTINCT
            lambda.arn AS workload_id,
            lambda.name AS workload_name,
            a.name AS account,
            a.id AS account_id,
            role.name AS role_name,
            actions,
            lambda.anonymous_access AS internet_accessible,
            lambda.description AS description
        ORDER BY account, workload_id, internet_accessible
    """,
    cypher_visual_query="""
        MATCH p = (a:AWSAccount)-[:RESOURCE]->(lambda:AWSLambda)
        MATCH p1 = (lambda)-[:STS_ASSUMEROLE_ALLOW]->(role:AWSRole)
        MATCH p2 = (role)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE stmt.effect = 'Allow'
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
class WorkloadIdentityAdminCapabilities(Finding):
    workload_name: str | None = None
    workload_id: str | None = None
    account: str | None = None
    account_id: str | None = None
    role_name: str | None = None
    actions: list[str] | None = None
    internet_accessible: bool | None = None
    public_ip_address: str | None = None


workload_identity_admin_capabilities = Rule(
    id="workload_identity_admin_capabilities",
    name="Workload Identity-Admin Capabilities",
    description=(
        "A compute workload (VM or function) holds permissions to administer identities/policies. "
        "If internet-exposed, the blast radius is higher."
    ),
    output_model=WorkloadIdentityAdminCapabilities,
    facts=(
        _aws_service_account_manipulation_via_ec2,
        _aws_service_account_manipulation_via_lambda,
    ),
    tags=("iam", "privilege_escalation"),
    version="0.1.0",
)
