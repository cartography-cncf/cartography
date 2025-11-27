from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# AWS Facts
_aws_ec2_instance_internet_exposed = Fact(
    id="aws_ec2_instance_internet_exposed",
    name="AWS EC2 Instances Exposed on Management and Database Ports",
    description=(
        "Finds AWS EC2 instances with security group rules that allow unrestricted internet access "
        "(0.0.0.0/0) on management ports (SSH 22, RDP 3389) and database ports (MySQL 3306, "
        "PostgreSQL 5432, Redis 6379, Elasticsearch 9200, MongoDB 27017)."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:IpRange{range:'0.0.0.0/0'})
    WHERE rule.fromport IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
    RETURN a.id as account_id, a.name AS account, ec2.instanceid AS instance_id, rule.fromport AS port, sg.groupid AS security_group order by account, instance_id, port, security_group
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
    MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:IpRange{range:'0.0.0.0/0'})
    WHERE rule.fromport IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class ComputeInstanceExposed(Finding):
    instance: str | None = None
    instance_id: str | None = None
    account: str | None = None
    account_id: str | None = None
    port: int | None = None
    security_group: str | None = None


compute_instance_exposed = Rule(
    id="compute_instance_exposed",
    name="Compute Instances Exposed on Management and Database Ports",
    description=(
        "Detects compute instances (EC2, etc.) directly exposed to the internet (0.0.0.0/0) on common "
        "management and database ports. These instances allow unrestricted access on critical ports "
        "including SSH (22), RDP (3389), MySQL (3306), PostgreSQL (5432), Redis (6379), Elasticsearch "
        "(9200), and MongoDB (27017). Direct internet exposure on these ports significantly increases "
        "the attack surface and creates high risk for unauthorized access, brute-force attacks, "
        "credential stuffing, data breaches, and lateral movement. Best practice is to restrict access "
        "to specific IP ranges, use bastion hosts/jump servers for management access, or implement "
        "VPN/Zero Trust solutions for administrative connectivity."
    ),
    output_model=ComputeInstanceExposed,
    facts=(_aws_ec2_instance_internet_exposed,),
    tags=("infrastructure", "compute", "attack_surface"),
    version="0.2.0",
    references=[
        RuleReference(
            text="CISA - BOD 23-02 Mitigating the Risk from Internet-Exposed Management Interfaces",
            url="https://www.cisa.gov/news-events/directives/binding-operational-directive-23-02",
        ),
        RuleReference(
            text="AWS - Security control recommendations for protecting infrastructure (unrestricted access from 0.0.0.0/0)",
            url="https://docs.aws.amazon.com/prescriptive-guidance/latest/security-controls-by-caf-capability/infrastructure-controls.html",
        ),
        RuleReference(
            text="GCP - Best practices for controlling SSH network access",
            url="https://docs.cloud.google.com/compute/docs/connect/ssh-best-practices/network-access",
        ),
        RuleReference(
            text="OWASP - Secure Cloud Architecture Cheat Sheet",
            url="https://cheatsheetseries.owasp.org/cheatsheets/Secure_Cloud_Architecture_Cheat_Sheet.html",
        ),
    ],
)
