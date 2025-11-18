from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# AWS Facts
_aws_rds_public_access = Fact(
    id="aws_rds_public_access",
    name="Internet-Accessible RDS Database Attack Surface",
    description="AWS RDS instances accessible from the internet",
    cypher_query="""
    MATCH (rds:RDSInstance)
    WHERE rds.publicly_accessible = true
    RETURN rds.id AS id,
        rds.engine AS engine,
        rds.db_instance_class AS instance_class,
        rds.endpoint_address AS host,
        rds.endpoint_port AS port,
        rds.region AS region,
        rds.storage_encrypted AS encrypted
    """,
    cypher_visual_query="""
    MATCH p1=(rds:RDSInstance{publicly_accessible: true})
    OPTIONAL MATCH p2=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
    OPTIONAL MATCH p3=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound:IpRule)
    OPTIONAL MATCH p4=(rds)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound:IpRule)<-[:MEMBER_OF_IP_RULE]-(ip:IpRange)
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class DatabaseInstanceExposed(Finding):
    host: str | None = None
    id: str | None = None
    engine: str | None = None
    port: int | None = None
    region: str | None = None
    encrypted: bool | None = None


database_instance_exposed = Rule(
    id="database_instance_exposed",
    name="Internet-Exposed Databases",
    description=("Database instances accessible from the internet"),
    output_model=DatabaseInstanceExposed,
    facts=(_aws_rds_public_access,),
    tags=("infrastructure", "databases", "attack_surface"),
    version="0.1.0",
)
