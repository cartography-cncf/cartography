"""
AWS CloudWatch log group configuration hygiene

At-rest encryption, retention and data-protection policy for log groups, plus
detection of the role that enables CloudWatch cross-account sharing.
Retention is a policy choice, so the minimum age is configurable below rather
than fixed; log groups set never to expire pass.

Every property used here is already synced by the AWS intel module; no
collector change is required. All rules are EXPERIMENTAL until validated
against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsCloudwatchAgentcoreLogGroupDataProtectionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    log_group_id: str | None = None
    log_group_name: str | None = None
    kms_key_id: str | None = None
    retention_in_days: str | None = None
    data_protection_status: str | None = None
    inherited_properties: str | None = None


_aws_cloudwatch_agentcore_log_group_data_protection_fact = Fact(
    id="aws_cloudwatch_agentcore_log_group_data_protection_fact",
    name="AgentCore log group without data protection",
    description="AgentCore-named log groups with data_protection_status not ACTIVE and no inherited account-level data protection policy.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lg:AWSCloudWatchLogGroup)
        WHERE (lg.log_group_name STARTS WITH '/aws/vendedlogs/bedrock-agentcore/'
               OR lg.log_group_name STARTS WITH '/aws/bedrock-agentcore/')
          AND coalesce(lg.data_protection_status, '') <> 'ACTIVE'
          AND NOT 'DATA_PROTECTION_POLICY' IN coalesce(lg.inherited_properties, [])
        RETURN a.id AS account_id, a.name AS account, lg.id AS log_group_id,
               lg.log_group_name AS log_group_name,
               lg.data_protection_status AS data_protection_status,
               lg.inherited_properties AS inherited_properties

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(lg:AWSCloudWatchLogGroup)
        WHERE (lg.log_group_name STARTS WITH '/aws/vendedlogs/bedrock-agentcore/'
               OR lg.log_group_name STARTS WITH '/aws/bedrock-agentcore/')
          AND coalesce(lg.data_protection_status, '') <> 'ACTIVE'
          AND NOT 'DATA_PROTECTION_POLICY' IN coalesce(lg.inherited_properties, [])
        RETURN *

    """,
    cypher_count_query="""
    MATCH (lg:AWSCloudWatchLogGroup) RETURN COUNT(lg) AS count
    """,
    asset_label="AWSCloudWatchLogGroup",
    asset_id_field="log_group_id",
    identity_fields=("account_id", "account", "log_group_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_agentcore_log_group_data_protection = Rule(
    id="aws_cloudwatch_agentcore_log_group_data_protection",
    name="Bedrock AgentCore Log Group Data Protection",
    description="A Bedrock AgentCore log group has no active CloudWatch Logs data protection policy and inherits none from account-level settings, so sensitive agent telemetry (prompts, tool arguments, retrieved context) is stored unmasked. Caveats (EXPERIMENTAL): AgentCore scoping is a log-group name-prefix heuristic ('/aws/vendedlogs/bedrock-agentcore/' and '/aws/bedrock-agentcore/', the standard prefixes); AgentCore delivery to arbitrarily named log groups (e.g. the shared aws/spans group) is not covered. inherited_properties semantics and sync population are unverified; the inheritance test is a toString/CONTAINS approximation tolerant of list or string storage.",
    output_model=AwsCloudwatchAgentcoreLogGroupDataProtectionOutput,
    facts=(_aws_cloudwatch_agentcore_log_group_data_protection_fact,),
    tags=("monitoring", "cloudwatch", "data-protection", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchCrossAccountSharingDisabledOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    role_arn: str | None = None
    role_name: str | None = None


_aws_cloudwatch_cross_account_sharing_disabled_fact = Fact(
    id="aws_cloudwatch_cross_account_sharing_disabled_fact",
    name="CloudWatch cross-account sharing role present",
    description="Accounts containing the CloudWatch-CrossAccountSharingRole IAM role.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(r:AWSRole)
        WHERE r.name = 'CloudWatch-CrossAccountSharingRole'
        RETURN a.id AS account_id, a.name AS account, r.arn AS role_arn, r.name AS role_name

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(r:AWSRole)
        WHERE r.name = 'CloudWatch-CrossAccountSharingRole'
        RETURN *

    """,
    cypher_count_query="""
    MATCH (r:AWSRole) RETURN COUNT(r) AS count
    """,
    asset_label="AWSRole",
    asset_id_field="role_arn",
    identity_fields=("account_id", "account", "role_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_cross_account_sharing_disabled = Rule(
    id="aws_cloudwatch_cross_account_sharing_disabled",
    name="CloudWatch Cross-Account Sharing Disabled",
    description="An IAM role named 'CloudWatch-CrossAccountSharingRole' exists in the account, indicating CloudWatch cross-account sharing is active (other accounts can view metrics, dashboards and alarms).",
    output_model=AwsCloudwatchCrossAccountSharingDisabledOutput,
    facts=(_aws_cloudwatch_cross_account_sharing_disabled_fact,),
    tags=("monitoring", "cloudwatch", "iam", "cspm"),
    version="0.1.0",
)


class AwsCloudwatchLogGroupKmsEncryptionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    log_group_id: str | None = None
    log_group_name: str | None = None
    kms_key_id: str | None = None
    retention_in_days: str | None = None
    data_protection_status: str | None = None
    inherited_properties: str | None = None


_aws_cloudwatch_log_group_kms_encryption_fact = Fact(
    id="aws_cloudwatch_log_group_kms_encryption_fact",
    name="Log group without KMS encryption",
    description="Log groups with kms_key_id null or empty.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lg:AWSCloudWatchLogGroup)
        WHERE lg.kms_key_id IS NULL OR lg.kms_key_id = ''
        RETURN a.id AS account_id, a.name AS account, lg.id AS log_group_id,
               lg.log_group_name AS log_group_name, lg.kms_key_id AS kms_key_id

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(lg:AWSCloudWatchLogGroup)
        WHERE lg.kms_key_id IS NULL OR lg.kms_key_id = ''
        RETURN *

    """,
    cypher_count_query="""
    MATCH (lg:AWSCloudWatchLogGroup) RETURN COUNT(lg) AS count
    """,
    asset_label="AWSCloudWatchLogGroup",
    asset_id_field="log_group_id",
    identity_fields=("account_id", "account", "log_group_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_log_group_kms_encryption = Rule(
    id="aws_cloudwatch_log_group_kms_encryption",
    name="CloudWatch Log Group KMS Encryption",
    description="CloudWatch log group has no AWS KMS key associated for at-rest encryption (kms_key_id null/empty).",
    output_model=AwsCloudwatchLogGroupKmsEncryptionOutput,
    facts=(_aws_cloudwatch_log_group_kms_encryption_fact,),
    tags=("monitoring", "cloudwatch", "encryption", "cspm"),
    version="0.1.0",
)


class AwsCloudwatchLogGroupRetentionOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    log_group_id: str | None = None
    log_group_name: str | None = None
    kms_key_id: str | None = None
    retention_in_days: str | None = None
    data_protection_status: str | None = None
    inherited_properties: str | None = None


_aws_cloudwatch_log_group_retention_fact = Fact(
    id="aws_cloudwatch_log_group_retention_fact",
    name="Log group retention below minimum",
    description="Log groups with retention_in_days set and < 365.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(lg:AWSCloudWatchLogGroup)
        WHERE lg.retention_in_days IS NOT NULL AND lg.retention_in_days < 365
        RETURN a.id AS account_id, a.name AS account, lg.id AS log_group_id,
               lg.log_group_name AS log_group_name, lg.retention_in_days AS retention_in_days

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(lg:AWSCloudWatchLogGroup)
        WHERE lg.retention_in_days IS NOT NULL AND lg.retention_in_days < 365
        RETURN *

    """,
    cypher_count_query="""
    MATCH (lg:AWSCloudWatchLogGroup) RETURN COUNT(lg) AS count
    """,
    asset_label="AWSCloudWatchLogGroup",
    asset_id_field="log_group_id",
    identity_fields=("account_id", "account", "log_group_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_log_group_retention = Rule(
    id="aws_cloudwatch_log_group_retention",
    name="CloudWatch Log Group Retention Policy",
    description="CloudWatch log group retention_in_days is set below the configured minimum (default 365 days). Log groups set to never expire (null retention) pass.",
    output_model=AwsCloudwatchLogGroupRetentionOutput,
    facts=(_aws_cloudwatch_log_group_retention_fact,),
    tags=("monitoring", "cloudwatch", "logging", "cspm"),
    version="0.1.0",
)
