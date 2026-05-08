from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule

# GCP Facts
_gcp_instance_internet_exposed = Fact(
    id="gcp_instance_internet_exposed",
    name="Internet-Exposed GCE Instances on Common Management Ports",
    description=(
        "GCE instances with a public IP (ONE_TO_ONE_NAT access config) whose "
        "VPC has an enabled INGRESS firewall allowing 0.0.0.0/0 on TCP (or "
        "all protocols) to a management port (22, 3389, 3306, 5432, 6379, "
        "9200, 27017). Port ranges (fromport/toport) covering a management "
        "port are detected. Mirrors the AWS EC2-on-management-ports "
        "semantics; matches are widened by VPC scope and do not currently "
        "account for firewall target_tags or target SAs, so a VPC-wide "
        "allow may produce findings on tagged instances that the firewall "
        "does not actually apply to."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (nic:GCPNetworkInterface)-[:NETWORK_INTERFACE]-(instance)
    MATCH (ac:GCPNicAccessConfig)-[:RESOURCE]-(nic)
    MATCH (nic)-[:PART_OF_SUBNET]->(subnet:GCPSubnet)<-[:HAS]-(vpc:GCPVpc)
    MATCH (vpc)-[:RESOURCE]->(fw:GCPFirewall)<-[:ALLOWED_BY]-(rule:GCPIpRule)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:GCPIpRange{range:'0.0.0.0/0'})
    WITH project, instance, nic, ac, fw, rule
    UNWIND [22, 3389, 3306, 5432, 6379, 9200, 27017] AS managed_port
    WITH project, instance, nic, ac, fw, rule, managed_port
    WHERE ac.type = 'ONE_TO_ONE_NAT'
      AND ac.public_ip IS NOT NULL
      AND coalesce(fw.disabled, false) = false
      AND fw.direction = 'INGRESS'
      AND (
        rule.protocol = 'all'
        OR (
          rule.protocol = 'tcp'
          AND coalesce(rule.fromport, 0) <= managed_port
          AND coalesce(rule.toport, rule.fromport, 0) >= managed_port
        )
      )
    RETURN
        project.id AS account_id,
        project.id AS account,
        instance.id AS instance_id,
        instance.name AS instance,
        managed_port AS port,
        fw.name AS security_group
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH p2=(nic:GCPNetworkInterface)-[:NETWORK_INTERFACE]-(instance)
    MATCH p3=(ac:GCPNicAccessConfig)-[:RESOURCE]-(nic)
    MATCH p4=(nic)-[:PART_OF_SUBNET]->(subnet:GCPSubnet)<-[:HAS]-(vpc:GCPVpc)
    MATCH p5=(vpc)-[:RESOURCE]->(fw:GCPFirewall)<-[:ALLOWED_BY]-(rule:GCPIpRule)
    MATCH p6=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:GCPIpRange{range:'0.0.0.0/0'})
    WHERE ac.type = 'ONE_TO_ONE_NAT'
      AND ac.public_ip IS NOT NULL
      AND coalesce(fw.disabled, false) = false
      AND fw.direction = 'INGRESS'
      AND (
        rule.protocol = 'all'
        OR (
          rule.protocol = 'tcp'
          AND any(
            managed_port IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
            WHERE coalesce(rule.fromport, 0) <= managed_port
              AND coalesce(rule.toport, rule.fromport, 0) >= managed_port
          )
        )
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)


