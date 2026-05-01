from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# GCP Facts
_gcp_instance_internet_exposed = Fact(
    id="gcp_instance_internet_exposed",
    name="Internet-Exposed GCE Instances on Common Management Ports",
    description=(
        "GCE instances with a public IP (ONE_TO_ONE_NAT access config) whose "
        "VPC has an enabled INGRESS firewall allowing 0.0.0.0/0 on TCP (or "
        "all protocols) to a management port (22, 3389, 3306, 5432, 6379, "
        "9200, 27017). Port ranges (fromport/toport) covering a management "
        "port are detected. Mirrors the AWS EC2-on-management-ports "
        "semantics; matches are widened by VPC scope and do not currently "
        "account for firewall target_tags or target SAs, so a VPC-wide "
        "allow may produce findings on tagged instances that the firewall "
        "does not actually apply to."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (nic:GCPNetworkInterface)-[:NETWORK_INTERFACE]-(instance)
    MATCH (ac:GCPNicAccessConfig)-[:RESOURCE]-(nic)
    MATCH (nic)-[:PART_OF_SUBNET]->(subnet:GCPSubnet)<-[:HAS]-(vpc:GCPVpc)
    MATCH (vpc)-[:RESOURCE]->(fw:GCPFirewall)<-[:ALLOWED_BY]-(rule:GCPIpRule)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:GCPIpRange{range:'0.0.0.0/0'})
    WITH project, instance, nic, ac, fw, rule
    UNWIND [22, 3389, 3306, 5432, 6379, 9200, 27017] AS managed_port
    WITH project, instance, nic, ac, fw, rule, managed_port
    WHERE ac.type = 'ONE_TO_ONE_NAT'
      AND ac.public_ip IS NOT NULL
      AND coalesce(fw.disabled, false) = false
      AND fw.direction = 'INGRESS'
      AND (
        rule.protocol = 'all'
        OR (
          rule.protocol = 'tcp'
          AND coalesce(rule.fromport, 0) <= managed_port
          AND coalesce(rule.toport, rule.fromport, 0) >= managed_port
        )
      )
    RETURN
        project.id AS account_id,
        project.id AS account,
        instance.id AS instance_id,
        instance.name AS instance,
        managed_port AS port,
        fw.name AS security_group
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH p2=(nic:GCPNetworkInterface)-[:NETWORK_INTERFACE]-(instance)
    MATCH p3=(ac:GCPNicAccessConfig)-[:RESOURCE]-(nic)
    MATCH p4=(nic)-[:PART_OF_SUBNET]->(subnet:GCPSubnet)<-[:HAS]-(vpc:GCPVpc)
    MATCH p5=(vpc)-[:RESOURCE]->(fw:GCPFirewall)<-[:ALLOWED_BY]-(rule:GCPIpRule)
    MATCH p6=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:GCPIpRange{range:'0.0.0.0/0'})
    WHERE ac.type = 'ONE_TO_ONE_NAT'
      AND ac.public_ip IS NOT NULL
      AND coalesce(fw.disabled, false) = false
      AND fw.direction = 'INGRESS'
      AND (
        rule.protocol = 'all'
        OR (
          rule.protocol = 'tcp'
          AND any(
            managed_port IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
            WHERE coalesce(rule.fromport, 0) <= managed_port
              AND coalesce(rule.toport, rule.fromport, 0) >= managed_port
          )
        )
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


# AWS Facts
_aws_ec2_instance_internet_exposed = Fact(
    id="aws_ec2_instance_internet_exposed",
    name="Internet-Exposed EC2 Instances on Common Management Ports",
    description=(
        "EC2 instances exposed to the internet on ports 22, 3389, 3306, 5432, 6379, 9200, 27017"
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange{range:'0.0.0.0/0'})
    WHERE rule.fromport IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
    RETURN a.id as account_id, a.name AS account, ec2.instanceid AS instance_id, rule.fromport AS port, sg.groupid AS security_group order by account, instance_id, port, security_group
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
    MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange{range:'0.0.0.0/0'})
    WHERE rule.fromport IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:EC2Instance)
    RETURN COUNT(ec2) AS count
    """,
    asset_id_field="instance_id",
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
    name="Internet-Exposed Compute Instances on Common Management Ports",
    description=(
        "Compute instances exposed to the internet on ports 22, 3389, 3306, 5432, 6379, 9200, 27017"
    ),
    output_model=ComputeInstanceExposed,
    facts=(
        _aws_ec2_instance_internet_exposed,
        _gcp_instance_internet_exposed,
    ),
    tags=(
        "infrastructure",
        "compute",
        "attack_surface",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
)
