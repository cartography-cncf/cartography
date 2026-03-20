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
        text="AWS Security Group Best Practices",
        url="https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html",
    ),
]


# =============================================================================
# CIS AWS 5.3: Remote Administration Ports Open to IPv4 Internet
# Main node: EC2SecurityGroup
# =============================================================================
class RemoteAdminIpv4Output(Finding):
    """Output model for IPv4 remote administration exposure check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_remote_admin_ipv4 = Fact(
    id="aws_remote_admin_ipv4",
    name="AWS security groups allow IPv4 internet access to remote administration ports",
    description=(
        "Detects security groups that allow ingress from 0.0.0.0/0 to remote "
        "administration ports (22 and 3389). Public access to SSH or RDP increases "
        "the risk of unauthorized access and brute force attacks."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
          -[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:AWSIpRange)
    WHERE range.id = '0.0.0.0/0'
      AND (
          (rule.fromport <= 22 AND rule.toport >= 22)
          OR (rule.fromport <= 3389 AND rule.toport >= 3389)
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
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
          -[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:AWSIpRange)
    WHERE range.id = '0.0.0.0/0'
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

cis_aws_5_3_remote_admin_ipv4 = Rule(
    id="cis_aws_5_3_remote_admin_ipv4",
    name="CIS AWS 5.3: IPv4 Remote Administration Ports Open to the Internet",
    description=(
        "Security groups should not allow ingress from 0.0.0.0/0 to remote "
        "administration ports such as SSH (22) and RDP (3389)."
    ),
    output_model=RemoteAdminIpv4Output,
    facts=(_aws_remote_admin_ipv4,),
    tags=(
        "networking",
        "security-groups",
        "remote-admin",
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
# CIS AWS 5.4: Remote Administration Ports Open to IPv6 Internet
# Main node: EC2SecurityGroup
# =============================================================================
class RemoteAdminIpv6Output(Finding):
    """Output model for IPv6 remote administration exposure check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_remote_admin_ipv6 = Fact(
    id="aws_remote_admin_ipv6",
    name="AWS security groups allow IPv6 internet access to remote administration ports",
    description=(
        "Detects security groups that allow ingress from ::/0 to remote "
        "administration ports (22 and 3389). Public access to SSH or RDP increases "
        "the risk of unauthorized access and brute force attacks."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
          -[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:AWSIpRange)
    WHERE range.id = '::/0'
      AND (
          (rule.fromport <= 22 AND rule.toport >= 22)
          OR (rule.fromport <= 3389 AND rule.toport >= 3389)
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
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
          -[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:AWSIpRange)
    WHERE range.id = '::/0'
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

cis_aws_5_4_remote_admin_ipv6 = Rule(
    id="cis_aws_5_4_remote_admin_ipv6",
    name="CIS AWS 5.4: IPv6 Remote Administration Ports Open to the Internet",
    description=(
        "Security groups should not allow ingress from ::/0 to remote "
        "administration ports such as SSH (22) and RDP (3389)."
    ),
    output_model=RemoteAdminIpv6Output,
    facts=(_aws_remote_admin_ipv6,),
    tags=(
        "networking",
        "security-groups",
        "remote-admin",
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
            requirement="5.4",
        ),
    ),
)


# =============================================================================
# CIS AWS 5.5: Default Security Group Restricts All Traffic
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
        "The default security group of every VPC should restrict all traffic to "
        "prevent accidental exposure of resources."
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
# CIS AWS 5.7: EC2 Instances Should Use IMDSv2
# Main node: EC2Instance
# =============================================================================
class Ec2Imdsv2RequiredOutput(Finding):
    """Output model for EC2 IMDSv2 requirement check."""

    instance_id: str | None = None
    region: str | None = None
    metadata_http_tokens: str | None = None
    imds_access_mode: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_ec2_imdsv2_required = Fact(
    id="aws_ec2_imdsv2_required",
    name="AWS EC2 instances allow IMDSv1",
    description=(
        "Detects EC2 instances where Instance Metadata Service Version 2 (IMDSv2) "
        "is not required. These instances allow IMDSv1 because HttpTokens is set "
        "to optional."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
    WHERE ec2.metadatahttptokens = 'optional'
    RETURN
        ec2.instanceid AS instance_id,
        ec2.region AS region,
        ec2.metadatahttptokens AS metadata_http_tokens,
        ec2.imdsaccessmode AS imds_access_mode,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)
    WHERE ec2.metadatahttptokens = 'optional'
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
    name="CIS AWS 5.7: EC2 Instances Should Use IMDSv2",
    description=(
        "EC2 instances should require Instance Metadata Service Version 2 (IMDSv2) "
        "so that IMDSv1 is disabled."
    ),
    output_model=Ec2Imdsv2RequiredOutput,
    facts=(_aws_ec2_imdsv2_required,),
    tags=(
        "networking",
        "ec2",
        "imds",
        "stride:spoofing",
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
