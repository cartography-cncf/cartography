from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# AWS Facts
_aws_rds_public_access = Fact(
    id="aws_rds_public_access",
    name="AWS RDS Instances with Public Accessibility Enabled",
    description=(
        "Finds AWS RDS database instances that have the 'publicly_accessible' configuration flag set to true, "
        "allowing the instance to receive connections from the internet. Returns instance details including "
        "database engine, instance class, endpoint address/port, region, and encryption status."
    ),
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
    name="Internet-Exposed Database Instances",
    description=(
        "Detects managed database instances configured to be publicly accessible from the internet. Public "
        "database exposure creates direct attack paths for unauthorized access, data breaches, ransomware, and "
        "data exfiltration. Publicly accessible databases are frequently targeted by automated scanners, credential "
        "brute-forcing, and exploitation of unpatched vulnerabilities. Even with authentication enabled, public "
        "database exposure violates security best practices and significantly increases risk. Databases should be "
        "deployed in private subnets with access restricted through application layers, bastion hosts, VPNs, or "
        "private connectivity solutions. Currently detects AWS RDS instances with public accessibility enabled. "
        "Future detection will expand to Azure SQL Database, Azure Database for MySQL/PostgreSQL, GCP Cloud SQL, "
        "GCP Cloud Spanner, and other managed database services across all major cloud providers."
    ),
    output_model=DatabaseInstanceExposed,
    facts=(_aws_rds_public_access,),
    tags=("infrastructure", "databases", "attack_surface"),
    version="0.2.0",
    references=[
        RuleReference(
            text="AWS - RDS Public Accessibility Guidance",
            url="https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PublicAccessible.html",
        ),
        RuleReference(
            text="GCP - Cloud SQL: Private IP vs Public IP - Security Recommendations",
            url="https://cloud.google.com/sql/docs/mysql/private-ip",
        ),
        RuleReference(
            text="Azure - Security recommendations for Azure Database Services",
            url="https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-security",
        ),
        RuleReference(
            text="Azure - Restrict Public Network Access for PaaS Databases",
            url="https://learn.microsoft.com/en-us/azure/azure-sql/managed-instance/public-endpoint-overview?view=azuresql",
        ),
    ],
)
