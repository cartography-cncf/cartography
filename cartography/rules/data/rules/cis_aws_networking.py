"""
CIS AWS Networking Security Checks

Implements CIS AWS Foundations Benchmark Section 5: Networking
Based on CIS AWS Foundations Benchmark v5.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Framework
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
        text="Amazon VPC security group rules",
        url="https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html",
    ),
    RuleReference(
        text="Control access with network ACLs",
        url="https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html",
    ),
    RuleReference(
        text="Transition to using Instance Metadata Service Version 2",
        url="https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-metadata-transition-to-version-2.html",
    ),
]


# =============================================================================
# CIS AWS 5.2: Network ACLs deny administrative ports from 0.0.0.0/0
# Main node: EC2NetworkAcl
# =============================================================================
class NetworkAclAdminPortsOutput(Finding):
    """Output model for the network ACL administrative ports check."""

    network_acl_id: str | None = None
    network_acl_arn: str | None = None
    region: str | None = None
    rule_number: int | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_nacl_admin_ports_ipv4 = Fact(
    id="aws_nacl_admin_ports_ipv4",
    name="AWS network ACLs allow administrative ports from 0.0.0.0/0",
    description=(
        "Detects inbound network ACL rules that allow remote administration ports "
        "from any IPv4 address. Inbound access to SSH and RDP should be denied "
        "from 0.0.0.0/0."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(rule:EC2NetworkAclRule:IpPermissionInbound)
          -[:MEMBER_OF_NACL]->(nacl:EC2NetworkAcl)
    WHERE rule.cidrblock = '0.0.0.0/0'
      AND rule.ruleaction = 'allow'
      AND coalesce(rule.protocol, '-1') IN ['6', '-1']
      AND (
          (rule.fromport <= 22 AND rule.toport >= 22)
          OR (rule.fromport <= 3389 AND rule.toport >= 3389)
          OR rule.protocol = '-1'
      )
    RETURN DISTINCT
        nacl.network_acl_id AS network_acl_id,
        nacl.arn AS network_acl_arn,
        nacl.region AS region,
        rule.rulenumber AS rule_number,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        rule.protocol AS protocol,
        rule.cidrblock AS cidr_range,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(rule:EC2NetworkAclRule:IpPermissionInbound)
          -[:MEMBER_OF_NACL]->(nacl:EC2NetworkAcl)
    WHERE rule.cidrblock = '0.0.0.0/0'
      AND rule.ruleaction = 'allow'
      AND coalesce(rule.protocol, '-1') IN ['6', '-1']
      AND (
          (rule.fromport <= 22 AND rule.toport >= 22)
          OR (rule.fromport <= 3389 AND rule.toport >= 3389)
          OR rule.protocol = '-1'
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (rule:EC2NetworkAclRule)
    RETURN COUNT(rule) AS count
    """,
    asset_id_field="network_acl_id",
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_5_2_nacl_admin_ports_ipv4 = Rule(
    id="cis_aws_5_2_nacl_admin_ports_ipv4",
    name="CIS AWS 5.2: Network ACLs Restrict Administrative Ports From 0.0.0.0/0",
    description=(
        "Inbound network ACL rules should not allow remote administration ports "
        "from any IPv4 address."
    ),
    output_model=NetworkAclAdminPortsOutput,
    facts=(_aws_nacl_admin_ports_ipv4,),
    tags=(
        "networking",
        "network-acls",
        "ssh",
        "rdp",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="5.0",
            requirement="5.2",
        ),
    ),
)