# Azure Facts
_azure_vm_internet_exposed = Fact(
    id="azure_vm_internet_exposed",
    name="Internet-Exposed Azure VMs on Common Management Ports",
    description=(
        "Azure Virtual Machines reachable from the public internet on ports "
        "22, 3389, 3306, 5432, 6379, 9200, or 27017. A VM is considered "
        "internet-reachable when it has a NIC associated with a public IP and "
        "an inbound NSG rule (NIC-level or subnet-level) that allows traffic "
        "from `*` / `Internet` / `0.0.0.0/0` on a TCP / `*` protocol covering "
        "one of those ports. Effective evaluation does not currently account "
        "for higher-priority deny rules that may shadow the allow."
    ),
    cypher_query="""
    MATCH (sub:AzureSubscription)-[:RESOURCE]->(vm:AzureVirtualMachine)
    MATCH (vm)<-[:ATTACHED_TO]-(nic:AzureNetworkInterface)
    MATCH (nic)-[:ASSOCIATED_WITH]->(pip:AzurePublicIPAddress)
    WHERE pip.ip_address IS NOT NULL
    MATCH (rule:AzureNetworkSecurityRule:IpPermissionInbound)-[:MEMBER_OF_AZURE_NSG]->(nsg:AzureNetworkSecurityGroup)
    WHERE rule.access = 'Allow'
      AND rule.protocol IN ['Tcp', '*']
      AND (
        EXISTS { (nic)-[:ASSOCIATED_WITH]->(nsg) }
        OR EXISTS { (nic)-[:ATTACHED_TO]->(:AzureSubnet)-[:ASSOCIATED_WITH]->(nsg) }
      )
      AND (
        coalesce(rule.source_address_prefix, '') IN ['*', 'Internet', '0.0.0.0/0']
        OR ANY(
          src IN coalesce(rule.source_address_prefixes, [])
          WHERE src IN ['*', 'Internet', '0.0.0.0/0']
        )
      )
    UNWIND [22, 3389, 3306, 5432, 6379, 9200, 27017] AS managed_port
    WITH sub, vm, nsg, rule, managed_port,
         coalesce(rule.destination_port_range, '') AS port_single,
         coalesce(rule.destination_port_ranges, []) AS port_list
    WHERE port_single = '*'
       OR port_single = toString(managed_port)
       OR (
         port_single CONTAINS '-'
         AND toInteger(split(port_single, '-')[0]) <= managed_port
         AND toInteger(split(port_single, '-')[1]) >= managed_port
       )
       OR ANY(
         p IN port_list
         WHERE p = '*'
            OR p = toString(managed_port)
            OR (
              p CONTAINS '-'
              AND toInteger(split(p, '-')[0]) <= managed_port
              AND toInteger(split(p, '-')[1]) >= managed_port
            )
       )
    RETURN DISTINCT
        sub.id AS account_id,
        sub.id AS account,
        vm.id AS instance_id,
        vm.name AS instance,
        managed_port AS port,
        nsg.name AS security_group
    """,
    cypher_visual_query="""
    MATCH p1=(sub:AzureSubscription)-[:RESOURCE]->(vm:AzureVirtualMachine)
    MATCH p2=(vm)<-[:ATTACHED_TO]-(nic:AzureNetworkInterface)-[:ASSOCIATED_WITH]->(pip:AzurePublicIPAddress)
    MATCH p3=(rule:AzureNetworkSecurityRule:IpPermissionInbound)-[:MEMBER_OF_AZURE_NSG]->(nsg:AzureNetworkSecurityGroup)
    WHERE pip.ip_address IS NOT NULL
      AND rule.access = 'Allow'
      AND rule.protocol IN ['Tcp', '*']
      AND (
        EXISTS { (nic)-[:ASSOCIATED_WITH]->(nsg) }
        OR EXISTS { (nic)-[:ATTACHED_TO]->(:AzureSubnet)-[:ASSOCIATED_WITH]->(nsg) }
      )
      AND (
        coalesce(rule.source_address_prefix, '') IN ['*', 'Internet', '0.0.0.0/0']
        OR ANY(src IN coalesce(rule.source_address_prefixes, [])
               WHERE src IN ['*', 'Internet', '0.0.0.0/0'])
      )
      // Mirror the finding query: keep only rules whose destination port
      // (or port range / list) covers a management port.
      AND ANY(managed_port IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
              WHERE
                coalesce(rule.destination_port_range, '') = '*'
                OR coalesce(rule.destination_port_range, '') = toString(managed_port)
                OR (
                  coalesce(rule.destination_port_range, '') CONTAINS '-'
                  AND toInteger(split(rule.destination_port_range, '-')[0]) <= managed_port
                  AND toInteger(split(rule.destination_port_range, '-')[1]) >= managed_port
                )
                OR ANY(p IN coalesce(rule.destination_port_ranges, [])
                       WHERE p = '*'
                          OR p = toString(managed_port)
                          OR (
                            p CONTAINS '-'
                            AND toInteger(split(p, '-')[0]) <= managed_port
                            AND toInteger(split(p, '-')[1]) >= managed_port
                          ))
              )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (vm:AzureVirtualMachine)
    RETURN COUNT(vm) AS count
    """,
    asset_id_field="instance_id",
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)


