from datetime import datetime
from typing import Annotated

from pydantic import BeforeValidator

from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference
from cartography.util import to_datetime

Neo4jDateTime = Annotated[datetime | None, BeforeValidator(to_datetime)]

# Admin is granted either by a policy on the user itself or by a policy on a
# group the user belongs to, so `holder` is the user (zero hops) or its group.
_aws_admin_user_access_key = Fact(
    id="aws_admin_user_access_key",
    name="AWS IAM users with full administrative privileges holding active access keys",
    description=(
        "Detects active IAM access keys owned by users that hold full '*:*' "
        "administrative privileges, either through a policy attached to the user "
        "or through a group the user belongs to. A long-lived admin key copied to "
        "a laptop, CI system, or remote host gives anyone who reads it full "
        "control of the account, with no MFA or session expiry in the way."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AWSAccountAccessKey)
    WHERE key.status = 'Active'
    MATCH (user)-[:MEMBER_AWS_GROUP*0..1]->(holder:AWSPrincipal)-[:POLICY]->(policy:AWSPolicy)
    WHERE EXISTS {
        MATCH (policy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
        WHERE stmt.effect = 'Allow'
          AND any(action IN stmt.action WHERE action = '*' OR action = '*:*')
          AND any(resource IN stmt.resource WHERE resource = '*')
    }
    WITH a, user, key,
         collect(DISTINCT policy.name) AS admin_policies,
         collect(DISTINCT CASE WHEN holder:AWSGroup THEN holder.name END) AS admin_groups
    RETURN
        key.accesskeyid AS access_key_id,
        user.name AS user_name,
        user.arn AS user_arn,
        key.createdate_dt AS key_create_date,
        key.lastuseddate_dt AS last_used_date,
        admin_policies,
        admin_groups,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(user:AWSUser)-[:AWS_ACCESS_KEY]->(key:AWSAccountAccessKey)
    WHERE key.status = 'Active'
    MATCH p2=(user)-[:MEMBER_AWS_GROUP*0..1]->(holder:AWSPrincipal)-[:POLICY]->(policy:AWSPolicy)-[:STATEMENT]->(stmt:AWSPolicyStatement)
    WHERE stmt.effect = 'Allow'
      AND any(action IN stmt.action WHERE action = '*' OR action = '*:*')
      AND any(resource IN stmt.resource WHERE resource = '*')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (:AWSUser)-[:AWS_ACCESS_KEY]->(key:AWSAccountAccessKey)
    WHERE key.status = 'Active'
    RETURN COUNT(DISTINCT key) AS count
    """,
    asset_label="AWSAccountAccessKey",
    asset_id_field="access_key_id",
    identity_fields=("access_key_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


class AdminUserAccessKeyOutput(Finding):
    access_key_id: str | None = None
    user_name: str | None = None
    user_arn: str | None = None
    key_create_date: Neo4jDateTime = None
    last_used_date: Neo4jDateTime = None
    admin_policies: list[str] | None = None
    admin_groups: list[str] | None = None
    account_id: str | None = None
    account: str | None = None


aws_admin_users_with_access_keys = Rule(
    id="aws_admin_users_with_access_keys",
    name="Administrator IAM Users With Access Keys",
    description=(
        "IAM users with full administrative privileges should not hold long-lived "
        "access keys. Give people short-lived credentials through IAM Identity "
        "Center, and give workloads IAM roles, so that a leaked credentials file "
        "cannot be replayed with admin rights."
    ),
    output_model=AdminUserAccessKeyOutput,
    facts=(_aws_admin_user_access_key,),
    tags=(
        "iam",
        "credentials",
        "stride:spoofing",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
    references=[
        RuleReference(
            text="AWS IAM Best Practices: Require human users to use temporary credentials",
            url="https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-users-federation-idp",
        ),
    ],
    frameworks=(
        iso27001_annex_a("5.17"),
        iso27001_annex_a("8.2"),
        soc2_tsc("CC6.1"),
    ),
)
