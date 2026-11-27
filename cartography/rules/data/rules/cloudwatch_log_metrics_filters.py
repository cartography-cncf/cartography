"""
AWS CloudWatch Logs metric filters for security-relevant API activity

CIS-style monitoring checks: each rule fails an account when no CloudWatch Logs
metric filter matching a security-relevant event pattern exists. These are
absence checks, so the subject is the account, not the filter.

Matching is deliberately conservative. Cartography stores the filter pattern as
an opaque string, so a filter is counted only when its pattern contains the
event-name literals (for example ``ConsoleLogin``, ``StopLogging``) plus the
triggering ``errorCode``/``eventSource`` keyword where the check implies one.
A single filter that bundles several event names satisfies every rule whose
names it lists.

Three limitations follow from that and are not detectable from the graph:
matching is case-sensitive, so a pattern spelled differently is missed; the
filter-to-alarm association is not modelled (``AWSCloudWatchLogMetricFilter``
links only ``METRIC_FILTER_OF`` to its log group, and ``AWSCloudWatchMetricAlarm``
carries no metric name or namespace), so what is verified is that a matching
filter exists, not that an alarm or action is wired to it; and filters are not
scoped to CloudTrail-fed log groups.

Every property used here is already synced by the AWS intel module; no
collector change is required. All rules are EXPERIMENTAL until validated
against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsCloudwatchMetricFilterAuthenticationFailuresOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_authentication_failures_fact = Fact(
    id="aws_cloudwatch_metric_filter_authentication_failures_fact",
    name="Missing metric filter for Console Authentication Failures",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches ConsoleLogin events with errorMessage 'Failed authentication' (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'ConsoleLogin' AND mf.filter_pattern CONTAINS 'Failed authentication')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'ConsoleLogin' AND mf.filter_pattern CONTAINS 'Failed authentication')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_authentication_failures = Rule(
    id="aws_cloudwatch_metric_filter_authentication_failures",
    name="CloudWatch Metric Filter and Alarm for Console Authentication Failures",
    description="No CloudWatch Logs metric filter matching ConsoleLogin events with errorMessage 'Failed authentication' exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterAuthenticationFailuresOutput,
    facts=(_aws_cloudwatch_metric_filter_authentication_failures_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterCloudtrailChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_cloudtrail_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_cloudtrail_changes_fact",
    name="Missing metric filter for CloudTrail Configuration Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches CloudTrail configuration change events (CreateTrail, UpdateTrail, DeleteTrail, StartLogging, StopLogging) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'CreateTrail' OR mf.filter_pattern CONTAINS 'UpdateTrail' OR mf.filter_pattern CONTAINS 'DeleteTrail' OR mf.filter_pattern CONTAINS 'StartLogging' OR mf.filter_pattern CONTAINS 'StopLogging')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'CreateTrail' OR mf.filter_pattern CONTAINS 'UpdateTrail' OR mf.filter_pattern CONTAINS 'DeleteTrail' OR mf.filter_pattern CONTAINS 'StartLogging' OR mf.filter_pattern CONTAINS 'StopLogging')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_cloudtrail_changes = Rule(
    id="aws_cloudwatch_metric_filter_cloudtrail_changes",
    name="CloudWatch Metric Filter and Alarm for CloudTrail Configuration Changes",
    description="No CloudWatch Logs metric filter matching CloudTrail configuration change events (CreateTrail, UpdateTrail, DeleteTrail, StartLogging, StopLogging) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterCloudtrailChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_cloudtrail_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterConfigChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_config_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_config_changes_fact",
    name="Missing metric filter for AWS Config Configuration Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches AWS Config configuration change events (StopConfigurationRecorder, DeleteDeliveryChannel, PutDeliveryChannel, PutConfigurationRecorder) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'ConfigurationRecorder' OR mf.filter_pattern CONTAINS 'DeliveryChannel')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'ConfigurationRecorder' OR mf.filter_pattern CONTAINS 'DeliveryChannel')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_config_changes = Rule(
    id="aws_cloudwatch_metric_filter_config_changes",
    name="CloudWatch Metric Filter and Alarm for AWS Config Configuration Changes",
    description="No CloudWatch Logs metric filter matching AWS Config configuration change events (StopConfigurationRecorder, DeleteDeliveryChannel, PutDeliveryChannel, PutConfigurationRecorder) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterConfigChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_config_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterIamPolicyChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_iam_policy_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_iam_policy_changes_fact",
    name="Missing metric filter for IAM Policy Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches IAM policy change events (CreatePolicy, DeletePolicy, policy version changes, inline policy edits, policy attach/detach) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'CreatePolicy' OR mf.filter_pattern CONTAINS 'DeletePolicy' OR mf.filter_pattern CONTAINS 'PolicyVersion' OR mf.filter_pattern CONTAINS 'PutRolePolicy' OR mf.filter_pattern CONTAINS 'PutUserPolicy' OR mf.filter_pattern CONTAINS 'PutGroupPolicy' OR mf.filter_pattern CONTAINS 'DeleteRolePolicy' OR mf.filter_pattern CONTAINS 'DeleteUserPolicy' OR mf.filter_pattern CONTAINS 'DeleteGroupPolicy' OR mf.filter_pattern CONTAINS 'AttachRolePolicy' OR mf.filter_pattern CONTAINS 'DetachRolePolicy' OR mf.filter_pattern CONTAINS 'AttachUserPolicy' OR mf.filter_pattern CONTAINS 'DetachUserPolicy' OR mf.filter_pattern CONTAINS 'AttachGroupPolicy' OR mf.filter_pattern CONTAINS 'DetachGroupPolicy')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'CreatePolicy' OR mf.filter_pattern CONTAINS 'DeletePolicy' OR mf.filter_pattern CONTAINS 'PolicyVersion' OR mf.filter_pattern CONTAINS 'PutRolePolicy' OR mf.filter_pattern CONTAINS 'PutUserPolicy' OR mf.filter_pattern CONTAINS 'PutGroupPolicy' OR mf.filter_pattern CONTAINS 'DeleteRolePolicy' OR mf.filter_pattern CONTAINS 'DeleteUserPolicy' OR mf.filter_pattern CONTAINS 'DeleteGroupPolicy' OR mf.filter_pattern CONTAINS 'AttachRolePolicy' OR mf.filter_pattern CONTAINS 'DetachRolePolicy' OR mf.filter_pattern CONTAINS 'AttachUserPolicy' OR mf.filter_pattern CONTAINS 'DetachUserPolicy' OR mf.filter_pattern CONTAINS 'AttachGroupPolicy' OR mf.filter_pattern CONTAINS 'DetachGroupPolicy')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_iam_policy_changes = Rule(
    id="aws_cloudwatch_metric_filter_iam_policy_changes",
    name="CloudWatch Metric Filter and Alarm for IAM Policy Changes",
    description="No CloudWatch Logs metric filter matching IAM policy change events (CreatePolicy, DeletePolicy, policy version changes, inline policy edits, policy attach/detach) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterIamPolicyChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_iam_policy_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterKmsCmkDeletionOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_kms_cmk_deletion_fact = Fact(
    id="aws_cloudwatch_metric_filter_kms_cmk_deletion_fact",
    name="Missing metric filter for KMS CMK Disable or Scheduled Deletion",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches DisableKey and ScheduleKeyDeletion events from kms.amazonaws.com (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'ScheduleKeyDeletion' OR mf.filter_pattern CONTAINS 'DisableKey')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'ScheduleKeyDeletion' OR mf.filter_pattern CONTAINS 'DisableKey')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_kms_cmk_deletion = Rule(
    id="aws_cloudwatch_metric_filter_kms_cmk_deletion",
    name="CloudWatch Metric Filter and Alarm for KMS CMK Disable or Scheduled Deletion",
    description="No CloudWatch Logs metric filter matching DisableKey and ScheduleKeyDeletion events from kms.amazonaws.com exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterKmsCmkDeletionOutput,
    facts=(_aws_cloudwatch_metric_filter_kms_cmk_deletion_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterNetworkAclChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_network_acl_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_network_acl_changes_fact",
    name="Missing metric filter for Network ACL Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches Network ACL (NACL) change events (CreateNetworkAcl, CreateNetworkAclEntry, DeleteNetworkAcl, DeleteNetworkAclEntry, ReplaceNetworkAclEntry, ReplaceNetworkAclAssociation) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'NetworkAcl')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'NetworkAcl')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_network_acl_changes = Rule(
    id="aws_cloudwatch_metric_filter_network_acl_changes",
    name="CloudWatch Metric Filter and Alarm for Network ACL Changes",
    description="No CloudWatch Logs metric filter matching Network ACL (NACL) change events (CreateNetworkAcl, CreateNetworkAclEntry, DeleteNetworkAcl, DeleteNetworkAclEntry, ReplaceNetworkAclEntry, ReplaceNetworkAclAssociation) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterNetworkAclChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_network_acl_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterNetworkGatewayChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_network_gateway_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_network_gateway_changes_fact",
    name="Missing metric filter for Network Gateway Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches network gateway change events (CreateCustomerGateway, DeleteCustomerGateway, AttachInternetGateway, CreateInternetGateway, DeleteInternetGateway, DetachInternetGateway) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'CustomerGateway' OR mf.filter_pattern CONTAINS 'InternetGateway')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'CustomerGateway' OR mf.filter_pattern CONTAINS 'InternetGateway')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_network_gateway_changes = Rule(
    id="aws_cloudwatch_metric_filter_network_gateway_changes",
    name="CloudWatch Metric Filter and Alarm for Network Gateway Changes",
    description="No CloudWatch Logs metric filter matching network gateway change events (CreateCustomerGateway, DeleteCustomerGateway, AttachInternetGateway, CreateInternetGateway, DeleteInternetGateway, DetachInternetGateway) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterNetworkGatewayChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_network_gateway_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterOrganizationsChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_organizations_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_organizations_changes_fact",
    name="Missing metric filter for AWS Organizations Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches AWS Organizations change events (eventSource organizations.amazonaws.com; CreateAccount, MoveAccount, UpdateOrganizationalUnit and similar) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'organizations.amazonaws.com' OR mf.filter_pattern CONTAINS 'CreateAccount' OR mf.filter_pattern CONTAINS 'MoveAccount' OR mf.filter_pattern CONTAINS 'UpdateOrganizationalUnit')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'organizations.amazonaws.com' OR mf.filter_pattern CONTAINS 'CreateAccount' OR mf.filter_pattern CONTAINS 'MoveAccount' OR mf.filter_pattern CONTAINS 'UpdateOrganizationalUnit')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_organizations_changes = Rule(
    id="aws_cloudwatch_metric_filter_organizations_changes",
    name="CloudWatch Metric Filter and Alarm for AWS Organizations Changes",
    description="No CloudWatch Logs metric filter matching AWS Organizations change events (eventSource organizations.amazonaws.com; CreateAccount, MoveAccount, UpdateOrganizationalUnit and similar) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterOrganizationsChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_organizations_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterRootUsageOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_root_usage_fact = Fact(
    id="aws_cloudwatch_metric_filter_root_usage_fact",
    name="Missing metric filter for Root Account Usage",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches root account activity (userIdentity.type = 'Root', invokedBy NOT EXISTS, eventType != 'AwsServiceEvent') (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'userIdentity' AND mf.filter_pattern CONTAINS 'Root')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'userIdentity' AND mf.filter_pattern CONTAINS 'Root')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_root_usage = Rule(
    id="aws_cloudwatch_metric_filter_root_usage",
    name="CloudWatch Metric Filter and Alarm for Root Account Usage",
    description="No CloudWatch Logs metric filter matching root account activity (userIdentity.type = 'Root', invokedBy NOT EXISTS, eventType != 'AwsServiceEvent') exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterRootUsageOutput,
    facts=(_aws_cloudwatch_metric_filter_root_usage_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterRouteTableChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_route_table_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_route_table_changes_fact",
    name="Missing metric filter for Route Table Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches route table change events (CreateRoute, CreateRouteTable, ReplaceRoute, ReplaceRouteTableAssociation, DeleteRoute, DeleteRouteTable) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'RouteTable' OR mf.filter_pattern CONTAINS 'CreateRoute' OR mf.filter_pattern CONTAINS 'DeleteRoute' OR mf.filter_pattern CONTAINS 'ReplaceRoute')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'RouteTable' OR mf.filter_pattern CONTAINS 'CreateRoute' OR mf.filter_pattern CONTAINS 'DeleteRoute' OR mf.filter_pattern CONTAINS 'ReplaceRoute')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_route_table_changes = Rule(
    id="aws_cloudwatch_metric_filter_route_table_changes",
    name="CloudWatch Metric Filter and Alarm for Route Table Changes",
    description="No CloudWatch Logs metric filter matching route table change events (CreateRoute, CreateRouteTable, ReplaceRoute, ReplaceRouteTableAssociation, DeleteRoute, DeleteRouteTable) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterRouteTableChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_route_table_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterS3BucketPolicyChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_s3_bucket_policy_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_s3_bucket_policy_changes_fact",
    name="Missing metric filter for S3 Bucket Policy Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches S3 bucket policy/configuration change events (PutBucketPolicy, DeleteBucketPolicy, PutBucketAcl, PutBucketCors, PutBucketLifecycle, PutBucketReplication and similar Put/Delete bucket-configuration operations) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'BucketPolicy' OR mf.filter_pattern CONTAINS 'BucketAcl' OR mf.filter_pattern CONTAINS 'BucketCors' OR mf.filter_pattern CONTAINS 'BucketLifecycle' OR mf.filter_pattern CONTAINS 'BucketReplication')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'BucketPolicy' OR mf.filter_pattern CONTAINS 'BucketAcl' OR mf.filter_pattern CONTAINS 'BucketCors' OR mf.filter_pattern CONTAINS 'BucketLifecycle' OR mf.filter_pattern CONTAINS 'BucketReplication')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_s3_bucket_policy_changes = Rule(
    id="aws_cloudwatch_metric_filter_s3_bucket_policy_changes",
    name="CloudWatch Metric Filter and Alarm for S3 Bucket Policy Changes",
    description="No CloudWatch Logs metric filter matching S3 bucket policy/configuration change events (PutBucketPolicy, DeleteBucketPolicy, PutBucketAcl, PutBucketCors, PutBucketLifecycle, PutBucketReplication and similar Put/Delete bucket-configuration operations) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterS3BucketPolicyChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_s3_bucket_policy_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterSecurityGroupChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_security_group_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_security_group_changes_fact",
    name="Missing metric filter for Security Group Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches security group change events (AuthorizeSecurityGroupIngress/Egress, RevokeSecurityGroupIngress/Egress, CreateSecurityGroup, DeleteSecurityGroup) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'SecurityGroup')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'SecurityGroup')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_security_group_changes = Rule(
    id="aws_cloudwatch_metric_filter_security_group_changes",
    name="CloudWatch Metric Filter and Alarm for Security Group Changes",
    description="No CloudWatch Logs metric filter matching security group change events (AuthorizeSecurityGroupIngress/Egress, RevokeSecurityGroupIngress/Egress, CreateSecurityGroup, DeleteSecurityGroup) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterSecurityGroupChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_security_group_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterSignInWithoutMfaOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_sign_in_without_mfa_fact = Fact(
    id="aws_cloudwatch_metric_filter_sign_in_without_mfa_fact",
    name="Missing metric filter for Console Sign-in Without MFA",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches ConsoleLogin events where additionalEventData.MFAUsed != 'Yes' (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'ConsoleLogin' AND mf.filter_pattern CONTAINS 'MFAUsed')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'ConsoleLogin' AND mf.filter_pattern CONTAINS 'MFAUsed')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_sign_in_without_mfa = Rule(
    id="aws_cloudwatch_metric_filter_sign_in_without_mfa",
    name="CloudWatch Metric Filter and Alarm for Console Sign-in Without MFA",
    description="No CloudWatch Logs metric filter matching ConsoleLogin events where additionalEventData.MFAUsed != 'Yes' exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterSignInWithoutMfaOutput,
    facts=(_aws_cloudwatch_metric_filter_sign_in_without_mfa_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterUnauthorizedApiCallsOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_unauthorized_api_calls_fact = Fact(
    id="aws_cloudwatch_metric_filter_unauthorized_api_calls_fact",
    name="Missing metric filter for Unauthorized API Calls",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches unauthorized API errors (errorCode '*UnauthorizedOperation' or 'AccessDenied*') (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'UnauthorizedOperation' OR mf.filter_pattern CONTAINS 'AccessDenied')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'UnauthorizedOperation' OR mf.filter_pattern CONTAINS 'AccessDenied')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_unauthorized_api_calls = Rule(
    id="aws_cloudwatch_metric_filter_unauthorized_api_calls",
    name="CloudWatch Metric Filter and Alarm for Unauthorized API Calls",
    description="No CloudWatch Logs metric filter matching unauthorized API errors (errorCode '*UnauthorizedOperation' or 'AccessDenied*') exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterUnauthorizedApiCallsOutput,
    facts=(_aws_cloudwatch_metric_filter_unauthorized_api_calls_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)


class AwsCloudwatchMetricFilterVpcChangesOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_cloudwatch_metric_filter_vpc_changes_fact = Fact(
    id="aws_cloudwatch_metric_filter_vpc_changes_fact",
    name="Missing metric filter for VPC Changes",
    description="Accounts with no CloudWatch Logs metric filter whose filter_pattern matches VPC change events (CreateVpc, DeleteVpc, ModifyVpcAttribute and VPC peering create/accept/reject/delete operations) (keyword match).",
    cypher_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'CreateVpc' OR mf.filter_pattern CONTAINS 'DeleteVpc' OR mf.filter_pattern CONTAINS 'ModifyVpcAttribute' OR mf.filter_pattern CONTAINS 'VpcPeeringConnection')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope:true})
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(mf:AWSCloudWatchLogMetricFilter)
        WHERE mf.filter_pattern IS NOT NULL
          AND (mf.filter_pattern CONTAINS 'CreateVpc' OR mf.filter_pattern CONTAINS 'DeleteVpc' OR mf.filter_pattern CONTAINS 'ModifyVpcAttribute' OR mf.filter_pattern CONTAINS 'VpcPeeringConnection')
    }
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope:true}) RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_metric_filter_vpc_changes = Rule(
    id="aws_cloudwatch_metric_filter_vpc_changes",
    name="CloudWatch Metric Filter and Alarm for VPC Changes",
    description="No CloudWatch Logs metric filter matching VPC change events (CreateVpc, DeleteVpc, ModifyVpcAttribute and VPC peering create/accept/reject/delete operations) exists in the account. Caveats (EXPERIMENTAL): matching is keyword-based, case-sensitive CONTAINS on filter_pattern, so it may over- or under-match versus the exact CIS filter pattern. The filter->alarm association is not stored in the graph (AWSCloudWatchLogMetricFilter links only METRIC_FILTER_OF to its log group; AWSCloudWatchMetricAlarm has no metric_name/metric_namespace and no relationship to filters), so alarm existence, AlarmActions and SNS subscriber wiring cannot be verified; metric-filter existence is the proxy. Filters are not scoped to CloudTrail-fed log groups.",
    output_model=AwsCloudwatchMetricFilterVpcChangesOutput,
    facts=(_aws_cloudwatch_metric_filter_vpc_changes_fact,),
    tags=("monitoring", "cloudwatch", "cis", "cspm", "best-effort"),
    version="0.1.0",
)
