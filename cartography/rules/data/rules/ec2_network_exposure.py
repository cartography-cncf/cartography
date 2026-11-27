"""
AWS EC2 network exposure: security groups, network ACLs, Elastic IPs


Each rule is a single-property check over data the AWS sync already collects.
All are EXPERIMENTAL until validated against a live graph.

"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule


class AwsEc2ElasticIpUnassignedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    public_ip: str | None = None
    allocation_id: str | None = None
    association_id: str | None = None
    instance_id: str | None = None
    network_interface_id: str | None = None


_aws_ec2_elastic_ip_unassigned_fact = Fact(
    id="aws_ec2_elastic_ip_unassigned_fact",
    name="Unassigned Elastic IP",
    description="Elastic IPs with no association, instance or network interface.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(e:AWSElasticIPAddress)
        WHERE e.association_id IS NULL
          AND e.instance_id IS NULL
          AND e.network_interface_id IS NULL
        RETURN a.id AS account_id, a.name AS account,
               e.public_ip AS public_ip, e.allocation_id AS allocation_id,
               e.association_id AS association_id, e.instance_id AS instance_id,
               e.network_interface_id AS network_interface_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(e:AWSElasticIPAddress)
        WHERE e.association_id IS NULL
          AND e.instance_id IS NULL
          AND e.network_interface_id IS NULL
        RETURN a.id AS account_id, a.name AS account,
               e.public_ip AS public_ip, e.allocation_id AS allocation_id,
               e.association_id AS association_id, e.instance_id AS instance_id,
               e.network_interface_id AS network_interface_id

    """,
    cypher_count_query="""
    MATCH (e:AWSElasticIPAddress) RETURN COUNT(e) AS count
    """,
    asset_label="AWSElasticIPAddress",
    asset_id_field="allocation_id",
    identity_fields=("account_id", "account", "allocation_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_elastic_ip_unassigned = Rule(
    id="aws_ec2_elastic_ip_unassigned",
    name="Unassigned Elastic IP",
    description="Elastic IP allocated but not associated with an instance or network interface (association_id, instance_id and network_interface_id all null). Unassociated EIPs incur cost and indicate stale allocations.",
    output_model=AwsEc2ElasticIpUnassignedOutput,
    facts=(_aws_ec2_elastic_ip_unassigned_fact,),
    tags=("ec2", "hygiene", "cspm", "low"),
    version="0.1.0",
)


class AwsEc2NetworkaclIngressAnyPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    network_acl_id: str | None = None
    is_default: bool | None = None
    rule_number: str | None = None


