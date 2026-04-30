from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# GCP Facts
_gcp_instance_internet_exposed = Fact(
    id="gcp_instance_internet_exposed",
    name="Internet-Exposed GCE Instances",
    description=(
        "GCE instances with at least one network interface that has an external "
        "IP attached via a ONE_TO_ONE_NAT access config, exposing them to the "
        "public internet."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]-(nic:GCPNetworkInterface)-[:RESOURCE]-(ac:GCPNicAccessConfig)
    WHERE ac.type = 'ONE_TO_ONE_NAT' AND ac.public_ip IS NOT NULL
    RETURN
        project.id AS account_id,
        project.id AS account,
        instance.id AS instance_id,
        instance.name AS instance,
        ac.public_ip AS host,
        nic.name AS security_group
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH p2=(instance)-[:NETWORK_INTERFACE]-(nic:GCPNetworkInterface)-[:RESOURCE]-(ac:GCPNicAccessConfig)
    WHERE ac.type = 'ONE_TO_ONE_NAT' AND ac.public_ip IS NOT NULL
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
