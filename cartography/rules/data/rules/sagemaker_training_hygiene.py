"""
AWS SageMaker training job isolation

Network isolation and inter-container traffic encryption for training jobs.
Both properties are populated by ``transform_training_jobs``.

No collector change is required: every property read here is already
populated by the AWS SageMaker intel module. All rules are EXPERIMENTAL
until validated against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsSagemakerTrainingIntercontainerEncryptionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    training_job_arn: str | None = None
    training_job_name: str | None = None
    inter_container_encryption: str | None = None
    training_job_status: str | None = None


_aws_sagemaker_training_intercontainer_encryption_fact = Fact(
    id="aws_sagemaker_training_intercontainer_encryption_fact",
    name="Training job without inter-container encryption",
    description="Training jobs with inter-container traffic encryption disabled/absent.",
    cypher_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(t:AWSSageMakerTrainingJob)
        WHERE t.enable_inter_container_traffic_encryption IS NULL
           OR t.enable_inter_container_traffic_encryption = false
        RETURN a.id AS account_id, a.name AS account, t.arn AS training_job_arn,
               t.training_job_name AS training_job_name,
               t.enable_inter_container_traffic_encryption AS inter_container_encryption,
               t.training_job_status AS training_job_status

    """,
    cypher_visual_query="""

        MATCH (a:AWSAccount)-[:RESOURCE]->(t:AWSSageMakerTrainingJob)
        WHERE t.enable_inter_container_traffic_encryption IS NULL
           OR t.enable_inter_container_traffic_encryption = false
        RETURN a.id AS account_id, a.name AS account, t.arn AS training_job_arn,
               t.training_job_name AS training_job_name,
               t.enable_inter_container_traffic_encryption AS inter_container_encryption,
               t.training_job_status AS training_job_status

    """,
    cypher_count_query="""
    MATCH (t:AWSSageMakerTrainingJob) RETURN COUNT(t) AS count
    """,
    asset_label="AWSSageMakerTrainingJob",
    asset_id_field="training_job_arn",
    identity_fields=("account_id", "account", "training_job_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_sagemaker_training_intercontainer_encryption = Rule(
    id="aws_sagemaker_training_intercontainer_encryption",
    name="SageMaker Training Inter-Container Encryption",
    description="Training job has enable_inter_container_traffic_encryption false or null, so traffic between training containers is not encrypted. Null is treated as failing (missing evidence of encryption).",
    output_model=AwsSagemakerTrainingIntercontainerEncryptionOutput,
    facts=(_aws_sagemaker_training_intercontainer_encryption_fact,),
    tags=("security", "sagemaker", "encryption", "cspm"),
    version="0.1.0",
)


class AwsSagemakerTrainingNetworkIsolationOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    training_job_arn: str | None = None
    training_job_name: str | None = None
    enable_network_isolation: bool | None = None


_aws_sagemaker_training_network_isolation_fact = Fact(
    id="aws_sagemaker_training_network_isolation_fact",
    name="SageMaker training no isolation",
    description="Training jobs with enable_network_isolation false/null.",
    cypher_query="""

        MATCH (acct:AWSAccount)-[:RESOURCE]->(t:AWSSageMakerTrainingJob)
        WHERE t.enable_network_isolation IS NULL OR t.enable_network_isolation = false
        RETURN acct.id AS account_id, acct.name AS account, t.arn AS training_job_arn,
               t.training_job_name AS training_job_name,
               t.enable_network_isolation AS enable_network_isolation

    """,
    cypher_visual_query="""

        MATCH (acct:AWSAccount)-[:RESOURCE]->(t:AWSSageMakerTrainingJob)
        WHERE t.enable_network_isolation IS NULL OR t.enable_network_isolation = false
        RETURN acct.id AS account_id, acct.name AS account, t.arn AS training_job_arn,
               t.training_job_name AS training_job_name,
               t.enable_network_isolation AS enable_network_isolation

    """,
    cypher_count_query="""

        MATCH (t:AWSSageMakerTrainingJob)
        RETURN count(t) AS total_assets,
               count(CASE WHEN t.enable_network_isolation IS NULL OR t.enable_network_isolation = false THEN 1 END) AS failing,
               count(t) AS count

    """,
    asset_label="AWSSageMakerTrainingJob",
    asset_id_field="training_job_arn",
    identity_fields=("training_job_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_sagemaker_training_network_isolation = Rule(
    id="aws_sagemaker_training_network_isolation",
    name="SageMaker Training Network Isolation",
    description="SageMaker training job has enable_network_isolation false or unset.",
    output_model=AwsSagemakerTrainingNetworkIsolationOutput,
    facts=(_aws_sagemaker_training_network_isolation_fact,),
    tags=("security", "sagemaker", "cspm"),
    version="0.1.0",
)
