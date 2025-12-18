"""
CIS AWS Networking Security Checks

Implements CIS AWS Foundations Benchmark Section 5: Networking
Based on CIS AWS Foundations Benchmark v5.0

Each Fact represents a specific CIS check that can be performed against
Neo4j data synced by Cartography.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

# -----------------------------------------------------------------------------
# CIS 5.1: Ensure no security groups allow ingress from 0.0.0.0/0 to remote
# server administration ports (SSH - port 22)
# -----------------------------------------------------------------------------
_cis_5_1_unrestricted_ssh = Fact(
    id="cis_5_1_unrestricted_ssh",
    name="CIS 5.1: Security groups allow unrestricted SSH access",
    description=(
        "Detects security groups that allow SSH access (port 22) from any IP address "
        "(0.0.0.0/0 or ::/0). Unrestricted SSH access increases the risk of "
        "unauthorized access and brute force attacks."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:IpRange)
    WHERE (range.id = '0.0.0.0/0' OR range.id = '::/0')
      AND (
          (rule.fromport <= 22 AND rule.toport >= 22)
          OR rule.protocol = '-1'
      )
    RETURN
        sg.groupid AS security_group_id,
        sg.name AS security_group_name,
        sg.region AS region,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        rule.protocol AS protocol,
        range.id AS cidr_range,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:IpRange)
    WHERE (range.id = '0.0.0.0/0' OR range.id = '::/0')
      AND (
          (rule.fromport <= 22 AND rule.toport >= 22)
          OR rule.protocol = '-1'
      )
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 5.2: Ensure no security groups allow ingress from 0.0.0.0/0 to remote
# server administration ports (RDP - port 3389)
# -----------------------------------------------------------------------------
_cis_5_2_unrestricted_rdp = Fact(
    id="cis_5_2_unrestricted_rdp",
    name="CIS 5.2: Security groups allow unrestricted RDP access",
    description=(
        "Detects security groups that allow RDP access (port 3389) from any IP address "
        "(0.0.0.0/0 or ::/0). Unrestricted RDP access increases the risk of "
        "unauthorized access and brute force attacks on Windows systems."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:IpRange)
    WHERE (range.id = '0.0.0.0/0' OR range.id = '::/0')
      AND (
          (rule.fromport <= 3389 AND rule.toport >= 3389)
          OR rule.protocol = '-1'
      )
    RETURN
        sg.groupid AS security_group_id,
        sg.name AS security_group_name,
        sg.region AS region,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        rule.protocol AS protocol,
        range.id AS cidr_range,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:IpRange)
    WHERE (range.id = '0.0.0.0/0' OR range.id = '::/0')
      AND (
          (rule.fromport <= 3389 AND rule.toport >= 3389)
          OR rule.protocol = '-1'
      )
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# CIS 5.4: Ensure the default security group of every VPC restricts all traffic
# -----------------------------------------------------------------------------
_cis_5_4_default_sg_allows_traffic = Fact(
    id="cis_5_4_default_sg_allows_traffic",
    name="CIS 5.4: Default security group allows traffic",
    description=(
        "Detects VPCs where the default security group has inbound or outbound rules "
        "allowing traffic. The default security group should restrict all traffic "
        "to prevent accidental exposure of resources."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
    WHERE sg.name = 'default'
    RETURN DISTINCT
        sg.groupid AS security_group_id,
        sg.name AS security_group_name,
        sg.region AS region,
        'inbound' AS rule_direction,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        rule.protocol AS protocol,
        a.id AS account_id,
        a.name AS account
    UNION
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionEgress)
    WHERE sg.name = 'default'
    RETURN DISTINCT
        sg.groupid AS security_group_id,
        sg.name AS security_group_name,
        sg.region AS region,
        'egress' AS rule_direction,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        rule.protocol AS protocol,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpRule)
    WHERE sg.name = 'default'
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# Additional: Security groups with unrestricted ingress on all ports
# -----------------------------------------------------------------------------
_unrestricted_all_ports = Fact(
    id="cis_aws_unrestricted_all_ports",
    name="Security groups with unrestricted access to all ports",
    description=(
        "Detects security groups that allow access to all ports from any IP address "
        "(0.0.0.0/0 or ::/0). This is a severe misconfiguration that exposes all "
        "services to the internet."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:IpRange)
    WHERE (range.id = '0.0.0.0/0' OR range.id = '::/0')
      AND rule.protocol = '-1'
    RETURN
        sg.groupid AS security_group_id,
        sg.name AS security_group_name,
        sg.region AS region,
        rule.protocol AS protocol,
        range.id AS cidr_range,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:IpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:IpRange)
    WHERE (range.id = '0.0.0.0/0' OR range.id = '::/0')
      AND rule.protocol = '-1'
    RETURN *
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)


# -----------------------------------------------------------------------------
# Output Model
# -----------------------------------------------------------------------------
class CISAWSNetworkingOutput(Finding):
    """Output model for CIS AWS Networking checks.

    Field order matters for display_name: first non-null field is used.
    Most specific identifiers should come first.
    """

    # Primary identifier (first non-null becomes display_name)
    security_group_id: str | None = None
    # Security group details
    security_group_name: str | None = None
    region: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    rule_direction: str | None = None
    # Account (last - generic identifier)
    account_id: str | None = None
    account: str | None = None


# -----------------------------------------------------------------------------
# Rule Definition
# -----------------------------------------------------------------------------
cis_aws_networking = Rule(
    id="cis_aws_networking",
    name="CIS AWS Networking Security Checks",
    description=(
        "CIS AWS Foundations Benchmark - Networking controls. "
        "Detects security group misconfigurations including unrestricted SSH, "
        "RDP, and overly permissive default security groups."
    ),
    output_model=CISAWSNetworkingOutput,
    facts=(
        _cis_5_1_unrestricted_ssh,
        _cis_5_2_unrestricted_rdp,
        _cis_5_4_default_sg_allows_traffic,
        _unrestricted_all_ports,
    ),
    tags=("cis", "compliance", "cis_aws_5.0", "networking", "security-groups"),
    version="1.0.0",
    references=[
        RuleReference(
            text="CIS AWS Foundations Benchmark v5.0",
            url="https://www.cisecurity.org/benchmark/amazon_web_services",
        ),
        RuleReference(
            text="AWS Security Group Best Practices",
            url="https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html",
        ),
    ],
)
