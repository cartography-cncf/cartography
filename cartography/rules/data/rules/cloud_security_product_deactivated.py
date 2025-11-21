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
    name="Cloud Security Product Deactivated",
    description="Detects accounts (or regions) where cloud security products are deactivated.",
    output_model=CloudSecurityProductDeactivated,
    tags=("cloud_security",),
    facts=(aws_guard_duty_detector_disabled,),
    version="0.1.0",
)