# =============================================================================
# CIS AWS 5.3: Security groups restrict administrative ports from 0.0.0.0/0
# Main node: EC2SecurityGroup
# =============================================================================
class SecurityGroupAdminPortsOutput(Finding):
    """Output model for the security group administrative ports check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_sg_admin_ports_ipv4 = Fact(
    id="aws_sg_admin_ports_ipv4",
    name="AWS security groups allow administrative ports from 0.0.0.0/0",
    description=(
        "Detects security groups that allow SSH or RDP access from any IPv4 "
        "address. Administrative ports should not be exposed to 0.0.0.0/0."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
          -[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:AWSIpRange)
    WHERE range.range = '0.0.0.0/0'
      AND coalesce(rule.protocol, 'tcp') IN ['tcp', '-1']
      AND (
          (rule.fromport <= 22 AND rule.toport >= 22)
          OR (rule.fromport <= 3389 AND rule.toport >= 3389)
          OR rule.protocol = '-1'
      )
    RETURN DISTINCT
        sg.groupid AS security_group_id,
        sg.name AS security_group_name,
        sg.region AS region,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        rule.protocol AS protocol,
        range.range AS cidr_range,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
          -[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:AWSIpRange)
    WHERE range.range = '0.0.0.0/0'
      AND coalesce(rule.protocol, 'tcp') IN ['tcp', '-1']
      AND (
          (rule.fromport <= 22 AND rule.toport >= 22)
          OR (rule.fromport <= 3389 AND rule.toport >= 3389)
          OR rule.protocol = '-1'
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sg:EC2SecurityGroup)
    RETURN COUNT(sg) AS count
    """,
    asset_id_field="security_group_id",
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_5_3_security_group_admin_ports_ipv4 = Rule(
    id="cis_aws_5_3_security_group_admin_ports_ipv4",
    name="CIS AWS 5.3: Security Groups Restrict Administrative Ports From 0.0.0.0/0",
    description=(
        "Security groups should not allow SSH or RDP access from any IPv4 address."
    ),
    output_model=SecurityGroupAdminPortsOutput,
    facts=(_aws_sg_admin_ports_ipv4,),
    tags=(
        "networking",
        "security-groups",
        "ssh",
        "rdp",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="5.0",
            requirement="5.3",
        ),
    ),
)


# =============================================================================
# CIS AWS 5.5: Default security group restricts all traffic
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
        "allowing traffic. Default security groups should restrict all traffic."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
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
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpRule:IpPermissionEgress)
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
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpRule)
    WHERE sg.name = 'default'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sg:EC2SecurityGroup)
    RETURN COUNT(sg) AS count
    """,
    asset_id_field="security_group_id",
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_5_5_default_sg_traffic = Rule(
    id="cis_aws_5_5_default_sg_traffic",
    name="CIS AWS 5.5: Default Security Group Restricts Traffic",
    description=(
        "The default security group of every VPC should restrict all traffic."
    ),
    output_model=DefaultSgAllowsTrafficOutput,
    facts=(_aws_default_sg_allows_traffic,),
    tags=(
        "networking",
        "security-groups",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="5.0",
            requirement="5.5",
        ),
    ),
)


# =============================================================================
# CIS AWS 5.7: EC2 instances use IMDSv2
# Main node: EC2Instance
# =============================================================================
class Ec2ImdsV2Output(Finding):
    """Output model for the EC2 IMDSv2 requirement check."""

    instance_id: str | None = None
    region: str | None = None
    state: str | None = None
    metadata_http_tokens: str | None = None
    imds_v2_required: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_ec2_imdsv2_not_required = Fact(
    id="aws_ec2_imdsv2_not_required",
    name="AWS EC2 instances do not require IMDSv2",
    description=(
        "Detects EC2 instances that still allow IMDSv1. Instances should require "
        "IMDSv2 to reduce the risk of SSRF and credential theft."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
    WHERE ec2.metadatahttptokens IS NULL OR ec2.metadatahttptokens <> 'required'
    RETURN
        ec2.instanceid AS instance_id,
        ec2.region AS region,
        ec2.state AS state,
        ec2.metadatahttptokens AS metadata_http_tokens,
        ec2.imdsv2required AS imds_v2_required,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
    WHERE ec2.metadatahttptokens IS NULL OR ec2.metadatahttptokens <> 'required'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:EC2Instance)
    RETURN COUNT(ec2) AS count
    """,
    asset_id_field="instance_id",
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_5_7_ec2_imdsv2 = Rule(
    id="cis_aws_5_7_ec2_imdsv2",
    name="CIS AWS 5.7: EC2 Instances Use IMDSv2",
    description=(
        "EC2 instances should require Instance Metadata Service Version 2 and not "
        "allow fallback to IMDSv1."
    ),
    output_model=Ec2ImdsV2Output,
    facts=(_aws_ec2_imdsv2_not_required,),
    tags=(
        "networking",
        "ec2",
        "imdsv2",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS AWS Foundations Benchmark",
            short_name="CIS",
            scope="aws",
            revision="5.0",
            requirement="5.7",
        ),
    ),
)
