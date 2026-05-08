"""
CIS GCP Security Checks

Implements CIS GCP Foundations Benchmark Sections 3-5: Networking, Compute, and Storage
Based on CIS Google Cloud Platform Foundation Benchmark v4.0.0

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
        text="CIS Google Cloud Platform Foundation Benchmark v4.0.0",
        url="https://www.cisecurity.org/benchmark/google_cloud_computing_platform",
    ),
    RuleReference(
        text="GCP VPC Network Security Best Practices",
        url="https://cloud.google.com/vpc/docs/firewalls",
    ),
]


# =============================================================================
# CIS GCP 3.1: Default network should not exist
# Main node: GCPVpc
# =============================================================================
class DefaultNetworkExistsOutput(Finding):
    """Output model for default network check."""

    vpc_name: str | None = None
    vpc_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None


_gcp_default_network_exists = Fact(
    id="gcp_default_network_exists",
    name="GCP projects with default network",
    description=(
        "Detects GCP projects that still contain the default network. The default "
        "network has preconfigured firewall rules that may not meet security requirements. "
        "It is recommended to delete the default network and create custom networks "
        "with appropriate firewall rules."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)
    WHERE vpc.name = 'default'
    RETURN
        vpc.name AS vpc_name,
        vpc.id AS vpc_id,
        project.id AS project_id,
        project.displayname AS project_name
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)
    WHERE vpc.name = 'default'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (vpc:GCPVpc)
    RETURN COUNT(vpc) AS count
    """,
    asset_id_field="vpc_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_3_1_default_network = Rule(
    id="cis_gcp_3_1_default_network",
    name="CIS GCP 3.1: Default Network Exists",
    description=(
        "The default network should be deleted from GCP projects. It includes "
        "preconfigured firewall rules that may not meet security requirements."
    ),
    output_model=DefaultNetworkExistsOutput,
    facts=(_gcp_default_network_exists,),
    tags=(
        "networking",
        "vpc",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="3.1",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 3.6: SSH should not be open to the internet
# Main node: GCPFirewall
# =============================================================================
class UnrestrictedSshOutput(Finding):
    """Output model for unrestricted SSH check."""

    firewall_name: str | None = None
    firewall_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    firewall_rule_id: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    source_range: str | None = None


_gcp_unrestricted_ssh = Fact(
    id="gcp_unrestricted_ssh",
    name="GCP firewall rules allow unrestricted SSH access",
    description=(
        "Detects firewall rules that allow SSH access (port 22) from any IP address "
        "(0.0.0.0/0 or ::/0). Unrestricted SSH access increases the risk of "
        "unauthorized access and brute force attacks."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)-[:RESOURCE]->(fw:GCPFirewall {direction: 'INGRESS'})
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:GCPIpRange)
    WHERE range.range IN ['0.0.0.0/0', '::/0']
      AND coalesce(fw.disabled, false) = false
      AND (
        (rule.protocol = 'tcp' AND rule.fromport <= 22 AND rule.toport >= 22)
        OR rule.protocol = 'all'
      )
    RETURN
        fw.name AS firewall_name,
        fw.id AS firewall_id,
        project.id AS project_id,
        project.displayname AS project_name,
        rule.ruleid AS firewall_rule_id,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        range.range AS source_range
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)-[:RESOURCE]->(fw:GCPFirewall {direction: 'INGRESS'})
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:GCPIpRange)
    WHERE range.range IN ['0.0.0.0/0', '::/0']
      AND coalesce(fw.disabled, false) = false
      AND (
        (rule.protocol = 'tcp' AND rule.fromport <= 22 AND rule.toport >= 22)
        OR rule.protocol = 'all'
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (fw:GCPFirewall)
    RETURN COUNT(fw) AS count
    """,
    asset_id_field="firewall_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_3_6_unrestricted_ssh = Rule(
    id="cis_gcp_3_6_unrestricted_ssh",
    name="CIS GCP 3.6: Unrestricted SSH Access",
    description=(
        "Firewall rules should not allow SSH access (port 22) from any IP address. "
        "Unrestricted SSH access increases the risk of unauthorized access."
    ),
    output_model=UnrestrictedSshOutput,
    facts=(_gcp_unrestricted_ssh,),
    tags=(
        "networking",
        "firewall",
        "ssh",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="3.6",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 3.7: RDP should not be open to the internet
# Main node: GCPFirewall
# =============================================================================
class UnrestrictedRdpOutput(Finding):
    """Output model for unrestricted RDP check."""

    firewall_name: str | None = None
    firewall_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    firewall_rule_id: str | None = None
    from_port: int | None = None
    to_port: int | None = None
    source_range: str | None = None


_gcp_unrestricted_rdp = Fact(
    id="gcp_unrestricted_rdp",
    name="GCP firewall rules allow unrestricted RDP access",
    description=(
        "Detects firewall rules that allow RDP access (port 3389) from any IP address "
        "(0.0.0.0/0 or ::/0). Unrestricted RDP access increases the risk of "
        "unauthorized access and brute force attacks on Windows systems."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)-[:RESOURCE]->(fw:GCPFirewall {direction: 'INGRESS'})
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:GCPIpRange)
    WHERE range.range IN ['0.0.0.0/0', '::/0']
      AND coalesce(fw.disabled, false) = false
      AND (
        (rule.protocol = 'tcp' AND rule.fromport <= 3389 AND rule.toport >= 3389)
        OR rule.protocol = 'all'
      )
    RETURN
        fw.name AS firewall_name,
        fw.id AS firewall_id,
        project.id AS project_id,
        project.displayname AS project_name,
        rule.ruleid AS firewall_rule_id,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        range.range AS source_range
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)-[:RESOURCE]->(fw:GCPFirewall {direction: 'INGRESS'})
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:GCPIpRange)
    WHERE range.range IN ['0.0.0.0/0', '::/0']
      AND coalesce(fw.disabled, false) = false
      AND (
        (rule.protocol = 'tcp' AND rule.fromport <= 3389 AND rule.toport >= 3389)
        OR rule.protocol = 'all'
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (fw:GCPFirewall)
    RETURN COUNT(fw) AS count
    """,
    asset_id_field="firewall_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_3_7_unrestricted_rdp = Rule(
    id="cis_gcp_3_7_unrestricted_rdp",
    name="CIS GCP 3.7: Unrestricted RDP Access",
    description=(
        "Firewall rules should not allow RDP access (port 3389) from any IP address. "
        "Unrestricted RDP access increases the risk of unauthorized access."
    ),
    output_model=UnrestrictedRdpOutput,
    facts=(_gcp_unrestricted_rdp,),
    tags=(
        "networking",
        "firewall",
        "rdp",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="3.7",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 4.9: Compute instances should not have public IPs
# Main node: GCPInstance
# =============================================================================
class InstancePublicIpOutput(Finding):
    """Output model for compute instance public IP check."""

    instance_name: str | None = None
    instance_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    external_ip: str | None = None
    network_tier: str | None = None


_gcp_instance_public_ip = Fact(
    id="gcp_instance_public_ip",
    name="GCP compute instances with public IPs",
    description=(
        "Detects VM instances with public NAT IPs attached to their network interfaces. "
        "Compute instances should not have public IP addresses to reduce the attack "
        "surface. Use Cloud NAT or bastion hosts for outbound and inbound access."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(access:GCPNicAccessConfig)
    WHERE access.public_ip IS NOT NULL
    RETURN
        instance.instancename AS instance_name,
        instance.id AS instance_id,
        project.id AS project_id,
        project.displayname AS project_name,
        access.public_ip AS external_ip,
        access.network_tier AS network_tier
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)-[:RESOURCE]->(access:GCPNicAccessConfig)
    WHERE access.public_ip IS NOT NULL
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_9_public_ip = Rule(
    id="cis_gcp_4_9_public_ip",
    name="CIS GCP 4.9: Compute Instance Public IPs",
    description=(
        "VM instances should not have external IPs attached to NICs. Use Cloud NAT "
        "or bastion hosts instead to reduce the attack surface."
    ),
    output_model=InstancePublicIpOutput,
    facts=(_gcp_instance_public_ip,),
    tags=(
        "compute",
        "networking",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.9",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 4.11: Compute instances have Confidential Computing enabled
# Main node: GCPInstance
# =============================================================================
class InstanceConfidentialComputeDisabledOutput(Finding):
    instance_name: str | None = None
    instance_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    machine_type: str | None = None
    enable_confidential_compute: bool | None = None


_gcp_instance_confidential_compute_disabled = Fact(
    id="gcp_instance_confidential_compute_disabled",
    name="GCP compute instances without Confidential Computing enabled",
    description=(
        "Detects eligible Compute Engine instances in supported machine families "
        "where Confidential Computing is not enabled."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND (
        instance.machine_type STARTS WITH 'n2d-'
        OR instance.machine_type STARTS WITH 'c2d-'
      )
      AND coalesce(instance.enable_confidential_compute, false) = false
    RETURN
        instance.instancename AS instance_name,
        instance.id AS instance_id,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.machine_type AS machine_type,
        instance.enable_confidential_compute AS enable_confidential_compute
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND (
        instance.machine_type STARTS WITH 'n2d-'
        OR instance.machine_type STARTS WITH 'c2d-'
      )
      AND coalesce(instance.enable_confidential_compute, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND (
        instance.machine_type STARTS WITH 'n2d-'
        OR instance.machine_type STARTS WITH 'c2d-'
      )
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_11_confidential_compute = Rule(
    id="cis_gcp_4_11_confidential_compute",
    name="CIS GCP 4.11: Instances Without Confidential Computing Enabled",
    description=(
        "Eligible Compute Engine instances should enable Confidential Computing."
    ),
    output_model=InstanceConfidentialComputeDisabledOutput,
    facts=(_gcp_instance_confidential_compute_disabled,),
    tags=(
        "compute",
        "confidential-computing",
        "encryption",
        "stride:information_disclosure",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.11",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 3.3: DNSSEC should be enabled for public Cloud DNS zones
# Main node: GCPDNSZone
# =============================================================================
class DnssecDisabledOutput(Finding):
    zone_id: str | None = None
    zone_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    dns_name: str | None = None


_gcp_dnssec_disabled = Fact(
    id="gcp_dnssec_disabled",
    name="GCP public DNS zones without DNSSEC enabled",
    description="Detects public Cloud DNS zones where DNSSEC is not enabled.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
      AND coalesce(zone.dnssec_state, 'off') <> 'on'
    RETURN
        zone.id AS zone_id,
        zone.name AS zone_name,
        project.id AS project_id,
        project.displayname AS project_name,
        zone.dns_name AS dns_name
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
      AND coalesce(zone.dnssec_state, 'off') <> 'on'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
    RETURN COUNT(zone) AS count
    """,
    asset_id_field="zone_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_3_3_dnssec_enabled = Rule(
    id="cis_gcp_3_3_dnssec_enabled",
    name="CIS GCP 3.3: Cloud DNS DNSSEC Disabled",
    description="Public Cloud DNS zones should have DNSSEC enabled.",
    output_model=DnssecDisabledOutput,
    facts=(_gcp_dnssec_disabled,),
    tags=("dns", "dnssec", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="3.3",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# TODO: CIS GCP 3.3: Partial control coverage
# Missing datamodel or evidence: imported public registrar delegation state; current rule only validates Cloud DNS managed-zone DNSSEC state
# =============================================================================


# =============================================================================
# CIS GCP 3.4: RSASHA1 should not be used for the DNSSEC key-signing key
# Main node: GCPDNSZone
# =============================================================================
class DnssecWeakKskOutput(Finding):
    zone_id: str | None = None
    zone_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    dns_name: str | None = None
    dnssec_key_signing_algorithm: str | None = None


_gcp_dnssec_weak_ksk = Fact(
    id="gcp_dnssec_weak_ksk",
    name="GCP public DNS zones using RSASHA1 for DNSSEC key-signing",
    description="Detects public Cloud DNS zones whose DNSSEC key-signing key uses RSASHA1.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
      AND coalesce(zone.dnssec_state, 'off') = 'on'
      AND zone.dnssec_key_signing_algorithm = 'rsasha1'
    RETURN
        zone.id AS zone_id,
        zone.name AS zone_name,
        project.id AS project_id,
        project.displayname AS project_name,
        zone.dns_name AS dns_name,
        zone.dnssec_key_signing_algorithm AS dnssec_key_signing_algorithm
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
      AND coalesce(zone.dnssec_state, 'off') = 'on'
      AND zone.dnssec_key_signing_algorithm = 'rsasha1'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
      AND coalesce(zone.dnssec_state, 'off') = 'on'
    RETURN COUNT(zone) AS count
    """,
    asset_id_field="zone_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_3_4_dnssec_no_rsasha1_ksk = Rule(
    id="cis_gcp_3_4_dnssec_no_rsasha1_ksk",
    name="CIS GCP 3.4: Cloud DNS DNSSEC Key-Signing Uses RSASHA1",
    description="Public Cloud DNS zones should not use RSASHA1 for the DNSSEC key-signing key.",
    output_model=DnssecWeakKskOutput,
    facts=(_gcp_dnssec_weak_ksk,),
    tags=("dns", "dnssec", "crypto", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="3.4",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 3.5: RSASHA1 should not be used for the DNSSEC zone-signing key
# Main node: GCPDNSZone
# =============================================================================
class DnssecWeakZskOutput(Finding):
    zone_id: str | None = None
    zone_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    dns_name: str | None = None
    dnssec_zone_signing_algorithm: str | None = None


_gcp_dnssec_weak_zsk = Fact(
    id="gcp_dnssec_weak_zsk",
    name="GCP public DNS zones using RSASHA1 for DNSSEC zone-signing",
    description="Detects public Cloud DNS zones whose DNSSEC zone-signing key uses RSASHA1.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
      AND coalesce(zone.dnssec_state, 'off') = 'on'
      AND zone.dnssec_zone_signing_algorithm = 'rsasha1'
    RETURN
        zone.id AS zone_id,
        zone.name AS zone_name,
        project.id AS project_id,
        project.displayname AS project_name,
        zone.dns_name AS dns_name,
        zone.dnssec_zone_signing_algorithm AS dnssec_zone_signing_algorithm
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
      AND coalesce(zone.dnssec_state, 'off') = 'on'
      AND zone.dnssec_zone_signing_algorithm = 'rsasha1'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (zone:GCPDNSZone)
    WHERE coalesce(zone.visibility, 'public') = 'public'
      AND coalesce(zone.dnssec_state, 'off') = 'on'
    RETURN COUNT(zone) AS count
    """,
    asset_id_field="zone_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_3_5_dnssec_no_rsasha1_zsk = Rule(
    id="cis_gcp_3_5_dnssec_no_rsasha1_zsk",
    name="CIS GCP 3.5: Cloud DNS DNSSEC Zone-Signing Uses RSASHA1",
    description="Public Cloud DNS zones should not use RSASHA1 for the DNSSEC zone-signing key.",
    output_model=DnssecWeakZskOutput,
    facts=(_gcp_dnssec_weak_zsk,),
    tags=("dns", "dnssec", "crypto", "stride:spoofing"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="3.5",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 3.8: VPC Flow Logs should be enabled for every subnet in a VPC network
# Main node: GCPSubnet
# =============================================================================
class SubnetFlowLogsDisabledOutput(Finding):
    subnet_id: str | None = None
    subnet_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    region: str | None = None
    purpose: str | None = None
    flow_logs_enabled: bool | None = None
    flow_logs_aggregation_interval: str | None = None
    flow_logs_sampling: float | None = None
    flow_logs_metadata: str | None = None


_gcp_subnet_flow_logs_disabled = Fact(
    id="gcp_subnet_flow_logs_disabled",
    name="GCP subnets without compliant VPC Flow Logs",
    description="Detects GCP subnets where VPC Flow Logs are disabled or not configured to CIS-recommended settings.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(subnet:GCPSubnet)
    WHERE coalesce(subnet.purpose, 'PRIVATE') = 'PRIVATE'
      AND (
        coalesce(subnet.flow_logs_enabled, false) = false
        OR subnet.flow_logs_aggregation_interval <> 'INTERVAL_5_SEC'
        OR coalesce(subnet.flow_logs_sampling, 0.0) <> 1.0
        OR subnet.flow_logs_metadata <> 'INCLUDE_ALL_METADATA'
        OR subnet.flow_logs_filter_expr IS NOT NULL
      )
    RETURN
        subnet.id AS subnet_id,
        subnet.name AS subnet_name,
        project.id AS project_id,
        project.displayname AS project_name,
        subnet.region AS region,
        subnet.purpose AS purpose,
        subnet.flow_logs_enabled AS flow_logs_enabled,
        subnet.flow_logs_aggregation_interval AS flow_logs_aggregation_interval,
        subnet.flow_logs_sampling AS flow_logs_sampling,
        subnet.flow_logs_metadata AS flow_logs_metadata
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(subnet:GCPSubnet)
    WHERE coalesce(subnet.purpose, 'PRIVATE') = 'PRIVATE'
      AND (
        coalesce(subnet.flow_logs_enabled, false) = false
        OR subnet.flow_logs_aggregation_interval <> 'INTERVAL_5_SEC'
        OR coalesce(subnet.flow_logs_sampling, 0.0) <> 1.0
        OR subnet.flow_logs_metadata <> 'INCLUDE_ALL_METADATA'
        OR subnet.flow_logs_filter_expr IS NOT NULL
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (subnet:GCPSubnet)
    WHERE coalesce(subnet.purpose, 'PRIVATE') = 'PRIVATE'
    RETURN COUNT(subnet) AS count
    """,
    asset_id_field="subnet_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_3_8_vpc_flow_logs = Rule(
    id="cis_gcp_3_8_vpc_flow_logs",
    name="CIS GCP 3.8: Subnets Without Compliant VPC Flow Logs",
    description="Private-purpose GCP subnets should enable VPC Flow Logs with CIS-recommended settings.",
    output_model=SubnetFlowLogsDisabledOutput,
    facts=(_gcp_subnet_flow_logs_disabled,),
    tags=("networking", "subnet", "flow-logs", "logging"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="3.8",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 6.6: Cloud SQL instances should not have public IPs
# Main node: GCPCloudSQLInstance
# =============================================================================
class CloudSqlPublicIpOutput(Finding):
    instance_id: str | None = None
    instance_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    ip_addresses: str | None = None


_gcp_cloudsql_public_ip = Fact(
    id="gcp_cloudsql_public_ip",
    name="GCP Cloud SQL instances with public IPs",
    description="Detects Cloud SQL instances whose ipAddresses include a PRIMARY public address.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
    WHERE instance.ip_addresses CONTAINS '"type": "PRIMARY"'
    RETURN
        instance.id AS instance_id,
        instance.name AS instance_name,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.ip_addresses AS ip_addresses
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
    WHERE instance.ip_addresses CONTAINS '"type": "PRIMARY"'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPCloudSQLInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_6_6_cloudsql_public_ip = Rule(
    id="cis_gcp_6_6_cloudsql_public_ip",
    name="CIS GCP 6.6: Cloud SQL Instances With Public IPs",
    description="Cloud SQL instances should use private IPs and avoid public PRIMARY addresses.",
    output_model=CloudSqlPublicIpOutput,
    facts=(_gcp_cloudsql_public_ip,),
    tags=("cloudsql", "database", "networking", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="6.6",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 6.7: Cloud SQL instances should have automated backups enabled
# Main node: GCPCloudSQLInstance
# =============================================================================
class CloudSqlBackupsDisabledOutput(Finding):
    instance_id: str | None = None
    instance_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    database_version: str | None = None


_gcp_cloudsql_backups_disabled = Fact(
    id="gcp_cloudsql_backups_disabled",
    name="GCP Cloud SQL instances without automated backups",
    description="Detects Cloud SQL instances where automated backups are not enabled.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
    WHERE coalesce(instance.backup_enabled, false) = false
    RETURN
        instance.id AS instance_id,
        instance.name AS instance_name,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.database_version AS database_version
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
    WHERE coalesce(instance.backup_enabled, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPCloudSQLInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_6_7_cloudsql_backups = Rule(
    id="cis_gcp_6_7_cloudsql_backups",
    name="CIS GCP 6.7: Cloud SQL Automated Backups Disabled",
    description="Cloud SQL instances should have automated backups enabled.",
    output_model=CloudSqlBackupsDisabledOutput,
    facts=(_gcp_cloudsql_backups_disabled,),
    tags=("cloudsql", "database", "backup", "resilience"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="6.7",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 7.1: BigQuery datasets are not anonymously or publicly accessible
# Main node: GCPBigQueryDataset
# =============================================================================
class BigQueryDatasetPublicAccessOutput(Finding):
    dataset_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    access_entries: str | None = None


_gcp_bigquery_dataset_public = Fact(
    id="gcp_bigquery_dataset_public",
    name="GCP BigQuery datasets with public access entries",
    description="Detects BigQuery datasets whose access entries reference allUsers or allAuthenticatedUsers.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(dataset:GCPBigQueryDataset)
    WHERE coalesce(dataset.access_entries, '') CONTAINS 'allUsers'
       OR coalesce(dataset.access_entries, '') CONTAINS 'allAuthenticatedUsers'
    RETURN
        dataset.id AS dataset_id,
        project.id AS project_id,
        project.displayname AS project_name,
        dataset.access_entries AS access_entries
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(dataset:GCPBigQueryDataset)
    WHERE coalesce(dataset.access_entries, '') CONTAINS 'allUsers'
       OR coalesce(dataset.access_entries, '') CONTAINS 'allAuthenticatedUsers'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (dataset:GCPBigQueryDataset)
    RETURN COUNT(dataset) AS count
    """,
    asset_id_field="dataset_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_7_1_bigquery_dataset_public = Rule(
    id="cis_gcp_7_1_bigquery_dataset_public",
    name="CIS GCP 7.1: BigQuery Datasets Publicly Accessible",
    description="BigQuery datasets should not grant access to allUsers or allAuthenticatedUsers.",
    output_model=BigQueryDatasetPublicAccessOutput,
    facts=(_gcp_bigquery_dataset_public,),
    tags=("bigquery", "data-warehouse", "iam", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="7.1",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 7.2: BigQuery tables are encrypted with CMEK
# Main node: GCPBigQueryTable
# =============================================================================
class BigQueryTableCmekMissingOutput(Finding):
    table_id: str | None = None
    dataset_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    kms_key_name: str | None = None


_gcp_bigquery_table_cmek_missing = Fact(
    id="gcp_bigquery_table_cmek_missing",
    name="GCP BigQuery tables without CMEK",
    description="Detects BigQuery tables whose encryptionConfiguration.kmsKeyName is not set.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(table:GCPBigQueryTable)
    WHERE table.kms_key_name IS NULL OR table.kms_key_name = ''
    RETURN
        table.id AS table_id,
        table.dataset_id AS dataset_id,
        project.id AS project_id,
        project.displayname AS project_name,
        table.kms_key_name AS kms_key_name
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(table:GCPBigQueryTable)
    WHERE table.kms_key_name IS NULL OR table.kms_key_name = ''
    RETURN *
    """,
    cypher_count_query="""
    MATCH (table:GCPBigQueryTable)
    RETURN COUNT(table) AS count
    """,
    asset_id_field="table_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_7_2_bigquery_table_cmek = Rule(
    id="cis_gcp_7_2_bigquery_table_cmek",
    name="CIS GCP 7.2: BigQuery Tables Without CMEK",
    description="BigQuery tables should use customer-managed encryption keys.",
    output_model=BigQueryTableCmekMissingOutput,
    facts=(_gcp_bigquery_table_cmek_missing,),
    tags=("bigquery", "encryption", "cmek", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="7.2",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 7.3: BigQuery datasets specify a default CMEK
# Main node: GCPBigQueryDataset
# =============================================================================
class BigQueryDatasetCmekMissingOutput(Finding):
    dataset_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    default_kms_key_name: str | None = None


_gcp_bigquery_dataset_cmek_missing = Fact(
    id="gcp_bigquery_dataset_cmek_missing",
    name="GCP BigQuery datasets without a default CMEK",
    description="Detects BigQuery datasets whose default encryption configuration does not define a CMEK.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(dataset:GCPBigQueryDataset)
    WHERE dataset.default_kms_key_name IS NULL OR dataset.default_kms_key_name = ''
    RETURN
        dataset.id AS dataset_id,
        project.id AS project_id,
        project.displayname AS project_name,
        dataset.default_kms_key_name AS default_kms_key_name
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(dataset:GCPBigQueryDataset)
    WHERE dataset.default_kms_key_name IS NULL OR dataset.default_kms_key_name = ''
    RETURN *
    """,
    cypher_count_query="""
    MATCH (dataset:GCPBigQueryDataset)
    RETURN COUNT(dataset) AS count
    """,
    asset_id_field="dataset_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_7_3_bigquery_dataset_cmek = Rule(
    id="cis_gcp_7_3_bigquery_dataset_cmek",
    name="CIS GCP 7.3: BigQuery Datasets Without Default CMEK",
    description="BigQuery datasets should define a default customer-managed encryption key.",
    output_model=BigQueryDatasetCmekMissingOutput,
    facts=(_gcp_bigquery_dataset_cmek_missing,),
    tags=("bigquery", "encryption", "cmek", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="7.3",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 6.4: Cloud SQL instances require all incoming connections to use SSL
# Main node: GCPCloudSQLInstance
# =============================================================================
class CloudSqlSslModeOutput(Finding):
    instance_id: str | None = None
    instance_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    ssl_mode: str | None = None


_gcp_cloudsql_ssl_not_enforced = Fact(
    id="gcp_cloudsql_ssl_not_enforced",
    name="GCP Cloud SQL instances not enforcing SSL-only connections",
    description=(
        "Detects Cloud SQL instances whose sslMode is not one of ENCRYPTED_ONLY or "
        "TRUSTED_CLIENT_CERTIFICATE_REQUIRED. Both modes restrict connections to "
        "SSL/TLS, with the latter additionally requiring valid client certificates."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
    WHERE NOT coalesce(instance.ssl_mode, '') IN ['ENCRYPTED_ONLY', 'TRUSTED_CLIENT_CERTIFICATE_REQUIRED']
    RETURN
        instance.id AS instance_id,
        instance.name AS instance_name,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.ssl_mode AS ssl_mode
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
    WHERE NOT coalesce(instance.ssl_mode, '') IN ['ENCRYPTED_ONLY', 'TRUSTED_CLIENT_CERTIFICATE_REQUIRED']
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPCloudSQLInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_6_4_cloudsql_ssl_required = Rule(
    id="cis_gcp_6_4_cloudsql_ssl_required",
    name="CIS GCP 6.4: Cloud SQL SSL Not Enforced",
    description="Cloud SQL instances should require all incoming connections to use SSL.",
    output_model=CloudSqlSslModeOutput,
    facts=(_gcp_cloudsql_ssl_not_enforced,),
    tags=("cloudsql", "database", "ssl", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="6.4",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 6.5: Cloud SQL instances do not implicitly whitelist all public IP addresses
# Main node: GCPCloudSQLInstance
# =============================================================================
class CloudSqlAuthorizedNetworksOutput(Finding):
    instance_id: str | None = None
    instance_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    authorized_networks: str | None = None


_gcp_cloudsql_authorized_networks_open = Fact(
    id="gcp_cloudsql_authorized_networks_open",
    name="GCP Cloud SQL instances authorizing 0.0.0.0/0",
    description="Detects Cloud SQL instances whose authorized networks include 0.0.0.0/0.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
    WHERE coalesce(instance.authorized_networks, '') CONTAINS '0.0.0.0/0'
    RETURN
        instance.id AS instance_id,
        instance.name AS instance_name,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.authorized_networks AS authorized_networks
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
    WHERE coalesce(instance.authorized_networks, '') CONTAINS '0.0.0.0/0'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPCloudSQLInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_6_5_cloudsql_authorized_networks = Rule(
    id="cis_gcp_6_5_cloudsql_authorized_networks",
    name="CIS GCP 6.5: Cloud SQL Authorized Networks Open to the Internet",
    description="Cloud SQL instances should not authorize 0.0.0.0/0 in authorized networks.",
    output_model=CloudSqlAuthorizedNetworksOutput,
    facts=(_gcp_cloudsql_authorized_networks_open,),
    tags=("cloudsql", "database", "networking", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="6.5",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


class CloudSqlDatabaseFlagOutput(Finding):
    instance_id: str | None = None
    instance_name: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    database_version: str | None = None
    database_flags: str | None = None


def _make_cloudsql_flag_fact(
    fact_id: str,
    name: str,
    description: str,
    db_version_filter: str,
    violation_predicate: str,
) -> Fact:
    return Fact(
        id=fact_id,
        name=name,
        description=description,
        cypher_query=f"""
        MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
        WHERE instance.database_version STARTS WITH '{db_version_filter}'
          AND ({violation_predicate})
        RETURN
            instance.id AS instance_id,
            instance.name AS instance_name,
            project.id AS project_id,
            project.displayname AS project_name,
            instance.database_version AS database_version,
            instance.database_flags AS database_flags
        """,
        cypher_visual_query=f"""
        MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPCloudSQLInstance)
        WHERE instance.database_version STARTS WITH '{db_version_filter}'
          AND ({violation_predicate})
        RETURN *
        """,
        cypher_count_query=f"""
        MATCH (instance:GCPCloudSQLInstance)
        WHERE instance.database_version STARTS WITH '{db_version_filter}'
        RETURN COUNT(instance) AS count
        """,
        asset_id_field="instance_id",
        module=Module.GCP,
        maturity=Maturity.STABLE,
    )


def _make_cloudsql_flag_rule(
    rule_id: str,
    name: str,
    description: str,
    requirement: str,
    fact: Fact,
) -> Rule:
    return Rule(
        id=rule_id,
        name=name,
        description=description,
        output_model=CloudSqlDatabaseFlagOutput,
        facts=(fact,),
        tags=("cloudsql", "database", "configuration"),
        version="1.0.0",
        references=CIS_REFERENCES,
        frameworks=(
            Framework(
                name="CIS GCP Foundations Benchmark",
                short_name="CIS",
                requirement=requirement,
                scope="gcp",
                revision="4.0",
            ),
        ),
    )


_gcp_cloudsql_mysql_skip_show_database = _make_cloudsql_flag_fact(
    "gcp_cloudsql_mysql_skip_show_database",
    "GCP Cloud SQL MySQL instances without skip_show_database=on",
    "Detects MySQL Cloud SQL instances where skip_show_database is not set to on.",
    "MYSQL",
    'coalesce(instance.database_flags, \'\') !~ \'.*\\"name\\": \\"skip_show_database\\", \\"value\\": \\"on\\".*\'',
)
cis_gcp_6_1_2_cloudsql_mysql_skip_show_database = _make_cloudsql_flag_rule(
    "cis_gcp_6_1_2_cloudsql_mysql_skip_show_database",
    "CIS GCP 6.1.2: Cloud SQL MySQL skip_show_database Not Set to On",
    "Cloud SQL MySQL instances should set skip_show_database to on.",
    "6.1.2",
    _gcp_cloudsql_mysql_skip_show_database,
)

_gcp_cloudsql_mysql_local_infile = _make_cloudsql_flag_fact(
    "gcp_cloudsql_mysql_local_infile",
    "GCP Cloud SQL MySQL instances without local_infile=off",
    "Detects MySQL Cloud SQL instances where local_infile is not set to off.",
    "MYSQL",
    'coalesce(instance.database_flags, \'\') !~ \'.*\\"name\\": \\"local_infile\\", \\"value\\": \\"off\\".*\'',
)
cis_gcp_6_1_3_cloudsql_mysql_local_infile = _make_cloudsql_flag_rule(
    "cis_gcp_6_1_3_cloudsql_mysql_local_infile",
    "CIS GCP 6.1.3: Cloud SQL MySQL local_infile Not Set to Off",
    "Cloud SQL MySQL instances should set local_infile to off.",
    "6.1.3",
    _gcp_cloudsql_mysql_local_infile,
)

_gcp_cloudsql_postgres_log_error_verbosity = _make_cloudsql_flag_fact(
    "gcp_cloudsql_postgres_log_error_verbosity",
    "GCP Cloud SQL PostgreSQL instances with log_error_verbosity weaker than DEFAULT",
    "Detects PostgreSQL Cloud SQL instances where log_error_verbosity is set to VERBOSE.",
    "POSTGRES",
    'coalesce(instance.database_flags, \'\') =~ \'.*\\"name\\": \\"log_error_verbosity\\", \\"value\\": \\"VERBOSE\\".*\'',
)
cis_gcp_6_2_1_cloudsql_postgres_log_error_verbosity = _make_cloudsql_flag_rule(
    "cis_gcp_6_2_1_cloudsql_postgres_log_error_verbosity",
    "CIS GCP 6.2.1: Cloud SQL PostgreSQL log_error_verbosity Too Permissive",
    "Cloud SQL PostgreSQL instances should set log_error_verbosity to DEFAULT or stricter.",
    "6.2.1",
    _gcp_cloudsql_postgres_log_error_verbosity,
)

_gcp_cloudsql_postgres_log_connections = _make_cloudsql_flag_fact(
    "gcp_cloudsql_postgres_log_connections",
    "GCP Cloud SQL PostgreSQL instances without log_connections=on",
    "Detects PostgreSQL Cloud SQL instances where log_connections is not set to on.",
    "POSTGRES",
    'coalesce(instance.database_flags, \'\') !~ \'.*\\"name\\": \\"log_connections\\", \\"value\\": \\"on\\".*\'',
)
cis_gcp_6_2_2_cloudsql_postgres_log_connections = _make_cloudsql_flag_rule(
    "cis_gcp_6_2_2_cloudsql_postgres_log_connections",
    "CIS GCP 6.2.2: Cloud SQL PostgreSQL log_connections Not Set to On",
    "Cloud SQL PostgreSQL instances should set log_connections to on.",
    "6.2.2",
    _gcp_cloudsql_postgres_log_connections,
)

_gcp_cloudsql_postgres_log_disconnections = _make_cloudsql_flag_fact(
    "gcp_cloudsql_postgres_log_disconnections",
    "GCP Cloud SQL PostgreSQL instances without log_disconnections=on",
    "Detects PostgreSQL Cloud SQL instances where log_disconnections is not set to on.",
    "POSTGRES",
    'coalesce(instance.database_flags, \'\') !~ \'.*\\"name\\": \\"log_disconnections\\", \\"value\\": \\"on\\".*\'',
)
cis_gcp_6_2_3_cloudsql_postgres_log_disconnections = _make_cloudsql_flag_rule(
    "cis_gcp_6_2_3_cloudsql_postgres_log_disconnections",
    "CIS GCP 6.2.3: Cloud SQL PostgreSQL log_disconnections Not Set to On",
    "Cloud SQL PostgreSQL instances should set log_disconnections to on.",
    "6.2.3",
    _gcp_cloudsql_postgres_log_disconnections,
)

_gcp_cloudsql_postgres_log_min_messages = _make_cloudsql_flag_fact(
    "gcp_cloudsql_postgres_log_min_messages",
    "GCP Cloud SQL PostgreSQL instances with log_min_messages below Warning",
    "Detects PostgreSQL Cloud SQL instances where log_min_messages is set below Warning.",
    "POSTGRES",
    'coalesce(instance.database_flags, \'\') =~ \'.*\\"name\\": \\"log_min_messages\\", \\"value\\": \\"(DEBUG5|DEBUG4|DEBUG3|DEBUG2|DEBUG1|INFO|NOTICE)\\".*\'',
)
cis_gcp_6_2_5_cloudsql_postgres_log_min_messages = _make_cloudsql_flag_rule(
    "cis_gcp_6_2_5_cloudsql_postgres_log_min_messages",
    "CIS GCP 6.2.5: Cloud SQL PostgreSQL log_min_messages Below Warning",
    "Cloud SQL PostgreSQL instances should set log_min_messages to Warning or stricter.",
    "6.2.5",
    _gcp_cloudsql_postgres_log_min_messages,
)

_gcp_cloudsql_postgres_log_min_error_statement = _make_cloudsql_flag_fact(
    "gcp_cloudsql_postgres_log_min_error_statement",
    "GCP Cloud SQL PostgreSQL instances with log_min_error_statement below Error",
    "Detects PostgreSQL Cloud SQL instances where log_min_error_statement is set below Error.",
    "POSTGRES",
    'coalesce(instance.database_flags, \'\') =~ \'.*\\"name\\": \\"log_min_error_statement\\", \\"value\\": \\"(DEBUG5|DEBUG4|DEBUG3|DEBUG2|DEBUG1|INFO|NOTICE|WARNING)\\".*\'',
)
cis_gcp_6_2_6_cloudsql_postgres_log_min_error_statement = _make_cloudsql_flag_rule(
    "cis_gcp_6_2_6_cloudsql_postgres_log_min_error_statement",
    "CIS GCP 6.2.6: Cloud SQL PostgreSQL log_min_error_statement Below Error",
    "Cloud SQL PostgreSQL instances should set log_min_error_statement to Error or stricter.",
    "6.2.6",
    _gcp_cloudsql_postgres_log_min_error_statement,
)

_gcp_cloudsql_postgres_log_min_duration_statement = _make_cloudsql_flag_fact(
    "gcp_cloudsql_postgres_log_min_duration_statement",
    "GCP Cloud SQL PostgreSQL instances without log_min_duration_statement=-1",
    "Detects PostgreSQL Cloud SQL instances where log_min_duration_statement is not set to -1.",
    "POSTGRES",
    'coalesce(instance.database_flags, \'\') =~ \'.*\\"name\\": \\"log_min_duration_statement\\", \\"value\\": \\"(?!-1)[^\\"]+\\".*\'',
)
cis_gcp_6_2_7_cloudsql_postgres_log_min_duration_statement = _make_cloudsql_flag_rule(
    "cis_gcp_6_2_7_cloudsql_postgres_log_min_duration_statement",
    "CIS GCP 6.2.7: Cloud SQL PostgreSQL log_min_duration_statement Not Disabled",
    "Cloud SQL PostgreSQL instances should set log_min_duration_statement to -1.",
    "6.2.7",
    _gcp_cloudsql_postgres_log_min_duration_statement,
)

_gcp_cloudsql_postgres_enable_pgaudit = _make_cloudsql_flag_fact(
    "gcp_cloudsql_postgres_enable_pgaudit",
    "GCP Cloud SQL PostgreSQL instances without cloudsql.enable_pgaudit=on",
    "Detects PostgreSQL Cloud SQL instances where cloudsql.enable_pgaudit is not set to on.",
    "POSTGRES",
    'coalesce(instance.database_flags, \'\') !~ \'.*\\"name\\": \\"cloudsql.enable_pgaudit\\", \\"value\\": \\"on\\".*\'',
)
cis_gcp_6_2_8_cloudsql_postgres_enable_pgaudit = _make_cloudsql_flag_rule(
    "cis_gcp_6_2_8_cloudsql_postgres_enable_pgaudit",
    "CIS GCP 6.2.8: Cloud SQL PostgreSQL cloudsql.enable_pgaudit Not Set to On",
    "Cloud SQL PostgreSQL instances should set cloudsql.enable_pgaudit to on.",
    "6.2.8",
    _gcp_cloudsql_postgres_enable_pgaudit,
)

_gcp_cloudsql_sqlserver_external_scripts = _make_cloudsql_flag_fact(
    "gcp_cloudsql_sqlserver_external_scripts",
    "GCP Cloud SQL SQL Server instances with external scripts enabled",
    "Detects SQL Server Cloud SQL instances where external scripts enabled is set to on.",
    "SQLSERVER",
    'coalesce(instance.database_flags, \'\') =~ \'.*\\"name\\": \\"external scripts enabled\\", \\"value\\": \\"on\\".*\'',
)
cis_gcp_6_3_1_cloudsql_sqlserver_external_scripts = _make_cloudsql_flag_rule(
    "cis_gcp_6_3_1_cloudsql_sqlserver_external_scripts",
    "CIS GCP 6.3.1: Cloud SQL SQL Server External Scripts Enabled",
    "Cloud SQL SQL Server instances should set external scripts enabled to off.",
    "6.3.1",
    _gcp_cloudsql_sqlserver_external_scripts,
)

_gcp_cloudsql_sqlserver_cross_db_ownership = _make_cloudsql_flag_fact(
    "gcp_cloudsql_sqlserver_cross_db_ownership",
    "GCP Cloud SQL SQL Server instances with cross db ownership chaining enabled",
    "Detects SQL Server Cloud SQL instances where cross db ownership chaining is set to on.",
    "SQLSERVER",
    'coalesce(instance.database_flags, \'\') =~ \'.*\\"name\\": \\"cross db ownership chaining\\", \\"value\\": \\"on\\".*\'',
)
cis_gcp_6_3_2_cloudsql_sqlserver_cross_db_ownership = _make_cloudsql_flag_rule(
    "cis_gcp_6_3_2_cloudsql_sqlserver_cross_db_ownership",
    "CIS GCP 6.3.2: Cloud SQL SQL Server Cross DB Ownership Chaining Enabled",
    "Cloud SQL SQL Server instances should not enable cross db ownership chaining.",
    "6.3.2",
    _gcp_cloudsql_sqlserver_cross_db_ownership,
)

_gcp_cloudsql_sqlserver_user_connections = _make_cloudsql_flag_fact(
    "gcp_cloudsql_sqlserver_user_connections",
    "GCP Cloud SQL SQL Server instances with limiting user connections",
    "Detects SQL Server Cloud SQL instances where user connections is set to a non-zero value.",
    "SQLSERVER",
    'coalesce(instance.database_flags, \'\') =~ \'.*\\"name\\": \\"user connections\\", \\"value\\": \\"(?!0)[^\\"]+\\".*\'',
)
cis_gcp_6_3_3_cloudsql_sqlserver_user_connections = _make_cloudsql_flag_rule(
    "cis_gcp_6_3_3_cloudsql_sqlserver_user_connections",
    "CIS GCP 6.3.3: Cloud SQL SQL Server User Connections Is Limiting",
    "Cloud SQL SQL Server instances should set user connections to a non-limiting value.",
    "6.3.3",
    _gcp_cloudsql_sqlserver_user_connections,
)

_gcp_cloudsql_sqlserver_user_options = _make_cloudsql_flag_fact(
    "gcp_cloudsql_sqlserver_user_options",
    "GCP Cloud SQL SQL Server instances with user options configured",
    "Detects SQL Server Cloud SQL instances where the user options flag is configured.",
    "SQLSERVER",
    "coalesce(instance.database_flags, '') CONTAINS '\"name\": \"user options\"'",
)
cis_gcp_6_3_4_cloudsql_sqlserver_user_options = _make_cloudsql_flag_rule(
    "cis_gcp_6_3_4_cloudsql_sqlserver_user_options",
    "CIS GCP 6.3.4: Cloud SQL SQL Server User Options Configured",
    "Cloud SQL SQL Server instances should not configure the user options flag.",
    "6.3.4",
    _gcp_cloudsql_sqlserver_user_options,
)

_gcp_cloudsql_sqlserver_remote_access = _make_cloudsql_flag_fact(
    "gcp_cloudsql_sqlserver_remote_access",
    "GCP Cloud SQL SQL Server instances without remote access=off",
    "Detects SQL Server Cloud SQL instances where remote access is not set to off.",
    "SQLSERVER",
    'coalesce(instance.database_flags, \'\') !~ \'.*\\"name\\": \\"remote access\\", \\"value\\": \\"off\\".*\'',
)
cis_gcp_6_3_5_cloudsql_sqlserver_remote_access = _make_cloudsql_flag_rule(
    "cis_gcp_6_3_5_cloudsql_sqlserver_remote_access",
    "CIS GCP 6.3.5: Cloud SQL SQL Server Remote Access Not Set to Off",
    "Cloud SQL SQL Server instances should set remote access to off.",
    "6.3.5",
    _gcp_cloudsql_sqlserver_remote_access,
)

_gcp_cloudsql_sqlserver_trace_3625 = _make_cloudsql_flag_fact(
    "gcp_cloudsql_sqlserver_trace_3625",
    "GCP Cloud SQL SQL Server instances without trace flag 3625=on",
    "Detects SQL Server Cloud SQL instances where trace flag 3625 is not set to on.",
    "SQLSERVER",
    'coalesce(instance.database_flags, \'\') !~ \'.*\\"name\\": \\"3625\\", \\"value\\": \\"on\\".*\'',
)
cis_gcp_6_3_6_cloudsql_sqlserver_trace_3625 = _make_cloudsql_flag_rule(
    "cis_gcp_6_3_6_cloudsql_sqlserver_trace_3625",
    "CIS GCP 6.3.6: Cloud SQL SQL Server Trace Flag 3625 Not Set to On",
    "Cloud SQL SQL Server instances should set trace flag 3625 to on.",
    "6.3.6",
    _gcp_cloudsql_sqlserver_trace_3625,
)

_gcp_cloudsql_sqlserver_contained_auth = _make_cloudsql_flag_fact(
    "gcp_cloudsql_sqlserver_contained_auth",
    "GCP Cloud SQL SQL Server instances with contained database authentication enabled",
    "Detects SQL Server Cloud SQL instances where contained database authentication is set to on.",
    "SQLSERVER",
    'coalesce(instance.database_flags, \'\') =~ \'.*\\"name\\": \\"contained database authentication\\", \\"value\\": \\"on\\".*\'',
)
cis_gcp_6_3_7_cloudsql_sqlserver_contained_auth = _make_cloudsql_flag_rule(
    "cis_gcp_6_3_7_cloudsql_sqlserver_contained_auth",
    "CIS GCP 6.3.7: Cloud SQL SQL Server Contained Database Authentication Enabled",
    "Cloud SQL SQL Server instances should set contained database authentication to off.",
    "6.3.7",
    _gcp_cloudsql_sqlserver_contained_auth,
)


# =============================================================================
# CIS GCP 5.2: Buckets should have uniform bucket-level access
# Main node: GCPBucket
# =============================================================================


# =============================================================================
# CIS GCP 5.2: Buckets should have uniform bucket-level access
# Main node: GCPBucket
# =============================================================================
class BucketUniformAccessOutput(Finding):
    """Output model for bucket uniform access check."""

    bucket_name: str | None = None
    bucket_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    bucket_location: str | None = None
    storage_class: str | None = None


_gcp_bucket_uniform_access_disabled = Fact(
    id="gcp_bucket_uniform_access_disabled",
    name="GCP buckets without uniform bucket-level access",
    description=(
        "Identifies buckets without uniform bucket-level access (bucket policy only) "
        "enabled. Uniform bucket-level access simplifies permission management by "
        "disabling object-level ACLs and using only IAM policies for access control."
    ),
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(bucket:GCPBucket)
    WHERE coalesce(bucket.iam_config_bucket_policy_only, false) = false
    RETURN
        bucket.id AS bucket_name,
        bucket.id AS bucket_id,
        project.id AS project_id,
        project.displayname AS project_name,
        bucket.location AS bucket_location,
        bucket.storage_class AS storage_class
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(bucket:GCPBucket)
    WHERE coalesce(bucket.iam_config_bucket_policy_only, false) = false
    RETURN *
    """,
    cypher_count_query="""
    MATCH (bucket:GCPBucket)
    RETURN COUNT(bucket) AS count
    """,
    asset_id_field="bucket_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_5_2_bucket_uniform_access = Rule(
    id="cis_gcp_5_2_bucket_uniform_access",
    name="CIS GCP 5.2: Bucket Uniform Access",
    description=(
        "Buckets should enable uniform bucket-level access (bucket policy only) to "
        "simplify permission management and use only IAM for access control."
    ),
    output_model=BucketUniformAccessOutput,
    facts=(_gcp_bucket_uniform_access_disabled,),
    tags=(
        "storage",
        "gcs",
        "stride:information_disclosure",
        "stride:elevation_of_privilege",
    ),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="5.2",
            scope="gcp",
            revision="4.0",
        ),
    ),
)

# =============================================================================
# TODO: CIS GCP 1.1: Corporate login credentials are used
# Missing datamodel or evidence: authoritative organization domain inventory and classification of IAM principals as corporate accounts versus external consumer identities
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.2: Multi-factor authentication is enabled for all non-service accounts
# Missing datamodel or evidence: MFA enrollment and enforcement state for human Google identities
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.3: Security key enforcement is enabled for all admin accounts
# Missing datamodel or evidence: security-key enforcement state for organization administrator identities
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.4: Only GCP-managed service account keys exist for each service account
# Missing datamodel or evidence: service account key inventory, key provenance, and key age
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.5: Service accounts have no admin privileges
# Missing datamodel or evidence: IAM bindings from service accounts to project, folder, and organization roles
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.6: IAM users are not assigned service account user or token creator roles at project level
# Missing datamodel or evidence: project-level IAM bindings that link human principals to role assignments
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.7: User-managed or external keys for service accounts are rotated every 90 days or fewer
# Missing datamodel or evidence: service account key inventory with validAfterTime or creation timestamps
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.8: Separation of duties is enforced for service-account-related roles
# Missing datamodel or evidence: project-level IAM bindings that let us correlate principals holding both admin and service-account-user style roles
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.9: Cloud KMS cryptokeys are not anonymously or publicly accessible
# Missing datamodel or evidence: IAM bindings on individual KMS cryptokeys
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.10: KMS encryption keys are rotated within 90 days
# Missing datamodel or evidence: next_rotation_time on GCPCryptoKey; current model only stores rotation_period
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.11: Separation of duties is enforced for KMS-related roles
# Missing datamodel or evidence: IAM bindings that correlate principals holding both Cloud KMS Admin and decrypt or encrypt roles
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.12: API keys only exist for active services
# Missing datamodel or evidence: API key inventory and key-to-service usage mappings
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.13: API keys are restricted to specified hosts and apps
# Missing datamodel or evidence: API key application restriction settings
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.14: API keys are restricted to only APIs the application needs access to
# Missing datamodel or evidence: API key API-target restriction settings
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.15: API keys are rotated every 90 days
# Missing datamodel or evidence: API key inventory with createTime or rotation timestamps
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.16: Essential Contacts is configured for organization
# Missing datamodel or evidence: Essential Contacts inventory and notification categories at organization scope
# =============================================================================

# =============================================================================
# TODO: CIS GCP 1.17: Secrets are not stored in Cloud Functions environment variables by using Secret Manager
# Missing datamodel or evidence: Cloud Function environment variables, Secret Manager API enablement, and secret reference usage
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.1: Cloud Audit Logging is configured properly
# Missing datamodel or evidence: auditConfigs and exemptedMembers from organization, folder, and project IAM policies
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.2: Sinks are configured for all log entries
# Missing datamodel or evidence: Logging sink inventory, inclusion filters, and sink destinations
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.3: Retention policies on storage buckets used for exporting logs are configured using Bucket Lock
# Missing datamodel or evidence: mapping from logging sinks to destination buckets plus bucket-lock retention state
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.4: Log metric filter and alerts exist for project ownership assignments or changes
# Missing datamodel or evidence: Logging metrics, Monitoring alert policies, and notification channel configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.5: Log metric filter and alerts exist for audit configuration changes
# Missing datamodel or evidence: Logging metrics, Monitoring alert policies, and notification channel configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.6: Log metric filter and alerts exist for custom role changes
# Missing datamodel or evidence: Logging metrics, Monitoring alert policies, and notification channel configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.7: Log metric filter and alerts exist for VPC network firewall rule changes
# Missing datamodel or evidence: Logging metrics, Monitoring alert policies, and notification channel configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.8: Log metric filter and alerts exist for VPC network route changes
# Missing datamodel or evidence: Logging metrics, Monitoring alert policies, and notification channel configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.9: Log metric filter and alerts exist for VPC network changes
# Missing datamodel or evidence: Logging metrics, Monitoring alert policies, and notification channel configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.10: Log metric filter and alerts exist for Cloud Storage IAM permission changes
# Missing datamodel or evidence: Logging metrics, Monitoring alert policies, and notification channel configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.11: Log metric filter and alerts exist for SQL instance configuration changes
# Missing datamodel or evidence: Logging metrics, Monitoring alert policies, and notification channel configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.12: Cloud DNS logging is enabled for all VPC networks
# Missing datamodel or evidence: Cloud DNS policy inventory, per-policy enableLogging state, and network-to-policy associations
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.13: Cloud Asset Inventory is enabled
# Missing datamodel or evidence: enabled-services inventory for cloudasset.googleapis.com per project
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.14: Access Transparency is enabled
# Missing datamodel or evidence: Access Transparency enrollment state at organization scope
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.15: Access Approval is enabled
# Missing datamodel or evidence: Access Approval enrollment state and notification recipients
# =============================================================================

# =============================================================================
# TODO: CIS GCP 2.16: Logging is enabled for HTTP(S) Load Balancer
# Missing datamodel or evidence: backend-service logging enablement and sampling rate
# =============================================================================

# =============================================================================
# TODO: CIS GCP 3.2: Legacy networks do not exist for older projects
# Missing datamodel or evidence: explicit network mode or legacy-network discriminator on GCPVpc
# =============================================================================

# =============================================================================
# TODO: CIS GCP 3.9: No HTTPS or SSL proxy load balancers permit SSL policies with weak cipher suites
# Missing datamodel or evidence: target proxy to SSL policy associations plus SSL policy min TLS version, profile, and enabled cipher features
# =============================================================================

# =============================================================================
# TODO: CIS GCP 3.10: Identity Aware Proxy restricts traffic to Google IP addresses
# Missing datamodel or evidence: IAP enablement state and app-specific firewall intent linking health-check and IAP CIDRs to protected workloads
# =============================================================================


# =============================================================================
# CIS GCP 4.1: Instances are not configured to use the default service account
# Main node: GCPInstance
# =============================================================================
class InstanceDefaultServiceAccountOutput(Finding):
    instance_name: str | None = None
    instance_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    service_account_email: str | None = None


_gcp_instance_default_service_account = Fact(
    id="gcp_instance_default_service_account",
    name="GCP compute instances using the default Compute Engine service account",
    description="Detects VM instances using the default Compute Engine service account, excluding GKE-managed nodes.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND instance.service_account_email ENDS WITH '-compute@developer.gserviceaccount.com'
    RETURN
        instance.instancename AS instance_name,
        instance.id AS instance_id,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.service_account_email AS service_account_email
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND instance.service_account_email ENDS WITH '-compute@developer.gserviceaccount.com'
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_1_default_service_account = Rule(
    id="cis_gcp_4_1_default_service_account",
    name="CIS GCP 4.1: Instances Using Default Service Account",
    description="VM instances should not use the default Compute Engine service account.",
    output_model=InstanceDefaultServiceAccountOutput,
    facts=(_gcp_instance_default_service_account,),
    tags=("compute", "iam", "service-accounts", "least-privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.1",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 4.2: Instances are not configured to use the default service account with full access to all Cloud APIs
# Main node: GCPInstance
# =============================================================================
class InstanceDefaultServiceAccountFullApiOutput(Finding):
    instance_name: str | None = None
    instance_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    service_account_email: str | None = None
    service_account_scopes: list[str] | None = None


_gcp_instance_default_service_account_full_api = Fact(
    id="gcp_instance_default_service_account_full_api",
    name="GCP compute instances using the default service account with full API scope",
    description="Detects VM instances using the default Compute Engine service account with the cloud-platform scope, excluding GKE-managed nodes.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND instance.service_account_email ENDS WITH '-compute@developer.gserviceaccount.com'
      AND any(scope IN coalesce(instance.service_account_scopes, []) WHERE scope CONTAINS 'cloud-platform')
    RETURN
        instance.instancename AS instance_name,
        instance.id AS instance_id,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.service_account_email AS service_account_email,
        instance.service_account_scopes AS service_account_scopes
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND instance.service_account_email ENDS WITH '-compute@developer.gserviceaccount.com'
      AND any(scope IN coalesce(instance.service_account_scopes, []) WHERE scope CONTAINS 'cloud-platform')
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_2_default_service_account_full_api = Rule(
    id="cis_gcp_4_2_default_service_account_full_api",
    name="CIS GCP 4.2: Default Service Account With Full Cloud API Scope",
    description="VM instances should not use the default Compute Engine service account with full access to all Cloud APIs.",
    output_model=InstanceDefaultServiceAccountFullApiOutput,
    facts=(_gcp_instance_default_service_account_full_api,),
    tags=("compute", "iam", "service-accounts", "least-privilege"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.2",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 4.3: Block project-wide SSH keys is enabled for VM instances
# Main node: GCPInstance
# =============================================================================
class InstanceProjectWideSshKeysOutput(Finding):
    instance_name: str | None = None
    instance_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    block_project_ssh_keys: str | None = None
    enable_oslogin_metadata: str | None = None
    compute_project_enable_oslogin: str | None = None


_gcp_instance_project_wide_ssh_keys = Fact(
    id="gcp_instance_project_wide_ssh_keys",
    name="GCP compute instances not blocking project-wide SSH keys",
    description="Detects VM instances that neither block project-wide SSH keys nor inherit an effective OS Login configuration.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND NOT (
        toLower(coalesce(instance.enable_oslogin_metadata, '')) = 'true'
        OR (
          instance.enable_oslogin_metadata IS NULL
          AND toLower(coalesce(project.compute_project_enable_oslogin, '')) = 'true'
        )
      )
      AND toLower(coalesce(instance.block_project_ssh_keys, 'false')) NOT IN ['true', '1']
    RETURN
        instance.instancename AS instance_name,
        instance.id AS instance_id,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.block_project_ssh_keys AS block_project_ssh_keys,
        instance.enable_oslogin_metadata AS enable_oslogin_metadata,
        project.compute_project_enable_oslogin AS compute_project_enable_oslogin
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND NOT (
        toLower(coalesce(instance.enable_oslogin_metadata, '')) = 'true'
        OR (
          instance.enable_oslogin_metadata IS NULL
          AND toLower(coalesce(project.compute_project_enable_oslogin, '')) = 'true'
        )
      )
      AND toLower(coalesce(instance.block_project_ssh_keys, 'false')) NOT IN ['true', '1']
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_3_block_project_wide_ssh_keys = Rule(
    id="cis_gcp_4_3_block_project_wide_ssh_keys",
    name="CIS GCP 4.3: Instances Not Blocking Project-Wide SSH Keys",
    description="Compute Engine instances should block project-wide SSH keys unless OS Login is effectively enabled.",
    output_model=InstanceProjectWideSshKeysOutput,
    facts=(_gcp_instance_project_wide_ssh_keys,),
    tags=("compute", "ssh", "oslogin", "remote-access"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.3",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 4.4: Oslogin is enabled for a project
# Main node: GCPProject
# =============================================================================
class ProjectOsloginDisabledOutput(Finding):
    project_id: str | None = None
    project_name: str | None = None
    compute_project_enable_oslogin: str | None = None
    overriding_instance_count: int | None = None


_gcp_project_oslogin_disabled = Fact(
    id="gcp_project_oslogin_disabled",
    name="GCP projects without effective OS Login enablement",
    description="Detects projects where OS Login is not enabled at project level or where non-GKE instances explicitly override it to false.",
    cypher_query="""
    MATCH (project:GCPProject)
    OPTIONAL MATCH (project)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND toLower(coalesce(instance.enable_oslogin_metadata, '')) IN ['false', '0']
    WITH project, count(instance) AS overriding_instance_count
    WHERE toLower(coalesce(project.compute_project_enable_oslogin, 'false')) <> 'true'
       OR overriding_instance_count > 0
    RETURN
        project.id AS project_id,
        project.displayname AS project_name,
        project.compute_project_enable_oslogin AS compute_project_enable_oslogin,
        overriding_instance_count
    """,
    cypher_visual_query="""
    MATCH (project:GCPProject)
    OPTIONAL MATCH p=(project)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND toLower(coalesce(instance.enable_oslogin_metadata, '')) IN ['false', '0']
    WITH project, collect(p) AS paths, count(instance) AS overriding_instance_count
    WHERE toLower(coalesce(project.compute_project_enable_oslogin, 'false')) <> 'true'
       OR overriding_instance_count > 0
    UNWIND paths AS p
    RETURN project, p
    """,
    cypher_count_query="""
    MATCH (project:GCPProject)
    RETURN COUNT(project) AS count
    """,
    asset_id_field="project_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_4_oslogin_enabled = Rule(
    id="cis_gcp_4_4_oslogin_enabled",
    name="CIS GCP 4.4: Projects Without Effective OS Login",
    description="Projects should enable OS Login and avoid instance-level overrides that disable it.",
    output_model=ProjectOsloginDisabledOutput,
    facts=(_gcp_project_oslogin_disabled,),
    tags=("compute", "ssh", "oslogin", "iam"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.4",
            scope="gcp",
            revision="4.0",
        ),
    ),
)

# =============================================================================
# TODO: CIS GCP 4.5: Enable connecting to serial ports is not enabled for VM instance
# Missing datamodel or evidence: project-level organization policy and inherited defaults; current rule detects explicit instance-level serial-port-enable only
# =============================================================================


# =============================================================================
# CIS GCP 4.6: IP forwarding is not enabled on instances
# Main node: GCPInstance
# =============================================================================
class InstanceIpForwardingOutput(Finding):
    instance_name: str | None = None
    instance_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None


_gcp_instance_ip_forwarding = Fact(
    id="gcp_instance_ip_forwarding",
    name="GCP compute instances with IP forwarding enabled",
    description="Detects VM instances with canIpForward enabled, excluding GKE-managed nodes.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND coalesce(instance.can_ip_forward, false) = true
    RETURN
        instance.instancename AS instance_name,
        instance.id AS instance_id,
        project.id AS project_id,
        project.displayname AS project_name
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND coalesce(instance.can_ip_forward, false) = true
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_6_ip_forwarding = Rule(
    id="cis_gcp_4_6_ip_forwarding",
    name="CIS GCP 4.6: Instances With IP Forwarding Enabled",
    description="Compute Engine instances should not enable IP forwarding.",
    output_model=InstanceIpForwardingOutput,
    facts=(_gcp_instance_ip_forwarding,),
    tags=("compute", "networking", "stride:information_disclosure"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.6",
            scope="gcp",
            revision="4.0",
        ),
    ),
)

# =============================================================================
# TODO: CIS GCP 4.7: VM disks for critical VMs are encrypted with customer-supplied encryption keys
# Missing datamodel or evidence: persistent disk inventory attached to instances with diskEncryptionKey or CSEK metadata and a way to identify critical VMs
# =============================================================================


# =============================================================================
# CIS GCP 4.8: Compute instances are launched with Shielded VM enabled
# Main node: GCPInstance
# =============================================================================
class InstanceShieldedVmDisabledOutput(Finding):
    instance_name: str | None = None
    instance_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    enable_vtpm: bool | None = None
    enable_integrity_monitoring: bool | None = None


_gcp_instance_shielded_vm_disabled = Fact(
    id="gcp_instance_shielded_vm_disabled",
    name="GCP compute instances without required Shielded VM settings",
    description="Detects VM instances where Shielded VM vTPM or Integrity Monitoring is not enabled.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND (
        coalesce(instance.enable_vtpm, false) = false
        OR coalesce(instance.enable_integrity_monitoring, false) = false
      )
    RETURN
        instance.instancename AS instance_name,
        instance.id AS instance_id,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.enable_vtpm AS enable_vtpm,
        instance.enable_integrity_monitoring AS enable_integrity_monitoring
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
      AND (
        coalesce(instance.enable_vtpm, false) = false
        OR coalesce(instance.enable_integrity_monitoring, false) = false
      )
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    WHERE instance.instancename IS NOT NULL
      AND NOT instance.instancename STARTS WITH 'gke-'
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_8_shielded_vm = Rule(
    id="cis_gcp_4_8_shielded_vm",
    name="CIS GCP 4.8: Instances Without Shielded VM Enabled",
    description="Compute Engine instances should enable Shielded VM vTPM and Integrity Monitoring.",
    output_model=InstanceShieldedVmDisabledOutput,
    facts=(_gcp_instance_shielded_vm_disabled,),
    tags=("compute", "shielded-vm", "integrity"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.8",
            scope="gcp",
            revision="4.0",
        ),
    ),
)


# =============================================================================
# CIS GCP 4.5: Enable connecting to serial ports is not enabled for VM instance
# Main node: GCPInstance
# =============================================================================
class InstanceSerialPortEnabledOutput(Finding):
    instance_name: str | None = None
    instance_id: str | None = None
    project_id: str | None = None
    project_name: str | None = None
    serial_port_enable: str | None = None


_gcp_instance_serial_port_enabled = Fact(
    id="gcp_instance_serial_port_enabled",
    name="GCP compute instances with serial port access enabled",
    description="Detects VM instances where serial-port-enable is explicitly enabled in instance metadata.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE toLower(coalesce(instance.serial_port_enable, '0')) IN ['1', 'true']
    RETURN
        instance.instancename AS instance_name,
        instance.id AS instance_id,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.serial_port_enable AS serial_port_enable
    """,
    cypher_visual_query="""
    MATCH p=(project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    WHERE toLower(coalesce(instance.serial_port_enable, '0')) IN ['1', 'true']
    RETURN *
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="instance_id",
    module=Module.GCP,
    maturity=Maturity.STABLE,
)

cis_gcp_4_5_serial_ports_disabled = Rule(
    id="cis_gcp_4_5_serial_ports_disabled",
    name="CIS GCP 4.5: Instances With Serial Port Access Enabled",
    description="Compute Engine instances should not enable serial port access.",
    output_model=InstanceSerialPortEnabledOutput,
    facts=(_gcp_instance_serial_port_enabled,),
    tags=("compute", "serial-port", "remote-access"),
    version="1.0.0",
    references=CIS_REFERENCES,
    frameworks=(
        Framework(
            name="CIS GCP Foundations Benchmark",
            short_name="CIS",
            requirement="4.5",
            scope="gcp",
            revision="4.0",
        ),
    ),
)

# =============================================================================
# TODO: CIS GCP 4.10: App Engine applications enforce HTTPS connections
# Missing datamodel or evidence: App Engine app.yaml or equivalent ingress redirection configuration
# =============================================================================

# =============================================================================
# TODO: CIS GCP 4.11: Compute instances have Confidential Computing enabled
# Missing datamodel or evidence: broader machine-family and CPU-platform eligibility matrix beyond the currently targeted N2D and C2D families
# =============================================================================

# =============================================================================
# TODO: CIS GCP 4.12: Latest operating system updates are installed on virtual machines in all projects
# Missing datamodel or evidence: OS Config API enablement, enable-osconfig metadata, OS inventory, patch compliance, and update-host reachability evidence
# =============================================================================

# =============================================================================
# TODO: CIS GCP 5.1: Cloud Storage bucket is not anonymously or publicly accessible
# Missing datamodel or evidence: bucket IAM bindings or effective public-access analysis for allUsers and allAuthenticatedUsers
# =============================================================================

# =============================================================================
# TODO: CIS GCP 6.1.1: MySQL instances do not allow anyone to connect with administrative privileges
# Missing datamodel or evidence: MySQL root-password state or no-password exposure signal
# =============================================================================

# =============================================================================
# TODO: CIS GCP 6.2.4: log_statement flag for Cloud SQL PostgreSQL is set appropriately
# Missing datamodel or evidence: parsed databaseFlags from Cloud SQL settings and an organization-defined approved value baseline
# =============================================================================

# =============================================================================
# TODO: CIS GCP 7.4: All data in BigQuery has been classified
# Missing datamodel or evidence: DLP data profile configuration, classification findings, or policy-tag coverage evidence
# =============================================================================

# =============================================================================
# TODO: CIS GCP 8.1: Dataproc clusters are encrypted using CMEK
# Missing datamodel or evidence: Dataproc cluster encryption configuration and associated KMS key reference
# =============================================================================
