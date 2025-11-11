from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

# AWS Facts
_aws_ec2_instance_internet_exposed = Fact(
    id="aws_ec2_instance_internet_exposed",
    name="Internet-Exposed EC2 Instances on Common Management Ports",
    description=(
        "EC2 instances exposed to the internet on ports 22, 3389, 3306, 5432, 6379, 9200, 27017"
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:IpRange{range:'0.0.0.0/0'})
    WHERE rule.fromport IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
    RETURN ec2, a, sg, rule, ip
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Finding
compute_instance_exposed = Finding(
    id="compute_instance_exposed",
    name="Internet-Exposed Compute Instances on Common Management Ports",
    description=(
        "Compute instances exposed to the internet on ports 22, 3389, 3306, 5432, 6379, 9200, 27017"
    ),
    facts=(_aws_ec2_instance_internet_exposed,),
    tags=("infrastructure", "compute", "attack_surface"),
    version="0.1.0",
)
