from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module

# AWS Facts
_aws_rds_public_access = Fact(
    id="aws_rds_public_access",
    name="Internet-Accessible RDS Database Attack Surface",
    description="AWS RDS instances accessible from the internet",
    cypher_query="""
    MATCH (rds:RDSInstance)
    OPTIONAL MATCH p2=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
    OPTIONAL MATCH p3=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound:IpRule)
    OPTIONAL MATCH p4=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound:IpRule)<-[:MEMBER_OF_IP_RULE]-(ip:IpRange)
    WHERE rds.publicly_accessible = true
    RETURN rds, sg, rule, ip
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Finding
database_instance_exposed = Finding(
    id="database_instance_exposed",
    name="Internet-Exposed Databases",
    description=("Database instances accessible from the internet"),
    facts=(_aws_rds_public_access,),
    tags=("infrastructure", "databases", "attack_surface"),
    version="0.1.0",
)
