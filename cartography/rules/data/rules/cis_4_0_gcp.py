"""
CIS GCP Foundations Benchmark v4.0.0

Each Rule maps to a single CIS control and uses Cartography's existing GCP data
model. Facts within a rule target the same security concept.
"""

from cartography.rules.spec.model import Fact
from cartography.rules.spec.model import Finding
from cartography.rules.spec.model import Maturity
from cartography.rules.spec.model import Module
from cartography.rules.spec.model import Rule
from cartography.rules.spec.model import RuleReference

CIS_REFERENCES = [
    RuleReference(
        text="CIS Google Cloud Platform Foundation Benchmark v4.0.0",
        url="https://www.cisecurity.org/benchmark/google_cloud_computing_platform",
    ),
]


class GCPCISFinding(Finding):
    control_id: str | None = None
    control_title: str | None = None
    profile: str | None = None
    severity: str | None = None
    resource_id: str | None = None
    resource_name: str | None = None
    resource_type: str | None = None
    project_id: str | None = None
    project_name: str | None = None


# =============================================================================
# CIS GCP 3.1: Default network should not exist
# =============================================================================
_cis_gcp_3_1_default_network = Fact(
    id="cis_gcp_3_1_default_network",
    name="CIS GCP 3.1: Default network exists in project",
    description="Detects GCP projects that still contain the default network.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)
    WHERE vpc.name = 'default'
    RETURN
        '3.1' AS control_id,
        'Ensure That the Default Network Does Not Exist in a Project' AS control_title,
        'Level 2' AS profile,
        'high' AS severity,
        project.id AS project_id,
        project.displayname AS project_name,
        vpc.id AS resource_id,
        vpc.name AS resource_name,
        'VPC Network' AS resource_type
    """,
    cypher_visual_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)
    WHERE vpc.name = 'default'
    RETURN project, vpc
    """,
    cypher_count_query="""
    MATCH (vpc:GCPVpc)
    RETURN COUNT(vpc) AS count
    """,
    asset_id_field="resource_id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gcp_3_1_default_network = Rule(
    id="cis_gcp_3_1_default_network",
    name="CIS GCP 3.1: Default network should be removed",
    description="Detects projects that still have the default network.",
    output_model=GCPCISFinding,
    facts=(_cis_gcp_3_1_default_network,),
    tags=("cis:3.1", "cis:gcp-4.0", "gcp", "compliance", "networking"),
    version="0.1.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS GCP 3.6: SSH should not be open to the internet
# =============================================================================
_cis_gcp_3_6_unrestricted_ssh = Fact(
    id="cis_gcp_3_6_unrestricted_ssh",
    name="CIS GCP 3.6: SSH open to the internet",
    description="Flags ingress firewall rules that allow SSH (port 22) from the internet (0.0.0.0/0 or ::/0).",
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
        '3.6' AS control_id,
        'Ensure That SSH Access Is Restricted From the Internet' AS control_title,
        'Level 2' AS profile,
        'high' AS severity,
        project.id AS project_id,
        project.displayname AS project_name,
        fw.id AS resource_id,
        fw.name AS resource_name,
        'Firewall Rule' AS resource_type,
        rule.ruleid AS firewall_rule_id,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        range.range AS source_range
    """,
    cypher_visual_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)-[:RESOURCE]->(fw:GCPFirewall {direction: 'INGRESS'})
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:IpRange)
    WHERE range.range IN ['0.0.0.0/0', '::/0']
      AND coalesce(fw.disabled, false) = false
      AND (
        (rule.protocol = 'tcp' AND rule.fromport <= 22 AND rule.toport >= 22)
        OR rule.protocol = 'all'
      )
    RETURN project, vpc, fw, rule, range
    """,
    cypher_count_query="""
    MATCH (fw:GCPFirewall)
    RETURN COUNT(fw) AS count
    """,
    asset_id_field="resource_id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gcp_3_6_unrestricted_ssh = Rule(
    id="cis_gcp_3_6_unrestricted_ssh",
    name="CIS GCP 3.6: SSH open to the internet",
    description="Ingress firewall rules should not allow SSH from the internet (0.0.0.0/0 or ::/0).",
    output_model=GCPCISFinding,
    facts=(_cis_gcp_3_6_unrestricted_ssh,),
    tags=("cis:3.6", "cis:gcp-4.0", "gcp", "compliance", "networking", "ssh"),
    version="0.1.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS GCP 3.7: RDP should not be open to the internet
# =============================================================================
_cis_gcp_3_7_unrestricted_rdp = Fact(
    id="cis_gcp_3_7_unrestricted_rdp",
    name="CIS GCP 3.7: RDP open to the internet",
    description="Flags ingress firewall rules that allow RDP (port 3389) from the internet (0.0.0.0/0 or ::/0).",
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
        '3.7' AS control_id,
        'Ensure That RDP Access Is Restricted From the Internet' AS control_title,
        'Level 2' AS profile,
        'high' AS severity,
        project.id AS project_id,
        project.displayname AS project_name,
        fw.id AS resource_id,
        fw.name AS resource_name,
        'Firewall Rule' AS resource_type,
        rule.ruleid AS firewall_rule_id,
        rule.fromport AS from_port,
        rule.toport AS to_port,
        range.range AS source_range
    """,
    cypher_visual_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(vpc:GCPVpc)-[:RESOURCE]->(fw:GCPFirewall {direction: 'INGRESS'})
    MATCH (fw)<-[:ALLOWED_BY]-(rule:GCPIpRule)<-[:MEMBER_OF_IP_RULE]-(range:IpRange)
    WHERE range.range IN ['0.0.0.0/0', '::/0']
      AND coalesce(fw.disabled, false) = false
      AND (
        (rule.protocol = 'tcp' AND rule.fromport <= 3389 AND rule.toport >= 3389)
        OR rule.protocol = 'all'
      )
    RETURN project, vpc, fw, rule, range
    """,
    cypher_count_query="""
    MATCH (fw:GCPFirewall)
    RETURN COUNT(fw) AS count
    """,
    asset_id_field="resource_id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gcp_3_7_unrestricted_rdp = Rule(
    id="cis_gcp_3_7_unrestricted_rdp",
    name="CIS GCP 3.7: RDP open to the internet",
    description="Ingress firewall rules should not allow RDP from the internet (0.0.0.0/0 or ::/0).",
    output_model=GCPCISFinding,
    facts=(_cis_gcp_3_7_unrestricted_rdp,),
    tags=("cis:3.7", "cis:gcp-4.0", "gcp", "compliance", "networking", "rdp"),
    version="0.1.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS GCP 4.9: Compute instances should not have public IPs
# =============================================================================
_cis_gcp_4_9_public_ip = Fact(
    id="cis_gcp_4_9_public_ip",
    name="CIS GCP 4.9: Compute instances have public IPs",
    description="Detects VM instances with public NAT IPs attached to their network interfaces.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(access:GCPNicAccessConfig)
    WHERE access.public_ip IS NOT NULL
    RETURN
        '4.9' AS control_id,
        'Ensure That Compute Instances Do Not Have Public IP Addresses' AS control_title,
        'Level 2' AS profile,
        'high' AS severity,
        project.id AS project_id,
        project.displayname AS project_name,
        instance.id AS resource_id,
        instance.instancename AS resource_name,
        'Compute Instance' AS resource_type,
        access.public_ip AS external_ip,
        access.network_tier AS network_tier
    """,
    cypher_visual_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(instance:GCPInstance)
    MATCH (instance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)-[:RESOURCE]->(access:GCPNicAccessConfig)
    WHERE access.public_ip IS NOT NULL
    RETURN project, instance, nic, access
    """,
    cypher_count_query="""
    MATCH (instance:GCPInstance)
    RETURN COUNT(instance) AS count
    """,
    asset_id_field="resource_id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gcp_4_9_public_ip = Rule(
    id="cis_gcp_4_9_public_ip",
    name="CIS GCP 4.9: Compute instances should not have public IPs",
    description="VM instances should not have external IPs attached to NICs.",
    output_model=GCPCISFinding,
    facts=(_cis_gcp_4_9_public_ip,),
    tags=("cis:4.9", "cis:gcp-4.0", "gcp", "compliance", "compute"),
    version="0.1.0",
    references=CIS_REFERENCES,
)


# =============================================================================
# CIS GCP 5.2: Buckets should have uniform bucket-level access
# =============================================================================
_cis_gcp_5_2_bucket_uniform_access = Fact(
    id="cis_gcp_5_2_bucket_uniform_access",
    name="CIS GCP 5.2: Bucket without uniform bucket-level access",
    description="Identifies buckets without uniform bucket-level access (bucket policy only) enabled.",
    cypher_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(bucket:GCPBucket)
    WHERE coalesce(bucket.iam_config_bucket_policy_only, false) = false
    RETURN
        '5.2' AS control_id,
        'Ensure That Cloud Storage Buckets Have Uniform Bucket-Level Access Enabled' AS control_title,
        'Level 2' AS profile,
        'high' AS severity,
        project.id AS project_id,
        project.displayname AS project_name,
        bucket.id AS resource_id,
        bucket.id AS resource_name,
        'GCS Bucket' AS resource_type,
        bucket.location AS bucket_location,
        bucket.storage_class AS storage_class
    """,
    cypher_visual_query="""
    MATCH (project:GCPProject)-[:RESOURCE]->(bucket:GCPBucket)
    WHERE coalesce(bucket.iam_config_bucket_policy_only, false) = false
    RETURN project, bucket
    """,
    cypher_count_query="""
    MATCH (bucket:GCPBucket)
    RETURN COUNT(bucket) AS count
    """,
    asset_id_field="resource_id",
    module=Module.GCP,
    maturity=Maturity.EXPERIMENTAL,
)

cis_gcp_5_2_bucket_uniform_access = Rule(
    id="cis_gcp_5_2_bucket_uniform_access",
    name="CIS GCP 5.2: Buckets should enforce uniform bucket-level access",
    description="Buckets should enable uniform bucket-level access (bucket policy only).",
    output_model=GCPCISFinding,
    facts=(_cis_gcp_5_2_bucket_uniform_access,),
    tags=("cis:5.2", "cis:gcp-4.0", "gcp", "compliance", "storage"),
    version="0.1.0",
    references=CIS_REFERENCES,
)
