"""
AWS CloudTrail Event Coverage and Delivery

The CIS benchmark rules in ``cis_aws_logging`` cover trail encryption, log file
validation, multi-region trails and the log bucket itself. They do not look at
*what* a trail records or where its records are delivered, which is what these
rules cover:

- ``aws_cloudtrail_cloudwatch_logs`` / ``aws_cloudtrail_insights_enabled``:
  per-trail delivery and detection features.
- ``aws_cloudtrail_management_events_read_write`` and the two S3 data-event
  rules: per-account coverage. These are absence checks, so their main node is
  ``AWSAccount`` rather than the trail.

Every property used here is already synced by the AWS intel module
(``CloudTrailTrailNodeProperties`` and ``AWSAccount.inscope``); no new collector
is required.

Selector checks read ``event_selectors`` / ``advanced_event_selectors``, which
are stored as JSON strings. They are matched with ``CONTAINS`` rather than
parsed, so a selector array whose entries are individually narrower can still
satisfy the check. ``IsLogging`` is not synced, so these rules evaluate every
synced trail rather than only the actively logging ones.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class CloudTrailDeliveryOutput(Finding):
    """Output model for the CloudWatch Logs delivery check."""

    account_id: str | None = None
    account: str | None = None
    trail_arn: str | None = None
    trail_name: str | None = None
    cloudwatch_logs_log_group_arn: str | None = None
    region: str | None = None


_aws_cloudtrail_cloudwatch_logs_fact = Fact(
    id="aws_cloudtrail_cloudwatch_logs_fact",
    name="Trail without CloudWatch Logs delivery",
    description=(
        "Trails whose cloudwatch_logs_log_group_arn is null, or that have no "
        "SENDS_LOGS_TO_CLOUDWATCH edge to a log group."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE t.cloudwatch_logs_log_group_arn IS NULL
       OR NOT (t)-[:SENDS_LOGS_TO_CLOUDWATCH]->(:AWSCloudWatchLogGroup)
    RETURN a.id AS account_id, a.name AS account, t.arn AS trail_arn,
           t.name AS trail_name,
           t.cloudwatch_logs_log_group_arn AS cloudwatch_logs_log_group_arn,
           t.region AS region
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE t.cloudwatch_logs_log_group_arn IS NULL
       OR NOT (t)-[:SENDS_LOGS_TO_CLOUDWATCH]->(:AWSCloudWatchLogGroup)
    RETURN *
    """,
    cypher_count_query="""
    MATCH (t:AWSCloudTrailTrail)
    RETURN COUNT(t) AS count
    """,
    asset_label="AWSCloudTrailTrail",
    asset_id_field="trail_arn",
    identity_fields=("account_id", "account", "trail_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudtrail_cloudwatch_logs = Rule(
    id="aws_cloudtrail_cloudwatch_logs",
    name="CloudTrail Trail Without CloudWatch Logs Delivery",
    description=(
        "A trail delivers no logs to CloudWatch Logs. Without that delivery the "
        "records are only in S3, where nothing can alert on them in near real time. "
        "This checks that a log group is configured, not that delivery happened "
        "recently: no delivery timestamp is synced and stored_bytes is cumulative."
    ),
    output_model=CloudTrailDeliveryOutput,
    facts=(_aws_cloudtrail_cloudwatch_logs_fact,),
    tags=("aws", "cloudtrail", "logging"),
    version="0.1.0",
)


class CloudTrailInsightsOutput(Finding):
    """Output model for the Insights check."""

    account_id: str | None = None
    account: str | None = None
    trail_arn: str | None = None
    trail_name: str | None = None
    has_insight_selectors: bool | None = None


