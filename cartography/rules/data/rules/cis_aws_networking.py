"""
CIS AWS Networking Security Checks

Implements CIS AWS Foundations Benchmark Section 5: Networking
Based on CIS AWS Foundations Benchmark v5.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS AWS Foundations Benchmark v5.0",
        url="https://www.cisecurity.org/benchmark/amazon_web_services",
    ),
    RuleReference(
        text="AWS Security Group Best Practices",
        url="https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html",
    ),
]


# =============================================================================
# CIS AWS 5.1: Unrestricted SSH Access
# Main node: EC2SecurityGroup
# =============================================================================
class UnrestrictedSshOutput(Finding):
    """Output model for unrestricted SSH check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_unrestricted_ssh = Fact(
    id="aws_unrestricted_ssh",
    name="AWS security groups allow unrestricted SSH access",
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

cis_5_1_unrestricted_ssh = Rule(
    id="cis_5_1_unrestricted_ssh",
    name="CIS AWS 5.1: Unrestricted SSH Access",
    description=(
        "Security groups should not allow SSH access (port 22) from any IP address. "
        "Unrestricted SSH access increases the risk of unauthorized access."
    ),
    output_model=UnrestrictedSshOutput,
    facts=(_aws_unrestricted_ssh,),
    tags=(
        "cis:5.1",
        "cis:aws-5.0",
        "networking",
        "security-groups",
        "ssh",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 5.2: Unrestricted RDP Access
# Main node: EC2SecurityGroup
# =============================================================================
class UnrestrictedRdpOutput(Finding):
    """Output model for unrestricted RDP check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_unrestricted_rdp = Fact(
    id="aws_unrestricted_rdp",
    name="AWS security groups allow unrestricted RDP access",
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

cis_5_2_unrestricted_rdp = Rule(
    id="cis_5_2_unrestricted_rdp",
    name="CIS AWS 5.2: Unrestricted RDP Access",
    description=(
        "Security groups should not allow RDP access (port 3389) from any IP address. "
        "Unrestricted RDP access increases the risk of unauthorized access."
    ),
    output_model=UnrestrictedRdpOutput,
    facts=(_aws_unrestricted_rdp,),
    tags=(
        "cis:5.2",
        "cis:aws-5.0",
        "networking",
        "security-groups",
        "rdp",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS AWS 5.4: Default Security Group Restricts All Traffic
# Main node: EC2SecurityGroup
# =============================================================================
class DefaultSgAllowsTrafficOutput(Finding):
    """Output model for default security group check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    rule_direction: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_default_sg_allows_traffic = Fact(
    id="aws_default_sg_allows_traffic",
    name="AWS default security group allows traffic",
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

cis_5_4_default_sg_traffic = Rule(
    id="cis_5_4_default_sg_traffic",
    name="CIS AWS 5.4: Default Security Group Restricts Traffic",
    description=(
        "The default security group of every VPC should restrict all traffic to "
        "prevent accidental exposure of resources."
    ),
    output_model=DefaultSgAllowsTrafficOutput,
    facts=(_aws_default_sg_allows_traffic,),
    tags=(
        "cis:5.4",
        "cis:aws-5.0",
        "networking",
        "security-groups",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# Additional: Unrestricted All Ports
# Main node: EC2SecurityGroup
# =============================================================================
class UnrestrictedAllPortsOutput(Finding):
    """Output model for unrestricted all ports check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_unrestricted_all_ports = Fact(
    id="aws_unrestricted_all_ports",
    name="AWS security groups with unrestricted access to all ports",
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

unrestricted_all_ports = Rule(
    id="unrestricted_all_ports",
    name="Unrestricted Access to All Ports",
    description=(
        "Security groups should not allow access to all ports from any IP address. "
        "This is a severe misconfiguration that exposes all services."
    ),
    output_model=UnrestrictedAllPortsOutput,
    facts=(_aws_unrestricted_all_ports,),
    tags=(
        "cis:aws-5.0",
        "networking",
        "security-groups",
        "critical",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
)
