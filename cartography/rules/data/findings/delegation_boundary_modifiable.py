from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import FindingOutput
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

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
@@ -44,26 +45,27 @@
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
        MATCH p1 = (principal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        MATCH (principal)-[:POLICY]->(:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE NOT principal.name STARTS WITH 'AWSServiceRole'
        AND principal.name <> 'OrganizationAccountAccessRole'
        AND stmt.effect = 'Allow'
        RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Finding
class DelegationBoundaryModifiable(FindingOutput):
    principal_name: str | None = None
    principal_identifier: str | None = None
    principal_type: str | None = None
    account: str | None = None
    account_id: str | None = None
    policy_name: str | None = None
    actions: list[str] = []
    resources: list[str] = []


delegation_boundary_modifiable = Finding(
    id="delegation_boundary_modifiable",
    name="Delegation Boundary Modifiable",
    description=(
        "Principals can edit role trust/assume policies or create roles with arbitrary trust—"
        "allowing cross-account or lateral impersonation paths."
    ),
    output_model=DelegationBoundaryModifiable,
    facts=(_aws_trust_relationship_manipulation,),
    tags=("iam", "privilege_escalation"),
    version="0.1.0",
)
