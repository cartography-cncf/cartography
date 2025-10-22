from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Requirement

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
            principal.name AS principal_name,
            principal.arn AS principal_arn,
            principal_type,
            policy.name AS policy_name,
            collect(DISTINCT action) AS action,
            stmt.resource AS resource
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
)

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
            principal.name AS principal_name,
            principal.arn AS principal_arn,
            policy.name AS policy_name,
            principal_type,
            collect(DISTINCT action) AS action,
            stmt.resource AS resource
        ORDER BY account, principal_name
    """,
    cypher_visual_query="""
        MATCH p = (a:AWSAccount)-[:RESOURCE]->(principal:AWSPrincipal)
        MATCH p1 = (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND principal.name <> 'OrganizationAccountAccessRole'
        AND stmt.effect = 'Allow'
        RETURN *
    """,
    module=Module.AWS,
)

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
            a.name AS account,
            a.id AS account_id,
            ec2.instanceid AS instance_id,
            ec2.exposed_internet AS internet_accessible,
            ec2.publicipaddress AS public_ip_address,
            role.name AS role_name,
            actions,
            ip.fromport AS from_port,
            ip.toport AS to_port
        ORDER BY account, instance_id, internet_accessible, from_port
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
            a.name AS account,
            a.id AS account_id,
            lambda.arn AS arn,
            lambda.description AS description,
            lambda.anonymous_access AS internet_accessible,
            role.name AS role_name,
            actions
        ORDER BY account, arn, internet_accessible
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
)

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

        // Step 1 – Collect (action, resource) pairs for allowed statements
        UNWIND allow_stmt.action AS allow_action
            WITH a, principal, principal_type, policy, allow_stmt, allow_action, patterns
            WHERE ANY(p IN patterns WHERE allow_action = p)
            OR allow_action = 'iam:*'
            OR allow_action = '*'
        WITH a, principal, principal_type, policy, allow_stmt, allow_action, allow_stmt.resource AS allow_resources

        // Step 2 – Gather all Deny statements for the same principal
        OPTIONAL MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(deny_stmt:AWSPolicyStatement {effect:"Deny"})
        WITH a, principal, principal_type, policy, allow_action, allow_resources,
            REDUCE(acc = [], ds IN collect(deny_stmt.action) | acc + ds) AS all_deny_actions

        // Step 3 – Filter out denied actions (handles *, iam:*, exact, and prefix wildcards)
        WHERE NOT (
            '*' IN all_deny_actions OR
            'iam:*' IN all_deny_actions OR
            allow_action IN all_deny_actions OR
            ANY(d IN all_deny_actions WHERE d ENDS WITH('*') AND allow_action STARTS WITH split(d,'*')[0])
        )

        // Step 4 – Preserve (action, resource) mapping
        UNWIND allow_resources AS resource
        RETURN DISTINCT
            a.name AS account,
            principal.name AS principal_name,
            principal.arn  AS principal_arn,
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
)


t1098 = Requirement(
    id="t1098",
    name="Account Manipulation",
    description=(
        "Adversaries may manipulate accounts to maintain or elevate access to victim systems. "
        "Activity that subverts security policies. For example in cloud this is "
        "updating IAM policies or adding new global admins."
    ),
    target_assets="Identities that can manipulate other identities",
    facts=(
        # AWS
        _aws_account_manipulation_permissions,
        _aws_trust_relationship_manipulation,
        _aws_service_account_manipulation_via_ec2,
        _aws_service_account_manipulation_via_lambda,
        _aws_policy_manipulation_capabilities,
    ),
    requirement_url="https://attack.mitre.org/techniques/T1098/",
    attributes={
        "tactic": "persistence,privilege_escalation",
        "technique_id": "T1098",
        "services": [
            "iam",
            "sts",
            "ec2",
            "lambda",
        ],
        "providers": ["AWS"],
    },
)
