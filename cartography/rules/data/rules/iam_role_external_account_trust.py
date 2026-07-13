from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

_aws_role_external_account_trust = Fact(
    id="aws-role-external-account-trust",
    name="IAM roles trusting AWS accounts not synced by Cartography",
    description=(
        "AWS IAM roles in a synced account whose trust policy allows assumption "
        "by a principal belonging to an AWS account that Cartography does not "
        "sync. Accounts actually in the sync scope carry `inscope = true`; stub "
        "accounts materialized from trust-policy parsing do not, so anything "
        "without it is treated as external. "
        "Scope note: this covers account-wide trusts (`arn:aws:iam::<acct>:root`), "
        "for which the sync materializes a stub external AWSAccount and root "
        "AWSPrincipal linked by `[:RESOURCE]`. Trusts toward a named principal in "
        "an unsynced account (e.g. `:role/X`, `:user/Y`) are not surfaced because "
        "the sync does not materialize that principal or its owning account."
    ),
    cypher_query="""
    MATCH (a:AWSAccount {inscope: true})-[:RESOURCE]->(role:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(p:AWSPrincipal)
    MATCH (ext:AWSAccount)-[:RESOURCE]->(p)
    WHERE coalesce(ext.inscope, false) <> true
    RETURN
        role.arn AS role_arn,
        role.name AS role_name,
        a.id AS account_id,
        ext.id AS external_account_id,
        p.arn AS trusted_principal_arn
    ORDER BY account_id, role_arn, external_account_id
    """,
    cypher_visual_query="""
    MATCH p1 = (a:AWSAccount {inscope: true})-[:RESOURCE]->(role:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(p:AWSPrincipal)
    MATCH p2 = (ext:AWSAccount)-[:RESOURCE]->(p)
    WHERE coalesce(ext.inscope, false) <> true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (:AWSAccount {inscope: true})-[:RESOURCE]->(role:AWSRole)
    RETURN COUNT(role) AS count
    """,
    asset_id_field="role_arn",
    identity_fields=("role_arn", "trusted_principal_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class IamRoleExternalAccountTrust(Finding):
    role_name: str | None = None
    role_arn: str | None = None
    account_id: str | None = None
    external_account_id: str | None = None
    trusted_principal_arn: str | None = None


iam_role_external_account_trust = Rule(
    id="iam_role_external_account_trust",
    name="IAM Role External Account Trust",
    description=(
        "Detects IAM roles in synced accounts that trust principals from AWS "
        "accounts outside the sync perimeter. Such external trusts are a silent "
        "lateral-movement and persistence vector, often left over from one-off "
        "integrations or audits."
    ),
    output_model=IamRoleExternalAccountTrust,
    facts=(_aws_role_external_account_trust,),
    tags=(
        "iam",
        "attack_surface",
        "aws",
        "stride:elevation_of_privilege",
        "stride:spoofing",
    ),
    version="0.1.0",
)
