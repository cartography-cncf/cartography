from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Module

aws_rds_public_access = Fact(
    id="aws_rds_public_access",
    name="Internet-Accessible RDS Database Attack Surface",
    description="AWS RDS instances accessible from the internet",
    cypher_query="""
    MATCH (rds:RDSInstance)
    WHERE rds.publicly_accessible = true
    RETURN rds.id AS instance_id,
           rds.engine AS engine,
           rds.db_instance_class AS instance_class,
           rds.endpoint_address AS endpoint,
           rds.endpoint_port AS port,
           rds.region AS region,
           rds.storage_encrypted AS encrypted
    """,
    cypher_visual_query="""
    MATCH p1=(rds:RDSInstance{publicly_accessible: true})
    OPTIONAL MATCH p2=(rds)--(sg:EC2SecurityGroup)
    OPTIONAL MATCH p3=(rds)--(sg:EC2SecurityGroup)--(rule:IpPermissionInbound:IpRule)
    OPTIONAL MATCH p4=(rds)--(sg:EC2SecurityGroup)--(rule:IpPermissionInbound:IpRule)--(ip:IpRange)
    RETURN *
    """,
    module=Module.AWS,
)
