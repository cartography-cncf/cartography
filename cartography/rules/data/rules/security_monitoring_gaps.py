from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AWSSecurityHubConfigurationGapOutput(Finding):
    account_name: str | None = None
    account_id: str | None = None
    region: str | None = None
    gap_type: str | None = None
    auto_enable_controls: bool | None = None


_aws_security_hub_missing = Fact(
    id="aws_security_hub_missing",
    name="AWS regions without Security Hub",
    description=(
        "Detects active AWS regions that contain supported resources but have no "
        "Security Hub subscription."
    ),
    cypher_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(resource)
    WHERE resource.region IS NOT NULL
      AND (
        resource:AWSEC2Instance
        OR resource:AWSEKSCluster
        OR resource:AWSLambda
        OR resource:AWSECSCluster
        OR resource:AWSRDSInstance
        OR resource:AWSRDSCluster
      )
    WITH DISTINCT account, resource.region AS region
    WHERE NOT EXISTS {
        MATCH (account)-[:RESOURCE]->(hub:AWSSecurityHub)
        WHERE split(hub.id, ':')[3] = region
    }
    RETURN
        account.name AS account_name,
        account.id AS account_id,
        region,
        'security_hub_missing' AS gap_type,
        null AS auto_enable_controls
    """,
    cypher_visual_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(resource)
    WHERE resource.region IS NOT NULL
      AND (
        resource:AWSEC2Instance
        OR resource:AWSEKSCluster
        OR resource:AWSLambda
        OR resource:AWSECSCluster
        OR resource:AWSRDSInstance
        OR resource:AWSRDSCluster
      )
    WITH DISTINCT account, resource.region AS region
    WHERE NOT EXISTS {
        MATCH (account)-[:RESOURCE]->(hub:AWSSecurityHub)
        WHERE split(hub.id, ':')[3] = region
    }
    RETURN account
    """,
    cypher_count_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(resource)
    WHERE resource.region IS NOT NULL
      AND (
        resource:AWSEC2Instance
        OR resource:AWSEKSCluster
        OR resource:AWSLambda
        OR resource:AWSECSCluster
        OR resource:AWSRDSInstance
        OR resource:AWSRDSCluster
      )
    WITH DISTINCT account, resource.region AS region
    RETURN COUNT(DISTINCT account) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "region", "gap_type"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


_aws_security_hub_controls_not_auto_enabled = Fact(
    id="aws_security_hub_controls_not_auto_enabled",
    name="AWS Security Hub controls not automatically enabled",
    description=(
        "Detects Security Hub subscriptions that do not automatically enable new "
        "controls."
    ),
    cypher_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(hub:AWSSecurityHub)
    WHERE coalesce(hub.auto_enable_controls, false) = false
    RETURN
        account.name AS account_name,
        account.id AS account_id,
        split(hub.id, ':')[3] AS region,
        'controls_not_auto_enabled' AS gap_type,
        hub.auto_enable_controls AS auto_enable_controls
    """,
    cypher_visual_query="""
    MATCH p=(account:AWSAccount)-[:RESOURCE]->(hub:AWSSecurityHub)
    WHERE coalesce(hub.auto_enable_controls, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (account:AWSAccount)-[:RESOURCE]->(:AWSSecurityHub)
    RETURN COUNT(DISTINCT account) AS count
    """,
    asset_label="AWSAccount",
    asset_id_field="account_id",
    identity_fields=("account_id", "region", "gap_type"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_security_hub_configuration_gaps = Rule(
    id="aws_security_hub_configuration_gaps",
    name="AWS Security Hub Configuration Gaps",
    description=(
        "Detects active AWS regions without Security Hub and subscriptions that "
        "do not automatically enable new controls."
    ),
    output_model=AWSSecurityHubConfigurationGapOutput,
    facts=(
        _aws_security_hub_missing,
        _aws_security_hub_controls_not_auto_enabled,
    ),
    tags=("aws", "security_hub", "monitoring", "vulnerability_management"),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.8"),
        iso27001_annex_a("8.16"),
        soc2_tsc("CC7.1"),
        soc2_tsc("CC7.2"),
    ),
)


# --- RDS event subscriptions ---
#
# RDS event subscriptions are how maintenance, failure and configuration changes
# reach an operator. These are absence checks: the subject is the account, and it
# fails when no enabled subscription of the required source type covers the
# critical categories. An empty ``event_categories`` list means all categories,
# so it satisfies every check.


class AwsRdsClusterCriticalEventSubscriptionOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_rds_cluster_critical_event_subscription_fact = Fact(
    id="aws_rds_cluster_critical_event_subscription_fact",
    name="RDS db-cluster event subscription coverage",
    description="Accounts with no enabled AWSRDSEventSubscription of source_type 'db-cluster' whose event_categories include 'maintenance', 'failure'. A NULL/empty event_categories list means all categories and passes. source_ids scoping is not evaluated (best-effort).",
    cypher_query="""
        MATCH (a:AWSAccount {inscope:true})
        OPTIONAL MATCH (a)-[:RESOURCE]->(sub:AWSRDSEventSubscription)
        WHERE sub.source_type = 'db-cluster'
          AND coalesce(sub.enabled, false) = true
          AND (sub.event_categories IS NULL
               OR size(sub.event_categories) = 0
               OR ('maintenance' IN sub.event_categories AND 'failure' IN sub.event_categories))
        WITH a, count(sub) AS qualifying
        WHERE qualifying = 0
        RETURN a.id AS account_id, a.name AS account

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount {inscope:true})
        OPTIONAL MATCH (a)-[:RESOURCE]->(sub:AWSRDSEventSubscription)
        WHERE sub.source_type = 'db-cluster'
          AND coalesce(sub.enabled, false) = true
          AND (sub.event_categories IS NULL
               OR size(sub.event_categories) = 0
               OR ('maintenance' IN sub.event_categories AND 'failure' IN sub.event_categories))
        WITH a, count(sub) AS qualifying
        WHERE qualifying = 0
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


aws_rds_cluster_critical_event_subscription = Rule(
    id="aws_rds_cluster_critical_event_subscription",
    name="RDS Cluster Critical Event Subscription",
    description="No enabled RDS event subscription with source_type='db-cluster' covers the critical event categories 'maintenance', 'failure'. Account-level negative check: the failing asset is the account (asset_label AWSAccount, count totals accounts); subscription data is read from AWSRDSEventSubscription. An empty/NULL event_categories list means all categories and passes. Subscription source_ids scoping is not evaluated.",
    output_model=AwsRdsClusterCriticalEventSubscriptionOutput,
    facts=(_aws_rds_cluster_critical_event_subscription_fact,),
    tags=("security", "rds", "monitoring", "cspm"),
    version="0.1.0",
)


class AwsRdsInstanceCriticalEventSubscriptionOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_rds_instance_critical_event_subscription_fact = Fact(
    id="aws_rds_instance_critical_event_subscription_fact",
    name="RDS db-instance event subscription coverage",
    description="Accounts with no enabled AWSRDSEventSubscription of source_type 'db-instance' whose event_categories include 'maintenance', 'configuration change', 'failure'. A NULL/empty event_categories list means all categories and passes. source_ids scoping is not evaluated (best-effort).",
    cypher_query="""
        MATCH (a:AWSAccount {inscope:true})
        OPTIONAL MATCH (a)-[:RESOURCE]->(sub:AWSRDSEventSubscription)
        WHERE sub.source_type = 'db-instance'
          AND coalesce(sub.enabled, false) = true
          AND (sub.event_categories IS NULL
               OR size(sub.event_categories) = 0
               OR ('maintenance' IN sub.event_categories AND 'configuration change' IN sub.event_categories AND 'failure' IN sub.event_categories))
        WITH a, count(sub) AS qualifying
        WHERE qualifying = 0
        RETURN a.id AS account_id, a.name AS account

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount {inscope:true})
        OPTIONAL MATCH (a)-[:RESOURCE]->(sub:AWSRDSEventSubscription)
        WHERE sub.source_type = 'db-instance'
          AND coalesce(sub.enabled, false) = true
          AND (sub.event_categories IS NULL
               OR size(sub.event_categories) = 0
               OR ('maintenance' IN sub.event_categories AND 'configuration change' IN sub.event_categories AND 'failure' IN sub.event_categories))
        WITH a, count(sub) AS qualifying
        WHERE qualifying = 0
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


aws_rds_instance_critical_event_subscription = Rule(
    id="aws_rds_instance_critical_event_subscription",
    name="RDS Instance Critical Event Subscription",
    description="No enabled RDS event subscription with source_type='db-instance' covers the critical event categories 'maintenance', 'configuration change', 'failure'. Account-level negative check: the failing asset is the account (asset_label AWSAccount, count totals accounts); subscription data is read from AWSRDSEventSubscription. An empty/NULL event_categories list means all categories and passes. Subscription source_ids scoping is not evaluated.",
    output_model=AwsRdsInstanceCriticalEventSubscriptionOutput,
    facts=(_aws_rds_instance_critical_event_subscription_fact,),
    tags=("security", "rds", "monitoring", "cspm"),
    version="0.1.0",
)


class AwsRdsInstanceEventSubscriptionParameterGroupsOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_rds_instance_event_subscription_parameter_groups_fact = Fact(
    id="aws_rds_instance_event_subscription_parameter_groups_fact",
    name="No enabled db-parameter-group configuration-change subscription",
    description="Accounts lacking a qualifying enabled RDS event subscription.",
    cypher_query="""
        MATCH (a:AWSAccount {inscope:true})
        OPTIONAL MATCH (a)-[:RESOURCE]->(sub:AWSRDSEventSubscription)
        WHERE sub.enabled = true
          AND sub.source_type = 'db-parameter-group'
          AND (sub.event_categories IS NULL
               OR size(sub.event_categories) = 0
               OR 'configuration change' IN sub.event_categories)
        WITH a, sub
        WHERE sub IS NULL
        RETURN a.id AS account_id, a.name AS account

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount {inscope:true})
        OPTIONAL MATCH (a)-[:RESOURCE]->(sub:AWSRDSEventSubscription)
        WHERE sub.enabled = true
          AND sub.source_type = 'db-parameter-group'
          AND (sub.event_categories IS NULL
               OR size(sub.event_categories) = 0
               OR 'configuration change' IN sub.event_categories)
        WITH a, sub
        WHERE sub IS NULL
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


aws_rds_instance_event_subscription_parameter_groups = Rule(
    id="aws_rds_instance_event_subscription_parameter_groups",
    name="No DB Parameter Group Event Subscription",
    description="Account has no enabled RDS event subscription with source_type='db-parameter-group' covering 'configuration change' events (an empty event_categories list means all categories and also qualifies). LIMITATION: absence check, so assessed at AWSAccount (spec asset_label AWSRDSEventSubscription); this rule is account-scoped rather than per-region; subscriptions with an empty source_type (all sources) are not counted; ingestion of db-parameter-group subscriptions is unverified.",
    output_model=AwsRdsInstanceEventSubscriptionParameterGroupsOutput,
    facts=(_aws_rds_instance_event_subscription_parameter_groups_fact,),
    tags=("rds", "observability", "cspm", "low", "best-effort"),
    version="0.1.0",
)


class AwsRdsInstanceEventSubscriptionSecurityGroupsOutput(Finding):
    account_id: str | None = None
    account: str | None = None


_aws_rds_instance_event_subscription_security_groups_fact = Fact(
    id="aws_rds_instance_event_subscription_security_groups_fact",
    name="RDS db-security-group event subscription coverage",
    description="Accounts with no enabled AWSRDSEventSubscription of source_type 'db-security-group' whose event_categories include 'configuration change', 'failure'. A NULL/empty event_categories list means all categories and passes. source_ids scoping is not evaluated (best-effort).",
    cypher_query="""
        MATCH (a:AWSAccount {inscope:true})
        OPTIONAL MATCH (a)-[:RESOURCE]->(sub:AWSRDSEventSubscription)
        WHERE sub.source_type = 'db-security-group'
          AND coalesce(sub.enabled, false) = true
          AND (sub.event_categories IS NULL
               OR size(sub.event_categories) = 0
               OR ('configuration change' IN sub.event_categories AND 'failure' IN sub.event_categories))
        WITH a, count(sub) AS qualifying
        WHERE qualifying = 0
        RETURN a.id AS account_id, a.name AS account

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount {inscope:true})
        OPTIONAL MATCH (a)-[:RESOURCE]->(sub:AWSRDSEventSubscription)
        WHERE sub.source_type = 'db-security-group'
          AND coalesce(sub.enabled, false) = true
          AND (sub.event_categories IS NULL
               OR size(sub.event_categories) = 0
               OR ('configuration change' IN sub.event_categories AND 'failure' IN sub.event_categories))
        WITH a, count(sub) AS qualifying
        WHERE qualifying = 0
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


aws_rds_instance_event_subscription_security_groups = Rule(
    id="aws_rds_instance_event_subscription_security_groups",
    name="RDS Security Group Critical Event Subscription",
    description="No enabled RDS event subscription with source_type='db-security-group' covers the critical event categories 'configuration change', 'failure'. Account-level negative check: the failing asset is the account (asset_label AWSAccount, count totals accounts); subscription data is read from AWSRDSEventSubscription. An empty/NULL event_categories list means all categories and passes. Subscription source_ids scoping is not evaluated.",
    output_model=AwsRdsInstanceEventSubscriptionSecurityGroupsOutput,
    facts=(_aws_rds_instance_event_subscription_security_groups_fact,),
    tags=("security", "rds", "monitoring", "cspm"),
    version="0.1.0",
)
