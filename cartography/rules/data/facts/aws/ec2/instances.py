from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Module

aws_ec2_instance_internet_exposed = Fact(
    id="aws_ec2_instance_internet_exposed",
    name="Internet-Exposed EC2 Instances on Common Management Ports",
    description=(
        "EC2 instances exposed to the internet on ports 22, 3389, 3306, 5432, 6379, 9200, 27017"
    ),
    cypher_query="""
    MATCH (a:AWSAccount)--(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:IpRange{range:'0.0.0.0/0'})
    WHERE rule.fromport IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
    RETURN a.name AS account, ec2.instanceid AS instance, rule.fromport AS port, sg.groupid AS sg order by account, instance, port, sg
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)--(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
    MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:IpRange{range:'0.0.0.0/0'})
    WHERE rule.fromport IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
    RETURN *
    """,
    module=Module.AWS,
)
