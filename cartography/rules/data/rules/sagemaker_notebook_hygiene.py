"""
AWS SageMaker notebook instance configuration hygiene

Storage encryption, direct internet access, root access and VPC placement for
notebook instances. All four read properties that
``transform_notebook_instances`` populates from the DescribeNotebookInstance
response.

No collector change is required: every property read here is already
populated by the AWS SageMaker intel module. All rules are EXPERIMENTAL
until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsSagemakerNotebookKmsEncryptionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    notebook_arn: str | None = None
    notebook_instance_name: str | None = None
    kms_key_id: str | None = None
    subnet_id: str | None = None
    security_groups: str | None = None
    direct_internet_access: str | None = None


_aws_sagemaker_notebook_kms_encryption_fact = Fact(
    id="aws_sagemaker_notebook_kms_encryption_fact",
    name="SageMaker notebook unencrypted",
    description="Notebook instances without a kms_key_id.",
    cypher_query="""

        MATCH (acct:AWSAccount)-[:RESOURCE]->(n:AWSSageMakerNotebookInstance)
        WHERE n.kms_key_id IS NULL OR n.kms_key_id = ''
        RETURN acct.id AS account_id, acct.name AS account, n.arn AS notebook_arn,
               n.notebook_instance_name AS notebook_instance_name, n.kms_key_id AS kms_key_id

    """,
    cypher_visual_query="""

        MATCH (acct:AWSAccount)-[:RESOURCE]->(n:AWSSageMakerNotebookInstance)
        WHERE n.kms_key_id IS NULL OR n.kms_key_id = ''
        RETURN acct.id AS account_id, acct.name AS account, n.arn AS notebook_arn,
               n.notebook_instance_name AS notebook_instance_name, n.kms_key_id AS kms_key_id

    """,
    cypher_count_query="""

        MATCH (n:AWSSageMakerNotebookInstance)
        RETURN count(n) AS total_assets,
               count(CASE WHEN n.kms_key_id IS NULL OR n.kms_key_id = '' THEN 1 END) AS failing,
               count(n) AS count

    """,
    asset_label="AWSSageMakerNotebookInstance",
    asset_id_field="notebook_arn",
    identity_fields=("notebook_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_sagemaker_notebook_kms_encryption = Rule(
    id="aws_sagemaker_notebook_kms_encryption",
    name="SageMaker Notebook KMS Encryption",
    description="SageMaker notebook instance has no kms_key_id set, so its ML storage volume is not KMS-encrypted.",
    output_model=AwsSagemakerNotebookKmsEncryptionOutput,
    facts=(_aws_sagemaker_notebook_kms_encryption_fact,),
    tags=("security", "sagemaker", "encryption", "cspm"),
    version="0.1.0",
)


class AwsSagemakerNotebookNoDirectInternetOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    notebook_arn: str | None = None
    notebook_instance_name: str | None = None
    kms_key_id: str | None = None
    subnet_id: str | None = None
    security_groups: str | None = None
    direct_internet_access: str | None = None


_aws_sagemaker_notebook_no_direct_internet_fact = Fact(
    id="aws_sagemaker_notebook_no_direct_internet_fact",
    name="SageMaker notebook internet",
    description="Notebook instances with direct_internet_access = 'Enabled'.",
    cypher_query="""

        MATCH (acct:AWSAccount)-[:RESOURCE]->(n:AWSSageMakerNotebookInstance)
        WHERE n.direct_internet_access = 'Enabled'
        RETURN acct.id AS account_id, acct.name AS account, n.arn AS notebook_arn,
               n.notebook_instance_name AS notebook_instance_name,
               n.direct_internet_access AS direct_internet_access

    """,
    cypher_visual_query="""

        MATCH (acct:AWSAccount)-[:RESOURCE]->(n:AWSSageMakerNotebookInstance)
        WHERE n.direct_internet_access = 'Enabled'
        RETURN acct.id AS account_id, acct.name AS account, n.arn AS notebook_arn,
               n.notebook_instance_name AS notebook_instance_name,
               n.direct_internet_access AS direct_internet_access

    """,
    cypher_count_query="""

        MATCH (n:AWSSageMakerNotebookInstance)
        RETURN count(n) AS total_assets,
               count(CASE WHEN n.direct_internet_access = 'Enabled' THEN 1 END) AS failing,
               count(n) AS count

    """,
    asset_label="AWSSageMakerNotebookInstance",
    asset_id_field="notebook_arn",
    identity_fields=("notebook_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_sagemaker_notebook_no_direct_internet = Rule(
    id="aws_sagemaker_notebook_no_direct_internet",
    name="SageMaker Notebook Direct Internet Access",
    description="SageMaker notebook instance has direct_internet_access = 'Enabled', giving it direct outbound internet access.",
    output_model=AwsSagemakerNotebookNoDirectInternetOutput,
    facts=(_aws_sagemaker_notebook_no_direct_internet_fact,),
    tags=("security", "sagemaker", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsSagemakerNotebookRootAccessDisabledOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    notebook_arn: str | None = None
    notebook_instance_name: str | None = None
    root_access: str | None = None
    instance_type: str | None = None
    notebook_instance_status: str | None = None


_aws_sagemaker_notebook_root_access_disabled_fact = Fact(
    id="aws_sagemaker_notebook_root_access_disabled_fact",
    name="Notebook root access enabled",
    description="Notebook instances with root_access other than Disabled.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(n:AWSSageMakerNotebookInstance)
        WHERE n.root_access IS NULL OR n.root_access <> 'Disabled'
        RETURN a.id AS account_id, a.name AS account, n.arn AS notebook_arn,
               n.notebook_instance_name AS notebook_instance_name,
               n.root_access AS root_access, n.instance_type AS instance_type,
               n.notebook_instance_status AS notebook_instance_status

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(n:AWSSageMakerNotebookInstance)
        WHERE n.root_access IS NULL OR n.root_access <> 'Disabled'
        RETURN a.id AS account_id, a.name AS account, n.arn AS notebook_arn,
               n.notebook_instance_name AS notebook_instance_name,
               n.root_access AS root_access, n.instance_type AS instance_type,
               n.notebook_instance_status AS notebook_instance_status

    """,
    cypher_count_query="""
    MATCH (n:AWSSageMakerNotebookInstance) RETURN COUNT(n) AS count
    """,
    asset_label="AWSSageMakerNotebookInstance",
    asset_id_field="notebook_arn",
    identity_fields=("account_id", "account", "notebook_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_sagemaker_notebook_root_access_disabled = Rule(
    id="aws_sagemaker_notebook_root_access_disabled",
    name="SageMaker Notebook Root Access Disabled",
    description="Notebook instance root_access is not 'Disabled' (Enabled or null), so users can obtain root on the notebook instance. Null is treated as failing per the predicate.",
    output_model=AwsSagemakerNotebookRootAccessDisabledOutput,
    facts=(_aws_sagemaker_notebook_root_access_disabled_fact,),
    tags=("security", "sagemaker", "privilege", "cspm"),
    version="0.1.0",
)


class AwsSagemakerNotebookVpcConfigOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    notebook_arn: str | None = None
    notebook_instance_name: str | None = None
    kms_key_id: str | None = None
    subnet_id: str | None = None
    security_groups: str | None = None
    direct_internet_access: str | None = None


_aws_sagemaker_notebook_vpc_config_fact = Fact(
    id="aws_sagemaker_notebook_vpc_config_fact",
    name="SageMaker notebook no VPC",
    description="Notebook instances without a subnet_id.",
    cypher_query="""

        MATCH (acct:AWSAccount)-[:RESOURCE]->(n:AWSSageMakerNotebookInstance)
        WHERE n.subnet_id IS NULL OR n.subnet_id = ''
        RETURN acct.id AS account_id, acct.name AS account, n.arn AS notebook_arn,
               n.notebook_instance_name AS notebook_instance_name,
               n.subnet_id AS subnet_id, n.security_groups AS security_groups

    """,
    cypher_visual_query="""

        MATCH (acct:AWSAccount)-[:RESOURCE]->(n:AWSSageMakerNotebookInstance)
        WHERE n.subnet_id IS NULL OR n.subnet_id = ''
        RETURN acct.id AS account_id, acct.name AS account, n.arn AS notebook_arn,
               n.notebook_instance_name AS notebook_instance_name,
               n.subnet_id AS subnet_id, n.security_groups AS security_groups

    """,
    cypher_count_query="""

        MATCH (n:AWSSageMakerNotebookInstance)
        RETURN count(n) AS total_assets,
               count(CASE WHEN n.subnet_id IS NULL OR n.subnet_id = '' THEN 1 END) AS failing,
               count(n) AS count

    """,
    asset_label="AWSSageMakerNotebookInstance",
    asset_id_field="notebook_arn",
    identity_fields=("notebook_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_sagemaker_notebook_vpc_config = Rule(
    id="aws_sagemaker_notebook_vpc_config",
    name="SageMaker Notebook VPC Configuration",
    description="SageMaker notebook instance has no subnet_id, so it is not attached to a VPC and uses public networking.",
    output_model=AwsSagemakerNotebookVpcConfigOutput,
    facts=(_aws_sagemaker_notebook_vpc_config_fact,),
    tags=("security", "sagemaker", "network", "cspm"),
    version="0.1.0",
)
