"""
AWS CloudWatch alarm response configuration

An alarm that cannot act is noise. ``actions_enabled`` is the only action
property Cartography syncs, so this checks that actions are enabled, not that
an action target is reachable.

Every property used here is already synced by the AWS intel module; no
collector change is required. All rules are EXPERIMENTAL until validated
against a live graph.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsCloudwatchAlarmActionsEnabledOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    alarm_arn: str | None = None
    alarm_name: str | None = None
    state_value: str | None = None
    actions_enabled: str | None = None
    region: str | None = None


_aws_cloudwatch_alarm_actions_enabled_fact = Fact(
    id="aws_cloudwatch_alarm_actions_enabled_fact",
    name="CloudWatch alarm actions disabled",
    description="Metric alarms with actions_enabled=false/null.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(alarm:AWSCloudWatchMetricAlarm)
        WHERE coalesce(alarm.actions_enabled, false) = false
        RETURN a.id AS account_id, a.name AS account, alarm.arn AS alarm_arn,
               alarm.alarm_name AS alarm_name, alarm.state_value AS state_value,
               alarm.actions_enabled AS actions_enabled, alarm.region AS region

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(alarm:AWSCloudWatchMetricAlarm)
        WHERE coalesce(alarm.actions_enabled, false) = false
        RETURN a.id AS account_id, a.name AS account, alarm.arn AS alarm_arn,
               alarm.alarm_name AS alarm_name, alarm.state_value AS state_value,
               alarm.actions_enabled AS actions_enabled, alarm.region AS region

    """,
    cypher_count_query="""
    MATCH (alarm:AWSCloudWatchMetricAlarm)
        RETURN COUNT(alarm) AS count, COUNT(alarm) AS total_assets,
               COUNT(CASE WHEN coalesce(alarm.actions_enabled, false) = false THEN 1 END) AS failing
    """,
    asset_label="AWSCloudWatchMetricAlarm",
    asset_id_field="alarm_arn",
    identity_fields=("alarm_arn",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudwatch_alarm_actions_enabled = Rule(
    id="aws_cloudwatch_alarm_actions_enabled",
    name="CloudWatch Alarm Actions Enabled",
    description="CloudWatch metric alarm has actions_enabled=false (or null), so state changes invoke no notification or automated response. Alarm action ARN lists are not synced, but this check only needs the activation flag.",
    output_model=AwsCloudwatchAlarmActionsEnabledOutput,
    facts=(_aws_cloudwatch_alarm_actions_enabled_fact,),
    tags=("security", "cloudwatch", "monitoring", "cspm"),
    version="0.1.0",
)
