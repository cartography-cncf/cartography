from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.soc2 import soc2_tsc
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS
aws_guard_duty_detector_disabled = Fact(
    id="aws_guard_duty_detector_disabled",
    name="GuardDuty Detector Disabled",
    description="Finds regions where GuardDuty Detector is disabled.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]-(r:AWSEC2Instance|AWSEKSCluster|AWSLambda|AWSECSCluster|AWSRDSInstance|AWSRDSCluster)
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(d:AWSGuardDutyDetector{status: "ENABLED"})
        WHERE d.region = r.region
    }
    RETURN DISTINCT r.region AS region, a.name AS account_name, a.id AS account_id
    ORDER BY r.region, a.name
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]-(r:AWSEC2Instance|AWSEKSCluster|AWSLambda|AWSECSCluster|AWSRDSInstance|AWSRDSCluster)
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(d:AWSGuardDutyDetector{status: "ENABLED"})
        WHERE d.region = r.region
    }
    RETURN *
    """,
    cypher_count_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]-(r:AWSEC2Instance|AWSEKSCluster|AWSLambda|AWSECSCluster|AWSRDSInstance|AWSRDSCluster)
    WITH DISTINCT a, r.region AS region
    RETURN COUNT(*) AS count
    """,
    identity_fields=("account_id", "region"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class CloudSecurityProductDeactivated(Finding):
    account_name: str | None = None
    region: str | None = None
    account_id: str | None = None


cloud_security_product_deactivated = Rule(
    id="cloud_security_product_deactivated",
    name="Cloud Security Product Deactivated",
    description="Detects accounts (or regions) where cloud security products are deactivated.",
    output_model=CloudSecurityProductDeactivated,
    tags=(
        "cloud_security",
        "stride:information_disclosure",
        "stride:tampering",
        "stride:elevation_of_privilege",
    ),
    facts=(aws_guard_duty_detector_disabled,),
    version="0.1.0",
    frameworks=(
        iso27001_annex_a("8.16"),
        soc2_tsc("CC7.2"),
    ),
)


# =============================================================================
# TODO: SOC 2 CC7.2: Partial anomaly-monitoring coverage
# Covered today: GuardDuty detector state and active findings, CloudTrail
# configuration, GCP VPC flow logs and Tailscale network flow logging. That is
# whether logging and detection are switched on, not whether anomalies are
# analyzed.
# Already in the graph but unused by any rule: AWSEventBridgeRule and its targets,
# AWSConfigurationRecorder, AWSConfigDeliveryChannel, AWSConfigRule,
# AWSSecurityHub, AWSCloudWatchMetricAlarm, AzureMonitorMetricAlert and
# AzureSecurityAssessment. Alert-rule and detector configuration for AWS and Azure
# is therefore queryable today, without new ingestion.
# Missing datamodel: Google Security Command Center inventory, per-account and
# per-region log-source coverage, and alert-delivery health.
# =============================================================================