_aws_cloudtrail_insights_enabled_fact = Fact(
    id="aws_cloudtrail_insights_enabled_fact",
    name="Trail without Insights selectors",
    description="Trails whose has_insight_selectors is false or null.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE t.has_insight_selectors IS NULL OR t.has_insight_selectors = false
    RETURN a.id AS account_id, a.name AS account,
           t.arn AS trail_arn, t.name AS trail_name,
           t.has_insight_selectors AS has_insight_selectors
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE t.has_insight_selectors IS NULL OR t.has_insight_selectors = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (t:AWSCloudTrailTrail)
    RETURN COUNT(t) AS count
    """,
    asset_label="AWSCloudTrailTrail",
    asset_id_field="trail_arn",
    identity_fields=("account_id", "account", "trail_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudtrail_insights_enabled = Rule(
    id="aws_cloudtrail_insights_enabled",
    name="CloudTrail Insights Disabled",
    description=(
        "A trail has no Insights selectors configured, so unusual API call volume is "
        "never surfaced as an event. IsLogging is not synced, so every synced trail "
        "is evaluated rather than only the actively logging ones."
    ),
    output_model=CloudTrailInsightsOutput,
    facts=(_aws_cloudtrail_insights_enabled_fact,),
    tags=("aws", "cloudtrail", "logging", "observability"),
    version="0.1.0",
)


class CloudTrailAccountCoverageOutput(Finding):
    """Output model for the per-account absence checks."""

    account_id: str | None = None
    account: str | None = None


_aws_cloudtrail_mgmt_events_fact = Fact(
    id="aws_cloudtrail_mgmt_events_fact",
    name="No trail recording management read+write events",
    description=(
        "Accounts with no trail whose selectors record management events for both "
        "read and write (ReadWriteType=All)."
    ),
    cypher_query="""
    MATCH (a:AWSAccount {inscope: true})
    OPTIONAL MATCH (a)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE toString(t.event_selectors) CONTAINS '"ReadWriteType": "All"'
       OR toString(t.event_selectors) CONTAINS '"ReadWriteType":"All"'
       OR toString(t.advanced_event_selectors) CONTAINS '"ReadWriteType": "All"'
       OR toString(t.advanced_event_selectors) CONTAINS '"ReadWriteType":"All"'
    WITH a, t
    WHERE t IS NULL
    RETURN a.id AS account_id, a.name AS account
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount {inscope: true})
    OPTIONAL MATCH p=(a)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WITH a, t, p
    WHERE t IS NULL
    RETURN *
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount {inscope: true})
    RETURN COUNT(a) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "account"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudtrail_management_events_read_write = Rule(
    id="aws_cloudtrail_management_events_read_write",
    name="No Trail Recording Management Read+Write Events",
    description=(
        "No trail in the account records management events for both read and write "
        "operations, so half the control-plane audit record is missing. Coverage is "
        "assessed per account, not per region: there is no region inventory to check "
        "against."
    ),
    output_model=CloudTrailAccountCoverageOutput,
    facts=(_aws_cloudtrail_mgmt_events_fact,),
    tags=("aws", "cloudtrail", "logging", "observability"),
    version="0.1.0",
)


# S3 object-level data events. `arn:aws:s3:::` (all current and future buckets)
# is what makes the check account-wide; naming specific buckets does not count,
# because a bucket created later would not be covered.
_S3_OBJECT_SELECTOR = """
       (toString(t.event_selectors) CONTAINS 'AWS::S3::Object'
        OR toString(t.advanced_event_selectors) CONTAINS 'AWS::S3::Object')
       AND (toString(t.event_selectors) CONTAINS 'arn:aws:s3:::'
            OR toString(t.advanced_event_selectors) CONTAINS 'arn:aws:s3:::')
"""


def _s3_data_event_fact(fact_id: str, read_write_types: tuple[str, ...]) -> Fact:
    """Build an S3 data-event absence fact for the given ReadWriteType values."""
    type_clause = " OR ".join(
        f"""toString(t.event_selectors) CONTAINS '"ReadWriteType": "{t}"'
        OR toString(t.event_selectors) CONTAINS '"ReadWriteType":"{t}"'
        OR toString(t.advanced_event_selectors) CONTAINS '"ReadWriteType": "{t}"'
        OR toString(t.advanced_event_selectors) CONTAINS '"ReadWriteType":"{t}"'"""
        for t in read_write_types
    )
    return Fact(
        id=fact_id,
        name=f"No trail recording S3 object data events ({'/'.join(read_write_types)})",
        description=(
            "Accounts with no trail whose selectors target AWS::S3::Object at "
            f"ReadWriteType {' or '.join(read_write_types)} and cover all current and "
            "future buckets."
        ),
        cypher_query=f"""
    MATCH (a:AWSAccount {{inscope: true}})
    OPTIONAL MATCH (a)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE ({_S3_OBJECT_SELECTOR.strip()})
      AND ({type_clause})
    WITH a, t
    WHERE t IS NULL
    RETURN a.id AS account_id, a.name AS account
    """,
        cypher_visual_query="""
    MATCH (a:AWSAccount {inscope: true})
    OPTIONAL MATCH p=(a)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WITH a, t, p
    WHERE t IS NULL
    RETURN *
    """,
        cypher_count_query="""
    MATCH (a:AWSAccount {inscope: true})
    RETURN COUNT(a) AS count
    """,
        asset_label="AWSAccount",
        asset_id_field="account_id",
        identity_fields=("account_id", "account"),
        module=Module.AWS,
        maturity=Maturity.EXPERIMENTAL,
    )


aws_cloudtrail_s3_data_events_read = Rule(
    id="aws_cloudtrail_s3_data_events_read",
    name="No Trail Recording S3 Read Data Events",
    description=(
        "No trail records S3 object-level read events across all buckets, so reads of "
        "object contents leave no audit record. ReadOnly and All selectors both "
        "qualify, and the selector must cover every bucket (arn:aws:s3:::), not a "
        "named list."
    ),
    output_model=CloudTrailAccountCoverageOutput,
    facts=(_s3_data_event_fact("aws_cloudtrail_s3_read_fact", ("ReadOnly", "All")),),
    tags=("aws", "cloudtrail", "logging", "s3"),
    version="0.1.0",
)