_aws_ec2_networkacl_ingress_any_port_fact = Fact(
    id="aws_ec2_networkacl_ingress_any_port_fact",
    name="NACL ingress any port",
    description="NACLs with an allow ingress rule from the internet covering any port.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(acl:AWSEC2NetworkAcl)<-[:MEMBER_OF_NACL]-(r:AWSEC2NetworkAclRule)
        WHERE r.egress = false
          AND r.ruleaction = 'allow'
          AND (r.cidrblock = '0.0.0.0/0' OR r.ipv6cidrblock = '::/0')
          AND (r.protocol = '-1' OR r.fromport IS NULL
               OR (coalesce(r.fromport, 0) <= 0 AND coalesce(r.toport, 65535) >= 65535))
        RETURN DISTINCT a.id AS account_id, a.name AS account,
               acl.network_acl_id AS network_acl_id, acl.is_default AS is_default,
               r.rulenumber AS rule_number

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(acl:AWSEC2NetworkAcl)<-[:MEMBER_OF_NACL]-(r:AWSEC2NetworkAclRule)
        WHERE r.egress = false
          AND r.ruleaction = 'allow'
          AND (r.cidrblock = '0.0.0.0/0' OR r.ipv6cidrblock = '::/0')
          AND (r.protocol = '-1' OR r.fromport IS NULL
               OR (coalesce(r.fromport, 0) <= 0 AND coalesce(r.toport, 65535) >= 65535))
        RETURN DISTINCT a.id AS account_id, a.name AS account,
               acl.network_acl_id AS network_acl_id, acl.is_default AS is_default,
               r.rulenumber AS rule_number

    """,
    cypher_count_query="""
    MATCH (acl:AWSEC2NetworkAcl) RETURN COUNT(acl) AS count
    """,
    asset_label="AWSEC2NetworkAcl",
    asset_id_field="network_acl_id",
    identity_fields=("network_acl_id", "rule_number"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_networkacl_ingress_any_port = Rule(
    id="aws_ec2_networkacl_ingress_any_port",
    name="Network ACL Ingress Any Port from Internet",
    description="Network ACL has an ingress rule (egress=false, ruleaction='allow') from 0.0.0.0/0 or ::/0 that allows any port/protocol (protocol='-1', no port range, or the full 0-65535 range). Rules join the ACL via MEMBER_OF_NACL.",
    output_model=AwsEc2NetworkaclIngressAnyPortOutput,
    facts=(_aws_ec2_networkacl_ingress_any_port_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2NetworkaclIngressRdpOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    network_acl_id: str | None = None
    is_default: bool | None = None
    rule_number: str | None = None
    source_cidr: str | None = None
    port: str | None = None


_aws_ec2_networkacl_ingress_rdp_fact = Fact(
    id="aws_ec2_networkacl_ingress_rdp_fact",
    name="Network ACLs allowing internet ingress to TCP 3389 (RDP)",
    description="Network ACLs with an ingress allow rule (egress=false, ruleaction='allow') from 0.0.0.0/0 or ::/0 whose protocol is TCP ('6') or all ('-1') and whose port range covers 3389 (RDP). LIMITATION: NACL rule ordering is not evaluated — a lower-numbered deny entry shadowing the allow is still flagged (same basis as the spec predicate).",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(acl:AWSEC2NetworkAcl)<-[:MEMBER_OF_NACL]-(rule:AWSEC2NetworkAclRule)
    WHERE rule.egress = false
      AND rule.ruleaction = 'allow'
      AND (rule.cidrblock = '0.0.0.0/0' OR rule.ipv6cidrblock = '::/0')
      AND toString(rule.protocol) IN ['6', '-1']
      AND (
        toString(rule.protocol) = '-1'
        OR (coalesce(rule.fromport, 0) <= 3389
            AND coalesce(rule.toport, rule.fromport, 0) >= 3389)
      )
    RETURN DISTINCT
        a.id AS account_id,
        a.name AS account,
        acl.network_acl_id AS network_acl_id,
        acl.is_default AS is_default,
        rule.rulenumber AS rule_number,
        coalesce(rule.cidrblock, rule.ipv6cidrblock) AS source_cidr,
        3389 AS port
    ORDER BY account, network_acl_id, rule_number
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(acl:AWSEC2NetworkAcl)<-[:MEMBER_OF_NACL]-(rule:AWSEC2NetworkAclRule)
    WHERE rule.egress = false
      AND rule.ruleaction = 'allow'
      AND (rule.cidrblock = '0.0.0.0/0' OR rule.ipv6cidrblock = '::/0')
      AND toString(rule.protocol) IN ['6', '-1']
      AND (
        toString(rule.protocol) = '-1'
        OR (coalesce(rule.fromport, 0) <= 3389
            AND coalesce(rule.toport, rule.fromport, 0) >= 3389)
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (acl:AWSEC2NetworkAcl) RETURN COUNT(acl) AS count
    """,
    asset_label="AWSEC2NetworkAcl",
    asset_id_field="network_acl_id",
    identity_fields=("account_id", "network_acl_id", "rule_number"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_networkacl_ingress_rdp = Rule(
    id="aws_ec2_networkacl_ingress_rdp",
    name="Network ACL Internet Ingress to TCP 3389 (RDP)",
    description="Network ACLs with an ingress allow rule (egress=false, ruleaction='allow') from 0.0.0.0/0 or ::/0 whose protocol is TCP ('6') or all ('-1') and whose port range covers 3389 (RDP). LIMITATION: NACL rule ordering is not evaluated — a lower-numbered deny entry shadowing the allow is still flagged (same basis as the spec predicate).",
    output_model=AwsEc2NetworkaclIngressRdpOutput,
    facts=(_aws_ec2_networkacl_ingress_rdp_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2NetworkaclIngressSshOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    network_acl_id: str | None = None
    is_default: bool | None = None
    rule_number: str | None = None
    source_cidr: str | None = None
    port: str | None = None


_aws_ec2_networkacl_ingress_ssh_fact = Fact(
    id="aws_ec2_networkacl_ingress_ssh_fact",
    name="Network ACLs allowing internet ingress to TCP 22 (SSH)",
    description="Network ACLs with an ingress allow rule (egress=false, ruleaction='allow') from 0.0.0.0/0 or ::/0 whose protocol is TCP ('6') or all ('-1') and whose port range covers 22 (SSH). LIMITATION: NACL rule ordering is not evaluated — a lower-numbered deny entry shadowing the allow is still flagged (same basis as the spec predicate).",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(acl:AWSEC2NetworkAcl)<-[:MEMBER_OF_NACL]-(rule:AWSEC2NetworkAclRule)
    WHERE rule.egress = false
      AND rule.ruleaction = 'allow'
      AND (rule.cidrblock = '0.0.0.0/0' OR rule.ipv6cidrblock = '::/0')
      AND toString(rule.protocol) IN ['6', '-1']
      AND (
        toString(rule.protocol) = '-1'
        OR (coalesce(rule.fromport, 0) <= 22
            AND coalesce(rule.toport, rule.fromport, 0) >= 22)
      )
    RETURN DISTINCT
        a.id AS account_id,
        a.name AS account,
        acl.network_acl_id AS network_acl_id,
        acl.is_default AS is_default,
        rule.rulenumber AS rule_number,
        coalesce(rule.cidrblock, rule.ipv6cidrblock) AS source_cidr,
        22 AS port
    ORDER BY account, network_acl_id, rule_number
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(acl:AWSEC2NetworkAcl)<-[:MEMBER_OF_NACL]-(rule:AWSEC2NetworkAclRule)
    WHERE rule.egress = false
      AND rule.ruleaction = 'allow'
      AND (rule.cidrblock = '0.0.0.0/0' OR rule.ipv6cidrblock = '::/0')
      AND toString(rule.protocol) IN ['6', '-1']
      AND (
        toString(rule.protocol) = '-1'
        OR (coalesce(rule.fromport, 0) <= 22
            AND coalesce(rule.toport, rule.fromport, 0) >= 22)
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (acl:AWSEC2NetworkAcl) RETURN COUNT(acl) AS count
    """,
    asset_label="AWSEC2NetworkAcl",
    asset_id_field="network_acl_id",
    identity_fields=("account_id", "network_acl_id", "rule_number"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_networkacl_ingress_ssh = Rule(
    id="aws_ec2_networkacl_ingress_ssh",
    name="Network ACL Internet Ingress to TCP 22 (SSH)",
    description="Network ACLs with an ingress allow rule (egress=false, ruleaction='allow') from 0.0.0.0/0 or ::/0 whose protocol is TCP ('6') or all ('-1') and whose port range covers 22 (SSH). LIMITATION: NACL rule ordering is not evaluated — a lower-numbered deny entry shadowing the allow is still flagged (same basis as the spec predicate).",
    output_model=AwsEc2NetworkaclIngressSshOutput,
    facts=(_aws_ec2_networkacl_ingress_ssh_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2NetworkaclUnusedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    network_acl_id: str | None = None
    is_default: bool | None = None
    vpc_id: str | None = None


_aws_ec2_networkacl_unused_fact = Fact(
    id="aws_ec2_networkacl_unused_fact",
    name="Non-default ACL without subnet",
    description="Non-default network ACLs with no PART_OF_SUBNET association.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(acl:AWSEC2NetworkAcl)
        WHERE acl.is_default = false
          AND NOT EXISTS { MATCH (acl)-[:PART_OF_SUBNET]->(:AWSEC2Subnet) }
        RETURN a.id AS account_id, a.name AS account,
               acl.network_acl_id AS network_acl_id, acl.is_default AS is_default,
               acl.vpc_id AS vpc_id

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(acl:AWSEC2NetworkAcl)
        WHERE acl.is_default = false
          AND NOT EXISTS { MATCH (acl)-[:PART_OF_SUBNET]->(:AWSEC2Subnet) }
        RETURN a.id AS account_id, a.name AS account,
               acl.network_acl_id AS network_acl_id, acl.is_default AS is_default,
               acl.vpc_id AS vpc_id

    """,
    cypher_count_query="""
    MATCH (acl:AWSEC2NetworkAcl) WHERE acl.is_default = false RETURN COUNT(acl) AS count
    """,
    asset_label="AWSEC2NetworkAcl",
    asset_id_field="network_acl_id",
    identity_fields=("account_id", "account", "network_acl_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_networkacl_unused = Rule(
    id="aws_ec2_networkacl_unused",
    name="Unused Non-Default Network ACL",
    description="Non-default network ACL (is_default=false) not associated with any subnet via PART_OF_SUBNET. Unused custom ACLs are stale configuration that should be removed.",
    output_model=AwsEc2NetworkaclUnusedOutput,
    facts=(_aws_ec2_networkacl_unused_fact,),
    tags=("ec2", "network", "hygiene", "cspm", "low"),
    version="0.1.0",
)


class AwsEc2SecuritygroupAllPortsOpenOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None


_aws_ec2_securitygroup_all_ports_open_fact = Fact(
    id="aws_ec2_securitygroup_all_ports_open_fact",
    name="SG all ports open",
    description="Security groups with an all-ports inbound rule from the internet, attached to a public instance.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)

        MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(pub)
        WHERE (pub:AWSEC2Instance AND pub.publicipaddress IS NOT NULL
               AND NOT coalesce(pub.state, 'running') IN ['terminated', 'shutting-down'])
           OR (pub:AWSRDSInstance AND pub.publicly_accessible = true)
           OR (pub:AWSRedshiftCluster AND pub.publicly_accessible = true)
           OR (pub:AWSNetworkInterface AND pub.public_ip IS NOT NULL)
           OR (pub:AWSLoadBalancerV2 AND pub.scheme = 'internet-facing')
           OR (pub:AWSLoadBalancer AND pub.scheme = 'internet-facing')

        WITH a, sg, rule, ip
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND (rule.protocol = '-1' OR rule.fromport IS NULL
               OR (coalesce(rule.fromport, 0) <= 0 AND coalesce(rule.toport, 65535) >= 65535))
        RETURN DISTINCT a.id AS account_id, a.name AS account,
               sg.groupid AS group_id, sg.name AS group_name

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)

        MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(pub)
        WHERE (pub:AWSEC2Instance AND pub.publicipaddress IS NOT NULL
               AND NOT coalesce(pub.state, 'running') IN ['terminated', 'shutting-down'])
           OR (pub:AWSRDSInstance AND pub.publicly_accessible = true)
           OR (pub:AWSRedshiftCluster AND pub.publicly_accessible = true)
           OR (pub:AWSNetworkInterface AND pub.public_ip IS NOT NULL)
           OR (pub:AWSLoadBalancerV2 AND pub.scheme = 'internet-facing')
           OR (pub:AWSLoadBalancer AND pub.scheme = 'internet-facing')

        WITH a, sg, rule, ip
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND (rule.protocol = '-1' OR rule.fromport IS NULL
               OR (coalesce(rule.fromport, 0) <= 0 AND coalesce(rule.toport, 65535) >= 65535))
        RETURN DISTINCT a.id AS account_id, a.name AS account,
               sg.groupid AS group_id, sg.name AS group_name

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_all_ports_open = Rule(
    id="aws_ec2_securitygroup_all_ports_open",
    name="Security Group All Ports Open to Internet",
    description="Security group allows inbound traffic on all ports from 0.0.0.0/0 or ::/0 AND is attached to at least one public resource (public-IP EC2 instance, publicly-accessible RDS/Redshift, public-IP network interface, or internet-facing load balancer). A wildcard group on internal-only resources is not world-open.",
    output_model=AwsEc2SecuritygroupAllPortsOpenOutput,
    facts=(_aws_ec2_securitygroup_all_ports_open_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupAnyPortOpenOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None


_aws_ec2_securitygroup_any_port_open_fact = Fact(
    id="aws_ec2_securitygroup_any_port_open_fact",
    name="SG any wildcard-source ingress",
    description="Security groups with at least one inbound rule from the internet.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)

        MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(pub)
        WHERE (pub:AWSEC2Instance AND pub.publicipaddress IS NOT NULL
               AND NOT coalesce(pub.state, 'running') IN ['terminated', 'shutting-down'])
           OR (pub:AWSRDSInstance AND pub.publicly_accessible = true)
           OR (pub:AWSRedshiftCluster AND pub.publicly_accessible = true)
           OR (pub:AWSNetworkInterface AND pub.public_ip IS NOT NULL)
           OR (pub:AWSLoadBalancerV2 AND pub.scheme = 'internet-facing')
           OR (pub:AWSLoadBalancer AND pub.scheme = 'internet-facing')

        WITH a, sg, rule, ip
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
        RETURN DISTINCT a.id AS account_id, a.name AS account,
               sg.groupid AS group_id, sg.name AS group_name

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)

        MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(pub)
        WHERE (pub:AWSEC2Instance AND pub.publicipaddress IS NOT NULL
               AND NOT coalesce(pub.state, 'running') IN ['terminated', 'shutting-down'])
           OR (pub:AWSRDSInstance AND pub.publicly_accessible = true)
           OR (pub:AWSRedshiftCluster AND pub.publicly_accessible = true)
           OR (pub:AWSNetworkInterface AND pub.public_ip IS NOT NULL)
           OR (pub:AWSLoadBalancerV2 AND pub.scheme = 'internet-facing')
           OR (pub:AWSLoadBalancer AND pub.scheme = 'internet-facing')

        WITH a, sg, rule, ip
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
        RETURN DISTINCT a.id AS account_id, a.name AS account,
               sg.groupid AS group_id, sg.name AS group_name

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id",),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_any_port_open = Rule(
    id="aws_ec2_securitygroup_any_port_open",
    name="Security Group Any Port Open to Internet",
    description="Security group has any inbound rule whose source is 0.0.0.0/0 or ::/0 (any port/protocol) AND is attached to at least one public resource (public-IP EC2 instance, publicly-accessible RDS/Redshift, public-IP network interface, or internet-facing load balancer). A wildcard group on internal-only resources is not world-open. Attachment-scoped: an unattached group is not flagged.",
    output_model=AwsEc2SecuritygroupAnyPortOpenOutput,
    facts=(_aws_ec2_securitygroup_any_port_open_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupCassandraPortsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_cassandra_ports_fact = Fact(
    id="aws_ec2_securitygroup_cassandra_ports_fact",
    name="Security groups with Cassandra ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on Cassandra port(s) [7199, 9160, 8888]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [7199, 9160, 8888] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [7199, 9160, 8888]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_cassandra_ports = Rule(
    id="aws_ec2_securitygroup_cassandra_ports",
    name="Security Group Cassandra Ports Exposed to Internet",
    description="Security groups with Cassandra ports ([7199, 9160, 8888]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupCassandraPortsOutput,
    facts=(_aws_ec2_securitygroup_cassandra_ports_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupElasticsearchKibanaPortsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_elasticsearch_kibana_ports_fact = Fact(
    id="aws_ec2_securitygroup_elasticsearch_kibana_ports_fact",
    name="Security groups with Elasticsearch/Kibana ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on Elasticsearch/Kibana port(s) [9200, 9300, 5601]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [9200, 9300, 5601] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [9200, 9300, 5601]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_elasticsearch_kibana_ports = Rule(
    id="aws_ec2_securitygroup_elasticsearch_kibana_ports",
    name="Security Group Elasticsearch/Kibana Ports Exposed to Internet",
    description="Security groups with Elasticsearch/Kibana ports ([9200, 9300, 5601]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupElasticsearchKibanaPortsOutput,
    facts=(_aws_ec2_securitygroup_elasticsearch_kibana_ports_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupFtpPortsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_ftp_ports_fact = Fact(
    id="aws_ec2_securitygroup_ftp_ports_fact",
    name="Security groups with FTP ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on FTP port(s) [20, 21]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [20, 21] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [20, 21]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_ftp_ports = Rule(
    id="aws_ec2_securitygroup_ftp_ports",
    name="Security Group FTP Ports Exposed to Internet",
    description="Security groups with FTP ports ([20, 21]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupFtpPortsOutput,
    facts=(_aws_ec2_securitygroup_ftp_ports_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupHighRiskTcpPortsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_high_risk_tcp_ports_fact = Fact(
    id="aws_ec2_securitygroup_high_risk_tcp_ports_fact",
    name="Security groups with high-risk TCP ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on high-risk TCP port(s) [25, 110, 135, 143, 445, 3000, 4333, 5000, 5500, 8080, 8088]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [25, 110, 135, 143, 445, 3000, 4333, 5000, 5500, 8080, 8088] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [25, 110, 135, 143, 445, 3000, 4333, 5000, 5500, 8080, 8088]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_high_risk_tcp_ports = Rule(
    id="aws_ec2_securitygroup_high_risk_tcp_ports",
    name="Security Group high-risk TCP Ports Exposed to Internet",
    description="Security groups with high-risk TCP ports ([25, 110, 135, 143, 445, 3000, 4333, 5000, 5500, 8080, 8088]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupHighRiskTcpPortsOutput,
    facts=(_aws_ec2_securitygroup_high_risk_tcp_ports_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupKafkaPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_kafka_port_fact = Fact(
    id="aws_ec2_securitygroup_kafka_port_fact",
    name="Security groups with Kafka ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on Kafka port(s) [9092]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [9092] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [9092]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_kafka_port = Rule(
    id="aws_ec2_securitygroup_kafka_port",
    name="Security Group Kafka Ports Exposed to Internet",
    description="Security groups with Kafka ports ([9092]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupKafkaPortOutput,
    facts=(_aws_ec2_securitygroup_kafka_port_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupLaunchWizardOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    source_cidr: str | None = None
    protocol: str | None = None
    from_port: str | None = None
    to_port: str | None = None
    ingress_count: str | None = None
    egress_count: str | None = None


_aws_ec2_securitygroup_launch_wizard_fact = Fact(
    id="aws_ec2_securitygroup_launch_wizard_fact",
    name="Security groups created by the EC2 launch wizard",
    description="Security groups whose name contains 'launch-wizard' (created by the EC2 console launch wizard; case-insensitive match). Wizard-created groups typically carry ad-hoc rules that bypass reviewed network policy.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)
    WHERE toLower(sg.name) CONTAINS 'launch-wizard'
    RETURN
        a.id AS account_id,
        a.name AS account,
        sg.groupid AS group_id,
        sg.name AS group_name
    ORDER BY account, group_id
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)
    WHERE toLower(sg.name) CONTAINS 'launch-wizard'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("account_id", "group_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_launch_wizard = Rule(
    id="aws_ec2_securitygroup_launch_wizard",
    name="Launch-Wizard Security Groups",
    description="Security groups whose name contains 'launch-wizard' (created by the EC2 console launch wizard; case-insensitive match). Wizard-created groups typically carry ad-hoc rules that bypass reviewed network policy.",
    output_model=AwsEc2SecuritygroupLaunchWizardOutput,
    facts=(_aws_ec2_securitygroup_launch_wizard_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2SecuritygroupMemcachedPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_memcached_port_fact = Fact(
    id="aws_ec2_securitygroup_memcached_port_fact",
    name="Security groups with Memcached ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on Memcached port(s) [11211]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [11211] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [11211]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_memcached_port = Rule(
    id="aws_ec2_securitygroup_memcached_port",
    name="Security Group Memcached Ports Exposed to Internet",
    description="Security groups with Memcached ports ([11211]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupMemcachedPortOutput,
    facts=(_aws_ec2_securitygroup_memcached_port_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupMongodbPortsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_mongodb_ports_fact = Fact(
    id="aws_ec2_securitygroup_mongodb_ports_fact",
    name="Security groups with MongoDB ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on MongoDB port(s) [27017, 27018]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [27017, 27018] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [27017, 27018]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_mongodb_ports = Rule(
    id="aws_ec2_securitygroup_mongodb_ports",
    name="Security Group MongoDB Ports Exposed to Internet",
    description="Security groups with MongoDB ports ([27017, 27018]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupMongodbPortsOutput,
    facts=(_aws_ec2_securitygroup_mongodb_ports_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupMysqlPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_mysql_port_fact = Fact(
    id="aws_ec2_securitygroup_mysql_port_fact",
    name="Security groups with MySQL ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on MySQL port(s) [3306]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [3306] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [3306]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_mysql_port = Rule(
    id="aws_ec2_securitygroup_mysql_port",
    name="Security Group MySQL Ports Exposed to Internet",
    description="Security groups with MySQL ports ([3306]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupMysqlPortOutput,
    facts=(_aws_ec2_securitygroup_mysql_port_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupOraclePortsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_oracle_ports_fact = Fact(
    id="aws_ec2_securitygroup_oracle_ports_fact",
    name="Security groups with Oracle ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on Oracle port(s) [1521, 2483]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [1521, 2483] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [1521, 2483]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_oracle_ports = Rule(
    id="aws_ec2_securitygroup_oracle_ports",
    name="Security Group Oracle Ports Exposed to Internet",
    description="Security groups with Oracle ports ([1521, 2483]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupOraclePortsOutput,
    facts=(_aws_ec2_securitygroup_oracle_ports_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupPostgresPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_postgres_port_fact = Fact(
    id="aws_ec2_securitygroup_postgres_port_fact",
    name="Security groups with Postgres ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on Postgres port(s) [5432]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [5432] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [5432]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_postgres_port = Rule(
    id="aws_ec2_securitygroup_postgres_port",
    name="Security Group Postgres Ports Exposed to Internet",
    description="Security groups with Postgres ports ([5432]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupPostgresPortOutput,
    facts=(_aws_ec2_securitygroup_postgres_port_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupRedisPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_redis_port_fact = Fact(
    id="aws_ec2_securitygroup_redis_port_fact",
    name="Security groups with Redis ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on Redis port(s) [6379]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [6379] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [6379]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_redis_port = Rule(
    id="aws_ec2_securitygroup_redis_port",
    name="Security Group Redis Ports Exposed to Internet",
    description="Security groups with Redis ports ([6379]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupRedisPortOutput,
    facts=(_aws_ec2_securitygroup_redis_port_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupRuleSprawlOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    source_cidr: str | None = None
    protocol: str | None = None
    from_port: str | None = None
    to_port: str | None = None
    ingress_count: str | None = None
    egress_count: str | None = None


_aws_ec2_securitygroup_rule_sprawl_fact = Fact(
    id="aws_ec2_securitygroup_rule_sprawl_fact",
    name="Security groups with excessive ingress/egress rules",
    description="Security groups with more than 50 inbound rules (AWSIpPermissionInbound) or more than 50 outbound rules (AWSIpRule nodes without the AWSIpPermissionInbound label — inbound rules carry both labels, egress rules only AWSIpRule). Threshold is configurable. Rule sprawl indicates unmanaged attack surface and makes reviews error-prone.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)
    OPTIONAL MATCH (in_rule:AWSIpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    OPTIONAL MATCH (out_rule:AWSIpRule)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    WHERE NOT out_rule:AWSIpPermissionInbound
    WITH a, sg, count(DISTINCT in_rule) AS ingress_count, count(DISTINCT out_rule) AS egress_count
    WHERE ingress_count > 50 OR egress_count > 50
    RETURN
        a.id AS account_id,
        a.name AS account,
        sg.groupid AS group_id,
        sg.name AS group_name,
        ingress_count AS ingress_count,
        egress_count AS egress_count
    ORDER BY account, group_id
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)
    OPTIONAL MATCH p2=(in_rule:AWSIpPermissionInbound)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    OPTIONAL MATCH p3=(out_rule:AWSIpRule)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg)
    WHERE NOT out_rule:AWSIpPermissionInbound
    WITH a, sg, count(DISTINCT in_rule) AS ingress_count, count(DISTINCT out_rule) AS egress_count
    WHERE ingress_count > 50 OR egress_count > 50
    RETURN a, sg, ingress_count, egress_count
    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("account_id", "group_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_rule_sprawl = Rule(
    id="aws_ec2_securitygroup_rule_sprawl",
    name="Security Group Rule Sprawl",
    description="Security groups with more than 50 inbound rules (AWSIpPermissionInbound) or more than 50 outbound rules (AWSIpRule nodes without the AWSIpPermissionInbound label — inbound rules carry both labels, egress rules only AWSIpRule). Threshold is configurable. Rule sprawl indicates unmanaged attack surface and makes reviews error-prone.",
    output_model=AwsEc2SecuritygroupRuleSprawlOutput,
    facts=(_aws_ec2_securitygroup_rule_sprawl_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2SecuritygroupSpecificPublicIpOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    source_cidr: str | None = None
    protocol: str | None = None
    from_port: str | None = None
    to_port: str | None = None
    ingress_count: str | None = None
    egress_count: str | None = None


_aws_ec2_securitygroup_specific_public_ip_fact = Fact(
    id="aws_ec2_securitygroup_specific_public_ip_fact",
    name="Security groups open to a specific public IP on any port",
    description="Security groups with an ingress rule (any port/protocol) whose AWSIpRange source is a specific globally-routable CIDR: not 0.0.0.0/0 or ::/0, not RFC1918 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), and not loopback, link-local, CGNAT (100.64.0.0/10), multicast/reserved (>=224), IPv6 loopback/link-local/ULA. LIMITATION: public-vs-private classification is a string heuristic in Cypher (prefix tests plus second-octet range tests); unusual non-global ranges and IPv6 special-purpose prefixes beyond those listed may be misclassified.",
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
    WHERE ip.range IS NOT NULL
      AND NOT ip.range IN ['0.0.0.0/0', '::/0', '::1/128']
      AND NOT ip.range STARTS WITH '10.'
      AND NOT ip.range STARTS WITH '192.168.'
      AND NOT (ip.range STARTS WITH '172.'
               AND toInteger(split(ip.range, '.')[1]) >= 16
               AND toInteger(split(ip.range, '.')[1]) <= 31)
      AND NOT ip.range STARTS WITH '127.'
      AND NOT ip.range STARTS WITH '169.254.'
      AND NOT (ip.range STARTS WITH '100.'
               AND toInteger(split(ip.range, '.')[1]) >= 64
               AND toInteger(split(ip.range, '.')[1]) <= 127)
      AND NOT (ip.range CONTAINS '.' AND toInteger(split(ip.range, '.')[0]) >= 224)
      AND NOT toLower(ip.range) STARTS WITH 'fe80'
      AND NOT toLower(ip.range) STARTS WITH 'fc'
      AND NOT toLower(ip.range) STARTS WITH 'fd'
    RETURN DISTINCT
        a.id AS account_id,
        a.name AS account,
        sg.groupid AS group_id,
        sg.name AS group_name,
        ip.range AS source_cidr,
        rule.protocol AS protocol,
        rule.fromport AS from_port,
        rule.toport AS to_port
    ORDER BY account, group_id, source_cidr
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
    WHERE ip.range IS NOT NULL
      AND NOT ip.range IN ['0.0.0.0/0', '::/0', '::1/128']
      AND NOT ip.range STARTS WITH '10.'
      AND NOT ip.range STARTS WITH '192.168.'
      AND NOT (ip.range STARTS WITH '172.'
               AND toInteger(split(ip.range, '.')[1]) >= 16
               AND toInteger(split(ip.range, '.')[1]) <= 31)
      AND NOT ip.range STARTS WITH '127.'
      AND NOT ip.range STARTS WITH '169.254.'
      AND NOT (ip.range STARTS WITH '100.'
               AND toInteger(split(ip.range, '.')[1]) >= 64
               AND toInteger(split(ip.range, '.')[1]) <= 127)
      AND NOT (ip.range CONTAINS '.' AND toInteger(split(ip.range, '.')[0]) >= 224)
      AND NOT toLower(ip.range) STARTS WITH 'fe80'
      AND NOT toLower(ip.range) STARTS WITH 'fc'
      AND NOT toLower(ip.range) STARTS WITH 'fd'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=(
        "account_id",
        "group_id",
        "source_cidr",
        "protocol",
        "from_port",
        "to_port",
    ),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_specific_public_ip = Rule(
    id="aws_ec2_securitygroup_specific_public_ip",
    name="Security Groups Open to a Specific Public IP",
    description="Security groups with an ingress rule (any port/protocol) whose AWSIpRange source is a specific globally-routable CIDR: not 0.0.0.0/0 or ::/0, not RFC1918 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), and not loopback, link-local, CGNAT (100.64.0.0/10), multicast/reserved (>=224), IPv6 loopback/link-local/ULA. LIMITATION: public-vs-private classification is a string heuristic in Cypher (prefix tests plus second-octet range tests); unusual non-global ranges and IPv6 special-purpose prefixes beyond those listed may be misclassified.",
    output_model=AwsEc2SecuritygroupSpecificPublicIpOutput,
    facts=(_aws_ec2_securitygroup_specific_public_ip_fact,),
    tags=("ec2", "security", "cspm", "medium"),
    version="0.1.0",
)


class AwsEc2SecuritygroupSqlserverPortsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_sqlserver_ports_fact = Fact(
    id="aws_ec2_securitygroup_sqlserver_ports_fact",
    name="Security groups with SQL Server ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on SQL Server port(s) [1433, 1434]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [1433, 1434] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [1433, 1434]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_sqlserver_ports = Rule(
    id="aws_ec2_securitygroup_sqlserver_ports",
    name="Security Group SQL Server Ports Exposed to Internet",
    description="Security groups with SQL Server ports ([1433, 1434]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupSqlserverPortsOutput,
    facts=(_aws_ec2_securitygroup_sqlserver_ports_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupTelnetPortOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    port: str | None = None


_aws_ec2_securitygroup_telnet_port_fact = Fact(
    id="aws_ec2_securitygroup_telnet_port_fact",
    name="Security groups with Telnet ports open to the internet",
    description="Security groups whose inbound rule allows TCP (or all-protocol) traffic from 0.0.0.0/0 or ::/0 on Telnet port(s) [23]. Assessed at the security group level (no instance join). Port ranges and all-ports rules are honoured.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
        UNWIND [23] AS check_port
        WITH a, sg, rule, check_port
        WHERE rule.fromport IS NULL
           OR (
             coalesce(rule.fromport, 0) <= check_port
             AND coalesce(rule.toport, rule.fromport, 0) >= check_port
           )
        RETURN DISTINCT
            a.id AS account_id,
            a.name AS account,
            sg.groupid AS group_id,
            sg.name AS group_name,
            check_port AS port
        ORDER BY account, group_id, port

    """,
    cypher_visual_query="""
        MATCH p=(a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
        MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)
        WHERE ip.range IN ['0.0.0.0/0', '::/0']
          AND coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
          AND (
            rule.fromport IS NULL
            OR ANY(check_port IN [23]
                   WHERE coalesce(rule.fromport, 0) <= check_port
                     AND coalesce(rule.toport, rule.fromport, 0) >= check_port)
          )
        RETURN *

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "port"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_telnet_port = Rule(
    id="aws_ec2_securitygroup_telnet_port",
    name="Security Group Telnet Ports Exposed to Internet",
    description="Security groups with Telnet ports ([23]) open to the internet (0.0.0.0/0 or ::/0). SG-level check.",
    output_model=AwsEc2SecuritygroupTelnetPortOutput,
    facts=(_aws_ec2_securitygroup_telnet_port_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm"),
    version="0.1.0",
)


class AwsEc2SecuritygroupUnusedOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None


_aws_ec2_securitygroup_unused_fact = Fact(
    id="aws_ec2_securitygroup_unused_fact",
    name="Non-default SG without attachments",
    description="Non-default SGs with no ENI/instance membership and no inbound cross-reference from other SGs.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)
        WHERE sg.name <> 'default'
          AND NOT EXISTS { MATCH (:AWSNetworkInterface)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg) }
          AND NOT EXISTS { MATCH (:AWSEC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg) }
          AND NOT EXISTS { MATCH (:AWSEC2SecurityGroup)-[:ALLOWS_TRAFFIC_FROM]->(sg) }
        RETURN a.id AS account_id, a.name AS account,
               sg.groupid AS group_id, sg.name AS group_name

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)
        WHERE sg.name <> 'default'
          AND NOT EXISTS { MATCH (:AWSNetworkInterface)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg) }
          AND NOT EXISTS { MATCH (:AWSEC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg) }
          AND NOT EXISTS { MATCH (:AWSEC2SecurityGroup)-[:ALLOWS_TRAFFIC_FROM]->(sg) }
        RETURN a.id AS account_id, a.name AS account,
               sg.groupid AS group_id, sg.name AS group_name

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) WHERE sg.name <> 'default' RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("account_id", "account", "group_id"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_unused = Rule(
    id="aws_ec2_securitygroup_unused",
    name="Unused Non-Default Security Group",
    description="Non-default security group (name<>'default') with no attachments: no network interface or instance MEMBER_OF_EC2_SECURITY_GROUP edge, and not referenced as a source by another security group's inbound rules (ALLOWS_TRAFFIC_FROM). LIMITATION: Lambda/Batch associations are approximated through ENI attachments (Lambda VPC creates ENIs); no direct Lambda-SG relationship exists in the graph and Batch is not synced, so a residual false-positive risk remains.",
    output_model=AwsEc2SecuritygroupUnusedOutput,
    facts=(_aws_ec2_securitygroup_unused_fact,),
    tags=("ec2", "network", "hygiene", "cspm", "low"),
    version="0.1.0",
)


class AwsEc2SecuritygroupWidePublicCidrsOutput(Finding):
    account_id: str | None = None
    account: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    cidr: str | None = None


_aws_ec2_securitygroup_wide_public_cidrs_fact = Fact(
    id="aws_ec2_securitygroup_wide_public_cidrs_fact",
    name="SG wide public CIDRs",
    description="Security groups with a wide public IPv4 CIDR on ingress or egress.",
    cypher_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpRule)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)

        MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(pub)
        WHERE (pub:AWSEC2Instance AND pub.publicipaddress IS NOT NULL
               AND NOT coalesce(pub.state, 'running') IN ['terminated', 'shutting-down'])
           OR (pub:AWSRDSInstance AND pub.publicly_accessible = true)
           OR (pub:AWSRedshiftCluster AND pub.publicly_accessible = true)
           OR (pub:AWSNetworkInterface AND pub.public_ip IS NOT NULL)
           OR (pub:AWSLoadBalancerV2 AND pub.scheme = 'internet-facing')
           OR (pub:AWSLoadBalancer AND pub.scheme = 'internet-facing')

        WITH a, sg, rule, ip
        WHERE ip.range CONTAINS '/'
          AND NOT ip.range CONTAINS ':'
          AND toInteger(split(ip.range, '/')[1]) >= 1
          AND toInteger(split(ip.range, '/')[1]) < 24
          AND NOT (ip.range STARTS WITH '10.'
                   OR ip.range STARTS WITH '192.168.'
                   OR (ip.range STARTS WITH '172.'
                       AND toInteger(split(ip.range, '.')[1]) >= 16
                       AND toInteger(split(ip.range, '.')[1]) <= 31))
        RETURN DISTINCT a.id AS account_id, a.name AS account,
               sg.groupid AS group_id, sg.name AS group_name, ip.range AS cidr

    """,
    cypher_visual_query="""
        MATCH (a:AWSAccount)-[:RESOURCE]->(sg:AWSEC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpRule)
        MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange)

        MATCH (sg)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(pub)
        WHERE (pub:AWSEC2Instance AND pub.publicipaddress IS NOT NULL
               AND NOT coalesce(pub.state, 'running') IN ['terminated', 'shutting-down'])
           OR (pub:AWSRDSInstance AND pub.publicly_accessible = true)
           OR (pub:AWSRedshiftCluster AND pub.publicly_accessible = true)
           OR (pub:AWSNetworkInterface AND pub.public_ip IS NOT NULL)
           OR (pub:AWSLoadBalancerV2 AND pub.scheme = 'internet-facing')
           OR (pub:AWSLoadBalancer AND pub.scheme = 'internet-facing')

        WITH a, sg, rule, ip
        WHERE ip.range CONTAINS '/'
          AND NOT ip.range CONTAINS ':'
          AND toInteger(split(ip.range, '/')[1]) >= 1
          AND toInteger(split(ip.range, '/')[1]) < 24
          AND NOT (ip.range STARTS WITH '10.'
                   OR ip.range STARTS WITH '192.168.'
                   OR (ip.range STARTS WITH '172.'
                       AND toInteger(split(ip.range, '.')[1]) >= 16
                       AND toInteger(split(ip.range, '.')[1]) <= 31))
        RETURN DISTINCT a.id AS account_id, a.name AS account,
               sg.groupid AS group_id, sg.name AS group_name, ip.range AS cidr

    """,
    cypher_count_query="""
    MATCH (sg:AWSEC2SecurityGroup) RETURN COUNT(sg) AS count
    """,
    asset_label="AWSEC2SecurityGroup",
    asset_id_field="group_id",
    identity_fields=("group_id", "cidr"),
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


aws_ec2_securitygroup_wide_public_cidrs = Rule(
    id="aws_ec2_securitygroup_wide_public_cidrs",
    name="Security Group Wide Public IPv4 CIDRs",
    description="Security group has an ingress or egress rule whose AWSIpRange is a public IPv4 CIDR with prefix length /1-/23 (toInteger(split(range,'/')[1]) < 24), excluding RFC1918 private ranges, AND is attached to a public resource (public-IP EC2/RDS/Redshift/ENI or internet-facing ELB). Both directions are covered by matching the shared AWSIpRule label (inbound AWSIpPermissionInbound nodes also carry it). LIMITATION: RFC1918 exclusion is a best-effort octet approximation (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16); other special-use ranges (e.g. 100.64.0.0/10) are not classified, and IPv6 wide ranges are not yet included.",
    output_model=AwsEc2SecuritygroupWidePublicCidrsOutput,
    facts=(_aws_ec2_securitygroup_wide_public_cidrs_fact,),
    tags=("infrastructure", "network", "attack_surface", "cspm", "best-effort"),
    version="0.1.0",
)
