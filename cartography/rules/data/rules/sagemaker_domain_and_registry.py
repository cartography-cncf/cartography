"""
AWS SageMaker domain authentication and model registry approval

Domain authentication mode and whether a model package group has any approved
package. ``auth_mode`` is populated by ``transform_domains`` and
``model_approval_status`` by ``transform_model_packages``.

No collector change is required: every property read here is already
populated by the AWS SageMaker intel module. All rules are EXPERIMENTAL
until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsSagemakerDomainSsoAuthOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    domain_id: str | None = None
    domain_name: str | None = None
    domain_arn: str | None = None
    auth_mode: str | None = None


_aws_sagemaker_domain_sso_auth_fact = Fact(
    id="aws_sagemaker_domain_sso_auth_fact",
    name="SageMaker domain IAM auth",
    description="Domains using IAM authentication mode.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSSageMakerDomain)
        WHERE d.auth_mode = 'IAM'
        RETURN a.id AS account_id, a.name AS account, d.domain_id AS domain_id,
               d.domain_name AS domain_name, d.arn AS domain_arn, d.auth_mode AS auth_mode

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(d:AWSSageMakerDomain)
        WHERE d.auth_mode = 'IAM'
        RETURN a.id AS account_id, a.name AS account, d.domain_id AS domain_id,
               d.domain_name AS domain_name, d.arn AS domain_arn, d.auth_mode AS auth_mode

    """,
    cypher_count_query="""
    MATCH (d:AWSSageMakerDomain) RETURN COUNT(d) AS count
    """,
    asset_label="AWSSageMakerDomain",
    asset_id_field="domain_id",
    identity_fields=("account_id", "account", "domain_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_sagemaker_domain_sso_auth = Rule(
    id="aws_sagemaker_domain_sso_auth",
    name="SageMaker Domain SSO Authentication",
    description="SageMaker domain auth_mode is 'IAM' instead of 'SSO'. PARTIAL: the full check also requires an IAM Identity Center association (SingleSignOnManagedApplicationInstanceId / SingleSignOnApplicationArn); those fields are not synced, so SSO-mode domains lacking an IdC association cannot be flagged.",
    output_model=AwsSagemakerDomainSsoAuthOutput,
    facts=(_aws_sagemaker_domain_sso_auth_fact,),
    tags=("security", "sagemaker", "authentication", "cspm"),
    version="0.1.0",
)


class AwsSagemakerModelRegistryApprovedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_arn: str | None = None
    group_name: str | None = None
    region: str | None = None


_aws_sagemaker_model_registry_approved_fact = Fact(
    id="aws_sagemaker_model_registry_approved_fact",
    name="Model package group without approved package",
    description="Groups with no Approved model package in the same account.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(g:AWSSageMakerModelPackageGroup)
        WHERE NOT EXISTS {
            MATCH (a)-[:RESOURCE]->(p:AWSSageMakerModelPackage)
            WHERE p.model_package_group_name = g.model_package_group_name
              AND p.model_approval_status = 'Approved'
        }
        RETURN a.id AS account_id, a.name AS account, g.arn AS group_arn,
               g.model_package_group_name AS group_name, g.region AS region

    """,
    cypher_visual_query="""

        MATCH p=(a:AWSAccount)-[:RESOURCE]->(g:AWSSageMakerModelPackageGroup)
        WHERE NOT EXISTS {
            MATCH (a)-[:RESOURCE]->(mp:AWSSageMakerModelPackage)
            WHERE mp.model_package_group_name = g.model_package_group_name
              AND mp.model_approval_status = 'Approved'
        }
        RETURN *

    """,
    cypher_count_query="""
    MATCH (g:AWSSageMakerModelPackageGroup) RETURN COUNT(g) AS count
    """,
    asset_label="AWSSageMakerModelPackageGroup",
    asset_id_field="group_arn",
    identity_fields=("account_id", "account", "group_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_sagemaker_model_registry_approved = Rule(
    id="aws_sagemaker_model_registry_approved",
    name="SageMaker Model Registry Approved Package",
    description="SageMaker model package group with no model package whose model_approval_status is 'Approved', i.e. the registry approval workflow is not in use for that group. BEST-EFFORT: evaluated per package group (the spec's asset label was the package, but the predicate's unit is the group); an entirely empty registry (no groups at all) produces no finding rows, empty registries are not flagged. Packages are matched to groups by model_package_group_name within the same account.",
    output_model=AwsSagemakerModelRegistryApprovedOutput,
    facts=(_aws_sagemaker_model_registry_approved_fact,),
    tags=("security", "sagemaker", "gen-ai", "cspm", "best-effort"),
    version="0.1.0",
)
