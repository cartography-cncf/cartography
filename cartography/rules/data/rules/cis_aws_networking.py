"""
CIS AWS Networking Security Checks

Implements CIS AWS Foundations Benchmark Section 6: Networking
Based on CIS AWS Foundations Benchmark v6.0.0

Each Rule represents a distinct security concept with a consistent main node type.
Facts within a Rule are provider-specific implementations of the same concept.
"""

from cartography.rules.data.frameworks.cis import cis_aws
from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS AWS Foundations Benchmark v6.0.0",
        url="https://www.cisecurity.org/benchmark/amazon_web_services",
    ),
    RuleReference(
        text="AWS Security Group Best Practices",
        url="https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html",
    ),
]


# =============================================================================
# CIS AWS 6.1.1: EBS Volume Encryption
# Main node: EBSVolume
# =============================================================================
class EbsEncryptionOutput(Finding):
    """Output model for EBS encryption check."""

    volume_id: str | None = None
    region: str | None = None
    volume_type: str | None = None
    size_gb: int | None = None
    state: str | None = None
    encrypted: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_ebs_encryption_disabled = Fact(
    id="aws_ebs_encryption_disabled",
    name="AWS EBS volumes without encryption",
    description=(
        "Detects EBS volumes that are not encrypted. Encrypting EBS volumes "
        "protects data at rest and data in transit between the volume and instance."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(volume:EBSVolume)
    WHERE volume.encrypted = false
    RETURN
        volume.id AS volume_id,
        volume.region AS region,
        volume.volumetype AS volume_type,
        volume.size AS size_gb,
        volume.state AS state,
        volume.encrypted AS encrypted,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(volume:EBSVolume)
    WHERE volume.encrypted = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (volume:EBSVolume)
    RETURN COUNT(volume) AS count
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

cis_aws_6_1_1_ebs_encryption = Rule(
    id="cis_aws_6_1_1_ebs_encryption",
    name="CIS AWS 6.1.1: EBS Volume Encryption",
    description=(
        "EBS volumes should be encrypted to protect data at rest and in transit "
        "between the volume and instance."
    ),
    output_model=EbsEncryptionOutput,
    facts=(_aws_ebs_encryption_disabled,),
    tags=("networking", "ebs", "encryption", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("6.1.1"),
        iso27001_annex_a("8.24"),
    ),
)


# =============================================================================
# CIS AWS 6.1.2: CIFS Access Is Restricted to Trusted Networks
# Main node: EC2SecurityGroup
# =============================================================================
class CifsInternetAccessOutput(Finding):
    """Output model for CIFS internet exposure check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    protocol: str | None = None
    cidr_range: str | None = None
    account_id: str | None = None
    account: str | None = None


_aws_cifs_internet_access = Fact(
    id="aws_cifs_internet_access",
    name="AWS security groups allow internet access to CIFS",
    description=(
        "Detects security groups that allow ingress from the internet to CIFS/SMB "
        "port 445. CIFS access should be restricted to trusted networks."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:AWSIpRange)
    WHERE coalesce(range.range, range.id) IN ['0.0.0.0/0', '::/0']
      AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
      AND (
          rule.fromport IS NULL
          OR (rule.fromport <= 445 AND rule.toport >= 445)
      )
    RETURN DISTINCT
        sg.groupid AS security_group_id,
        sg.name AS security_group_name,
        sg.region AS region,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        rule.protocol AS protocol,
        coalesce(range.range, range.id) AS cidr_range,
        a.id AS account_id,
        a.name AS account
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
          <-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
          <-[:MEMBER_OF_IP_RULE]-(range:AWSIpRange)
    WHERE coalesce(range.range, range.id) IN ['0.0.0.0/0', '::/0']
      AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
      AND (
          rule.fromport IS NULL
          OR (rule.fromport <= 445 AND rule.toport >= 445)
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

cis_aws_6_1_2_cifs_restricted = Rule(
    id="cis_aws_6_1_2_cifs_restricted",
    name="CIS AWS 6.1.2: CIFS Access Is Restricted to Trusted Networks",
    description=(
        "Security groups should not allow ingress from public internet ranges to "
        "CIFS/SMB port 445."
    ),
    output_model=CifsInternetAccessOutput,
    facts=(_aws_cifs_internet_access,),
    tags=(
        "networking",
        "security-groups",
        "cifs",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        cis_aws("6.1.2"),
        iso27001_annex_a("8.20"),
    ),
)


# =============================================================================
# CIS AWS 6.3: Remote Administration Ports Open to IPv4 Internet
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

cis_aws_6_3_remote_admin_ipv4 = Rule(
    id="cis_aws_6_3_remote_admin_ipv4",
    name="CIS AWS 6.3: IPv4 Remote Administration Ports Open to the Internet",
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
        cis_aws("6.3"),
        iso27001_annex_a("8.20"),
    ),
)


# =============================================================================
# CIS AWS 6.4: Remote Administration Ports Open to IPv6 Internet
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

cis_aws_6_4_remote_admin_ipv6 = Rule(
    id="cis_aws_6_4_remote_admin_ipv6",
    name="CIS AWS 6.4: IPv6 Remote Administration Ports Open to the Internet",
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
        cis_aws("6.4"),
        iso27001_annex_a("8.20"),
    ),
)


# =============================================================================
# CIS AWS 6.5: Default Security Group Restricts All Traffic
# Main node: EC2SecurityGroup
# =============================================================================
class DefaultSgAllowsTrafficOutput(Finding):
    """Output model for default security group check."""

    security_group_id: str | None = None
    security_group_name: str | None = None
    region: str | None = None
    has_inbound_rules: bool | None = None
    has_egress_rules: bool | None = None
    in_use: bool | None = None
    account_id: str | None = None
    account: str | None = None


_aws_default_sg_allows_traffic = Fact(
    id="aws_default_sg_allows_traffic",
    name="AWS default security group allows traffic",
    description=(
        "Detects VPCs where the default security group has inbound or outbound rules "
        "allowing traffic. The default security group should restrict all traffic "
        "to prevent accidental exposure of resources. The `in_use` flag indicates "
        "whether any non-rule resource (EC2 instance, ENI, load balancer, RDS, etc.) "
        "is attached, so unused-VPC defaults can be filtered or downgraded."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:EC2SecurityGroup)
    WHERE sg.name = 'default'
    OPTIONAL MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(inbound:AWSIpPermissionInbound)
    OPTIONAL MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(egress:AWSIpRule)
        WHERE NOT egress:AWSIpPermissionInbound
    OPTIONAL MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(consumer)
        WHERE NOT consumer:IpRule AND NOT consumer:AWSVpc
    WITH a, sg,
        count(DISTINCT inbound) > 0 AS has_inbound_rules,
        count(DISTINCT egress) > 0 AS has_egress_rules,
        count(DISTINCT consumer) > 0 AS in_use
    WHERE has_inbound_rules OR has_egress_rules
    RETURN
        sg.groupid AS security_group_id,
        sg.name AS security_group_name,
        sg.region AS region,
        has_inbound_rules,
        has_egress_rules,
        in_use,
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

cis_aws_6_5_default_sg_traffic = Rule(
    id="cis_aws_6_5_default_sg_traffic",
    name="CIS AWS 6.5: Default Security Group Restricts Traffic",
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
        cis_aws("6.5"),
        iso27001_annex_a("8.20"),
        iso27001_annex_a("8.22"),
    ),
)


# =============================================================================
# CIS AWS 6.7: EC2 Instances Should Use IMDSv2
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

cis_aws_6_7_ec2_imdsv2 = Rule(
    id="cis_aws_6_7_ec2_imdsv2",
    name="CIS AWS 6.7: EC2 Instances Should Use IMDSv2",
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
        cis_aws("6.7"),
        iso27001_annex_a("8.9"),
    ),
)


# =============================================================================
# CIS AWS 6.1.1: Partial control coverage
# Missing datamodel: account-level EnableEbsEncryptionByDefault setting per region;
# current rule evaluates per-volume encrypted state, which is stricter but does not
# detect the absence of the account-level default
# =============================================================================

# =============================================================================
# TODO: CIS AWS 6.2: No Network ACLs allow ingress from 0.0.0.0/0 to remote administration ports
# Missing datamodel or evidence: Network ACL inventory, rule entries, and subnet associations
# =============================================================================

# =============================================================================
# TODO: CIS AWS 6.6: Routing tables for VPC peering are least access
# Missing datamodel or evidence: route table entries, peering connection targets, and organization-defined least-access routing baseline
# =============================================================================

# =============================================================================
# TODO: ISO 27001 Annex A 8.21: Network services security
# Missing datamodel or evidence: service-level requirements and monitoring state
# for managed network services. Existing security group facts cover network
# exposure, but not agreed service levels or operational monitoring.
# =============================================================================