# AWS Facts
_aws_ec2_instance_internet_exposed = Fact(
    id="aws_ec2_instance_internet_exposed",
    name="Internet-Exposed EC2 Instances on Common Management Ports",
    description=(
        "EC2 instances exposed to the internet on ports 22, 3389, 3306, "
        "5432, 6379, 9200, 27017. Matches inbound 0.0.0.0/0 SG rules over "
        "TCP (or `-1` / `all` covering every protocol) whose port range "
        "covers any of those ports, including all-ports rules "
        "(`fromport` IS NULL) and ranges like 0-65535. UDP / ICMP rules "
        "are intentionally skipped so a wide-open UDP rule does not flag "
        "TCP management ports. Aligned with the GCP and Azure facts."
    ),
    cypher_query="""
    MATCH (a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
    MATCH (rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange{range:'0.0.0.0/0'})
    WHERE coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
    UNWIND [22, 3389, 3306, 5432, 6379, 9200, 27017] AS managed_port
    WITH a, ec2, sg, rule, managed_port
    WHERE rule.fromport IS NULL
       OR (
         coalesce(rule.fromport, 0) <= managed_port
         AND coalesce(rule.toport, rule.fromport, 0) >= managed_port
       )
    RETURN DISTINCT
        a.id AS account_id,
        a.name AS account,
        ec2.instanceid AS instance_id,
        managed_port AS port,
        sg.groupid AS security_group
    ORDER BY account, instance_id, port, security_group
    """,
    cypher_visual_query="""
    MATCH p=(a:AWSAccount)-[:RESOURCE]->(ec2:EC2Instance)-[:MEMBER_OF_EC2_SECURITY_GROUP]->(sg:EC2SecurityGroup)<-[:MEMBER_OF_EC2_SECURITY_GROUP]-(rule:AWSIpPermissionInbound)
    MATCH p2=(rule)<-[:MEMBER_OF_IP_RULE]-(ip:AWSIpRange{range:'0.0.0.0/0'})
    WHERE coalesce(rule.protocol, '') IN ['tcp', '-1', 'all']
      AND (
        rule.fromport IS NULL
        OR ANY(managed_port IN [22, 3389, 3306, 5432, 6379, 9200, 27017]
               WHERE coalesce(rule.fromport, 0) <= managed_port
                 AND coalesce(rule.toport, rule.fromport, 0) >= managed_port)
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (ec2:EC2Instance)
    RETURN COUNT(ec2) AS count
    """,
    asset_id_field="instance_id",
    module=Module.AWS,
    maturity=Maturity.EXPERIMENTAL,
)


# Rule
class ComputeInstanceExposed(Finding):
    instance: str | None = None
    instance_id: str | None = None
    account: str | None = None
    account_id: str | None = None
    port: int | None = None
    security_group: str | None = None


compute_instance_exposed = Rule(
    id="compute_instance_exposed",
    name="Internet-Exposed Compute Instances on Common Management Ports",
    description=(
        "Compute instances exposed to the internet on ports 22, 3389, 3306, 5432, 6379, 9200, 27017"
    ),
    output_model=ComputeInstanceExposed,
    facts=(
        _aws_ec2_instance_internet_exposed,
        _azure_vm_internet_exposed,
        _gcp_instance_internet_exposed,
    ),
    tags=(
        "infrastructure",
        "compute",
        "attack_surface",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="0.1.0",
)
