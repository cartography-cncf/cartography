from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# AWS
aws_guard_duty_detector_disabled = Fact(
    id="aws_guard_duty_detector_disabled",
    name="AWS Regions with Disabled GuardDuty Detectors",
    description=(
        "Finds AWS regions that contain active resources (EC2 instances, EKS clusters, Lambda functions, "
        "ECS clusters, RDS instances/clusters) but do not have an enabled GuardDuty detector for threat "
        "monitoring and security event detection."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]-(r:EC2Instance|EKSCluster|AWSLambda|ECSCluster|RDSInstance|RDSCluster)
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(d:GuardDutyDetector{status: "ENABLED"})
        WHERE d.region = r.region
    }
    RETURN DISTINCT r.region AS region, a.name AS account_name, a.id AS account_id
    ORDER BY r.region, a.name
    """,
    cypher_visual_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]-(r:EC2Instance|EKSCluster|AWSLambda|ECSCluster|RDSInstance|RDSCluster)
    WHERE NOT EXISTS {
        MATCH (a)-[:RESOURCE]->(d:GuardDutyDetector{status: "ENABLED"})
        WHERE d.region = r.region
    }
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class CloudSecurityProductDeactivated(Finding):
    region: str | None = None
    account_name: str | None = None
    account_id: str | None = None


cloud_security_product_deactivated = Rule(
    id="cloud_security_product_deactivated",
    name="Cloud-Native Security Products Disabled",
    description=(
        "Detects cloud accounts, subscriptions, projects, or regions where critical cloud-native threat detection "
        "and monitoring services are disabled. When disabled in environments with active workloads, organizations "
        "lose visibility into compromised instances, credential theft, cryptocurrency mining, data exfiltration, "
        "lateral movement, and other attacks. Organizations should enable these services in all regions/projects "
        "with production workloads and enforce enablement through infrastructure-as-code."
    ),
    output_model=CloudSecurityProductDeactivated,
    tags=("cloud_security", "monitoring", "threat_detection"),
    facts=(aws_guard_duty_detector_disabled,),
    version="0.2.0",
    references=[
        RuleReference(
            text="AWS - GuardDuty Documentation (continuous threat detection)",
            url="https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html",
        ),
        RuleReference(
            text="Azure - Microsoft Defender for Cloud (cloud-native threat detection)",
            url="https://learn.microsoft.com/en-us/azure/defender-for-cloud/defender-for-cloud-introduction",
        ),
        RuleReference(
            text="GCP - Best practices for enterprise organizations (visibility & monitoring)",
            url="https://cloud.google.com/architecture/framework/security",
        ),
    ],
)
