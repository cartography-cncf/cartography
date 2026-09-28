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
