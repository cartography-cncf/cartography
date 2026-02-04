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
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:IpRange)
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
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:IpRange)
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
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:IpRange)
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
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:IpRange)
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
