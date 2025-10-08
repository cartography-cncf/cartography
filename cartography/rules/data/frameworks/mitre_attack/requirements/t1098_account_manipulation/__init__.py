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
        MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND principal.name <> 'OrganizationAccountAccessRole'
        AND stmt.effect = 'Allow'
        WITH a, principal, stmt,
            // Return labels that are not the general "AWSPrincipal" label
            [label IN labels(principal) WHERE label <> 'AWSPrincipal'][0] AS principal_type,
            // Define the list of IAM actions to match on
            [p IN ['iam:Create','iam:Attach','iam:Put','iam:Update','iam:Add'] |
                p] AS patterns
        WITH a, principal, principal_type, stmt,
            // Filter on the desired IAM actions
            [action IN stmt.action
                WHERE ANY(prefix IN patterns WHERE action STARTS WITH prefix)
                OR action = 'iam:*'
                OR action = '*'
            ] AS matched_actions
        // Return only statement actions that we matched on
        WHERE size(matched_actions) > 0
        UNWIND matched_actions AS action
        RETURN DISTINCT a.name AS account,
            principal.name AS principal_name,
            principal.arn AS principal_arn,
            principal_type,
            collect(action) as action,
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
        MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        OPTIONAL MATCH (groupmember:AWSUser)
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND principal.name <> 'OrganizationAccountAccessRole'
        AND stmt.effect = 'Allow'
        WITH a, principal, stmt,
            [label IN labels(principal) WHERE label <> 'AWSPrincipal'][0] AS principal_type,
            ['iam:UpdateAssumeRolePolicy','iam:CreateRole'] AS patterns
        WITH a, principal, principal_type, stmt,
            [action IN stmt.action
                WHERE ANY(p IN patterns WHERE action = p)
                OR action = 'iam:*' OR action = '*'
            ] AS matched_actions
        WHERE size(matched_actions) > 0
        UNWIND matched_actions AS action
        RETURN DISTINCT a.name AS account,
            principal.name AS principal_name,
            principal.arn AS principal_arn,
            principal_type,
            collect(distinct action) as action,
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
        MATCH (role)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE stmt.effect = 'Allow'
        WITH a, ec2, role,
            // Define the list of IAM actions to match on
            ['iam:Create', 'iam:Attach', 'iam:Put', 'iam:Update'] AS patterns,
            // Filter on the desired IAM actions
            [action IN stmt.action
                WHERE ANY(p IN ['iam:Create','iam:Attach','iam:Put','iam:Update', 'iam:Add'] WHERE action STARTS WITH p)
                OR action = 'iam:*'
                OR action = '*'
            ] AS actions
        // For the instances that are internet open, include the SG and rules
        OPTIONAL MATCH (ec2{exposed_internet:True})-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(ip:IpPermissionInbound)
        // Return only statement actions that we matched on
        WHERE size(actions) > 0
        UNWIND actions AS flat_action
        WITH a, ec2, role, sg, ip,
            collect(DISTINCT flat_action) AS actions
        RETURN DISTINCT a.name AS account,
            a.id as account_id,
            ec2.instanceid AS instance_id,
            ec2.exposed_internet AS internet_accessible,
            ec2.publicipaddress as public_ip_address,
            role.name AS role_name,
            collect(actions) as action,
            ip.fromport as from_port,
            ip.toport as to_port
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
        // Find Lambda functions with account manipulation capabilities
        MATCH (a:AWSAccount)-[:RESOURCE]->(lambda:AWSLambda)
        MATCH (lambda)-[:STS_ASSUMEROLE_ALLOW]->(role:AWSRole)
        MATCH (role)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE stmt.effect = 'Allow'
        WITH a, lambda, role, stmt,
            // Define the list of IAM actions to match on
            ['iam:Create', 'iam:Attach', 'iam:Put', 'iam:Update'] AS patterns,
            // Filter on the desired IAM actions
            [action IN stmt.action
                WHERE ANY(p IN ['iam:Create', 'iam:Attach', 'iam:Put', 'iam:Update', 'iam:Add'] WHERE action STARTS WITH p)
                OR action = 'iam:*'
                OR action = '*'
            ] AS actions
        // Return only statement actions that we matched on
        WHERE size(actions) > 0
        UNWIND actions AS flat_action
        WITH a, lambda, role, stmt,
            collect(DISTINCT flat_action) AS actions
        RETURN DISTINCT a.name AS account,
            a.id as account_id,
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
        MATCH (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND NOT principal.name CONTAINS 'QuickSetup'
        AND principal.name <> 'OrganizationAccountAccessRole'
        AND stmt.effect = 'Allow'

        WITH a, principal, stmt,
            // Return labels that are not the general "AWSPrincipal" label
            [label IN labels(principal) WHERE label <> 'AWSPrincipal'][0] AS principal_type,
            // Define the list of IAM actions to match on
            [p IN
            ['iam:CreatePolicy', 'iam:CreatePolicyVersion', 'iam:AttachUserPolicy', 'iam:AttachRolePolicy', 'iam:AttachGroupPolicy',
            'iam:AttachRolePolicy', 'iam:AttachGroupPolicy', 'iam:DetachUserPolicy', 'iam:DetachRolePolicy', 'iam:DetachGroupPolicy',
            'iam:PutUserPolicy', 'iam:PutRolePolicy', 'iam:PutGroupPolicy'] |
                p] AS patterns

        // Return only statement actions that we matched on
        WITH a, principal, principal_type, stmt,
            [action IN stmt.action
                WHERE ANY(p IN patterns WHERE action = p)
                OR action = 'iam:*' OR action = '*'
            ] AS matched_actions
        WHERE size(matched_actions) > 0
        UNWIND matched_actions AS action
        RETURN DISTINCT a.name AS account,
            principal.name AS principal_name,
            principal.arn AS principal_arn,
            principal_type,
            collect(action) as action,
            stmt.resource AS resource
        ORDER BY account, principal_name
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