aws_cloudtrail_s3_data_events_write = Rule(
    id="aws_cloudtrail_s3_data_events_write",
    name="No Trail Recording S3 Write Data Events",
    description=(
        "No trail records S3 object-level write events across all buckets, so object "
        "creation and deletion leave no audit record. WriteOnly and All selectors "
        "both qualify, and the selector must cover every bucket (arn:aws:s3:::), not "
        "a named list."
    ),
    output_model=CloudTrailAccountCoverageOutput,
    facts=(_s3_data_event_fact("aws_cloudtrail_s3_write_fact", ("WriteOnly", "All")),),
    tags=("aws", "cloudtrail", "logging", "s3"),
    version="0.1.0",
)


class CloudTrailSelectorCoverageOutput(Finding):
    """Output model for the advanced-selector content checks."""

    account_id: str | None = None
    account: str | None = None
    trail_arn: str | None = None
    trail_name: str | None = None
    is_multi_region_trail: bool | None = None
    advanced_event_selectors: str | None = None


_aws_cloudtrail_bedrock_logging_fact = Fact(
    id="aws_cloudtrail_bedrock_logging_fact",
    name="Trail recording no Bedrock activity",
    description=(
        "Trails with neither an AWS::Bedrock:: advanced selector nor a ReadWriteType=All "
        "management selector."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE NOT (
        toString(coalesce(t.advanced_event_selectors, '')) CONTAINS 'AWS::Bedrock::'
        OR toString(coalesce(t.event_selectors, '')) CONTAINS '"ReadWriteType": "All"'
        OR toString(coalesce(t.event_selectors, '')) CONTAINS '"ReadWriteType":"All"'
    )
    RETURN a.id AS account_id, a.name AS account, t.arn AS trail_arn,
           t.name AS trail_name, t.is_multi_region_trail AS is_multi_region_trail,
           t.advanced_event_selectors AS advanced_event_selectors
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE NOT (
        toString(coalesce(t.advanced_event_selectors, '')) CONTAINS 'AWS::Bedrock::'
        OR toString(coalesce(t.event_selectors, '')) CONTAINS '"ReadWriteType": "All"'
        OR toString(coalesce(t.event_selectors, '')) CONTAINS '"ReadWriteType":"All"'
    )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (t:AWSCloudTrailTrail)
    RETURN COUNT(t) AS count
    """,
    asset_label="AWSCloudTrailTrail",
    asset_id_field="trail_arn",
    identity_fields=("account_id", "account", "trail_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudtrail_bedrock_logging = Rule(
    id="aws_cloudtrail_bedrock_logging",
    name="CloudTrail Bedrock API Logging",
    description=(
        "A trail records no Amazon Bedrock API activity: there is neither an "
        "AWS::Bedrock:: advanced selector nor a ReadWriteType=All management "
        "selector, so a read-only trail does not count as covering it. Selectors are "
        "matched as strings, so a narrower selector array can still satisfy this."
    ),
    output_model=CloudTrailSelectorCoverageOutput,
    facts=(_aws_cloudtrail_bedrock_logging_fact,),
    tags=("aws", "cloudtrail", "logging", "bedrock"),
    version="0.1.0",
)


_aws_cloudtrail_agentcore_fact = Fact(
    id="aws_cloudtrail_agentcore_fact",
    name="Trail recording no Bedrock AgentCore data events",
    description=(
        "Trails with no advanced selector mentioning AWS::BedrockAgentCore resource "
        "types."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE t.advanced_event_selectors IS NULL
       OR NOT toString(t.advanced_event_selectors) CONTAINS 'AWS::BedrockAgentCore'
    RETURN a.id AS account_id, a.name AS account, t.arn AS trail_arn,
           t.name AS trail_name, t.is_multi_region_trail AS is_multi_region_trail,
           t.advanced_event_selectors AS advanced_event_selectors
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(t:AWSCloudTrailTrail)
    WHERE t.advanced_event_selectors IS NULL
       OR NOT toString(t.advanced_event_selectors) CONTAINS 'AWS::BedrockAgentCore'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (t:AWSCloudTrailTrail)
    RETURN COUNT(t) AS count
    """,
    asset_label="AWSCloudTrailTrail",
    asset_id_field="trail_arn",
    identity_fields=("account_id", "account", "trail_arn"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_cloudtrail_agentcore_data_events = Rule(
    id="aws_cloudtrail_agentcore_data_events",
    name="CloudTrail Bedrock AgentCore Data Events",
    description=(
        "A trail records no Bedrock AgentCore data events: no advanced selector "
        "mentions AWS::BedrockAgentCore resource types, so agent runtime, gateway, "
        "memory and code-interpreter activity would not be captured. Per-resource-type "
        "coverage against what the account actually runs is not verified, and a single "
        "trail covering AgentCore satisfies the account."
    ),
    output_model=CloudTrailSelectorCoverageOutput,
    facts=(_aws_cloudtrail_agentcore_fact,),
    tags=("aws", "cloudtrail", "logging", "bedrock"),
    version="0.1.0",
)
