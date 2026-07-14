from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import Case
from cartography.graph.analysis import RawCypher
from cartography.graph.analysis import ScopeById
from cartography.graph.analysis import SetProperties
from cartography.graph.analysis import SetProperty

GCP_COMPUTE_INSTANCE_VPC_ANALYSIS = AnalysisJob(
    name="GCP Instance to VPC derived relationship analysis",
    short_name="gcp_compute_instance_vpc_analysis",
    cleanup_iterationsize=100,
    statements=(
        AnalysisStatement(
            match="MATCH (i:GCPInstance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)-[:PART_OF_SUBNET]->(sn:GCPSubnet)<-[:HAS]-(vpc:GCPVpc)",
            effects=(
                AddRelationship(
                    "i",
                    "MEMBER_OF_GCP_VPC",
                    "vpc",
                    rel_alias="m",
                    source_label="GCPInstance",
                    target_label="GCPVpc",
                ),
            ),
        ),
    ),
)
GCP_GKE_ASSET_EXPOSURE = AnalysisJob(
    name="GCP GKE internet exposure",
    short_name="gcp_gke_asset_exposure",
    statements=(
        AnalysisStatement(
            match="MATCH (cluster:GKECluster) WHERE cluster.private_nodes = false OR cluster.private_endpoint_enabled = false OR cluster.master_authorized_networks = false",
            effects=(
                SetProperty("cluster", "exposed_internet", True, label="GKECluster"),
            ),
        ),
    ),
)
GCP_GKE_BASIC_AUTH = AnalysisJob(
    name="GCP GKE basic authentication exposure",
    short_name="gcp_gke_basic_auth",
    statements=(
        AnalysisStatement(
            match="MATCH (cluster:GKECluster) WHERE (cluster.masterauth_username IS NOT NULL AND NOT cluster.masterauth_username = '') AND (cluster.masterauth_password IS NOT NULL AND NOT cluster.masterauth_password = '')",
            effects=(SetProperty("cluster", "basic_auth", True, label="GKECluster"),),
        ),
    ),
)
GCP_BUCKET_PUBLIC_PROJECTION = AnalysisJob(
    name="Ontology - GCP bucket public projection",
    short_name="gcp_bucket_public_projection",
    statements=(
        AnalysisStatement(
            match="MATCH (b:GCPBucket)",
            effects=(
                SetProperty(
                    "b",
                    "_ont_public",
                    Case(
                        when=(
                            (
                                "COALESCE(b.iam_config_public_access_prevention, '') = 'enforced'",
                                False,
                            ),
                        ),
                        else_=RawCypher(
                            "COALESCE(b.acl_public, false) OR EXISTS { MATCH (b)<-[:APPLIES_TO]-(binding:GCPPolicyBinding) WHERE binding.is_public = true AND COALESCE(binding.has_condition, false) = false }"
                        ),
                    ),
                    label="GCPBucket",
                ),
            ),
        ),
    ),
)
GCP_COMPUTE_FORWARDING_RULE_EXPOSURE = AnalysisJob(
    name="GCP ForwardingRule internet exposure",
    short_name="gcp_compute_forwarding_rule_exposure",
    scope=ScopeById("GCPProject", "PROJECT_ID", scope_on="fr"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (fr:GCPForwardingRule) WHERE fr.load_balancing_scheme = 'EXTERNAL' OR fr.load_balancing_scheme = 'EXTERNAL_MANAGED'",
            effects=(
                SetProperties(
                    "fr",
                    {"exposed_internet": True, "exposed_internet_type": "direct"},
                    label="GCPForwardingRule",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (fr:GCPForwardingRule) WHERE fr.exposed_internet IS NULL",
            effects=(
                SetProperty("fr", "exposed_internet", False, label="GCPForwardingRule"),
            ),
        ),
    ),
)
GCP_COMPUTE_FIREWALL_INGRESS = AnalysisJob(
    name="GCP firewall ingress to instance analysis",
    short_name="gcp_compute_firewall_ingress",
    scope=ScopeById("GCPProject", "PROJECT_ID", scope_on="vpc"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (vpc:GCPVpc)<-[mem:MEMBER_OF_GCP_VPC]-(inst:GCPInstance)-[t:TAGGED]->(tag:GCPNetworkTag)-[tt:TARGET_TAG]-(fw:GCPFirewall{direction: 'INGRESS'})<-[res:RESOURCE]-(vpc)",
            effects=(
                AddRelationship(
                    "fw",
                    "FIREWALL_INGRESS",
                    "inst",
                    rel_alias="a",
                    source_label="GCPFirewall",
                    target_label="GCPInstance",
                    scoped_to="target",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (fw:GCPFirewall{direction: 'INGRESS', has_target_service_accounts: False}) WHERE NOT (fw)-[:TARGET_TAG]->(:GCPNetworkTag) MATCH (vpc:GCPVpc)-[res:RESOURCE]->(fw) MATCH (inst:GCPInstance)-[mem:MEMBER_OF_GCP_VPC]->(vpc)",
            effects=(
                AddRelationship(
                    "fw",
                    "FIREWALL_INGRESS",
                    "inst",
                    rel_alias="a",
                    source_label="GCPFirewall",
                    target_label="GCPInstance",
                    scoped_to="target",
                ),
            ),
        ),
    ),
)
GCP_COMPUTE_INSTANCE_EXPOSURE = AnalysisJob(
    name="GCP Instance internet exposure",
    short_name="gcp_compute_instance_exposure",
    scope=ScopeById(
        "GCPProject",
        "PROJECT_ID",
        scope_on=("bs", "n", "n", "n", "i"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (bs:GCPBackendService)-[:ROUTES_TO]->(ig:GCPInstanceGroup)-[:HAS_MEMBER]->(i:GCPInstance) WHERE bs.load_balancing_scheme = 'EXTERNAL' OR bs.load_balancing_scheme = 'EXTERNAL_MANAGED'",
            effects=(
                SetProperties(
                    "i",
                    {"exposed_internet": True, "exposed_internet_type": "gcp_lb"},
                    label="GCPInstance",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (n:GCPInstance)<-[:FIREWALL_INGRESS]-(firewall_a:GCPFirewall)<-[:ALLOWED_BY]-(allow_rule:GCPIpRule{protocol:'tcp'})<-[:MEMBER_OF_IP_RULE]-(:GCPIpRange{id:\"0.0.0.0/0\"}) MATCH (n)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(ac:GCPNicAccessConfig) WHERE ac.public_ip IS NOT NULL OPTIONAL MATCH (n)<-[:FIREWALL_INGRESS]-(firewall_b:GCPFirewall)<-[:DENIED_BY]-(deny_rule:GCPIpRule{protocol:'tcp'}) WITH n, firewall_a, allow_rule, deny_rule, firewall_b WHERE deny_rule IS NULL OR firewall_b.priority > firewall_a.priority OR NOT allow_rule.fromport IN RANGE(deny_rule.fromport, deny_rule.toport) OR NOT allow_rule.toport IN RANGE(deny_rule.fromport, deny_rule.toport)",
            effects=(
                SetProperties(
                    "n",
                    {"exposed_internet": True, "exposed_internet_type": "direct"},
                    label="GCPInstance",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (n:GCPInstance)<-[:FIREWALL_INGRESS]-(firewall_a:GCPFirewall)<-[:ALLOWED_BY]-(allow_rule:GCPIpRule{protocol:'udp'})<-[:MEMBER_OF_IP_RULE]-(:GCPIpRange{id:\"0.0.0.0/0\"}) MATCH (n)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(ac:GCPNicAccessConfig) WHERE ac.public_ip IS NOT NULL OPTIONAL MATCH (n)<-[:FIREWALL_INGRESS]-(firewall_b:GCPFirewall)<-[:DENIED_BY]-(deny_rule:GCPIpRule{protocol:'udp'}) WITH n, firewall_a, allow_rule, deny_rule, firewall_b WHERE deny_rule IS NULL OR firewall_b.priority > firewall_a.priority OR NOT allow_rule.fromport IN RANGE(deny_rule.fromport, deny_rule.toport) OR NOT allow_rule.toport IN RANGE(deny_rule.fromport, deny_rule.toport)",
            effects=(
                SetProperties(
                    "n",
                    {"exposed_internet": True, "exposed_internet_type": "direct"},
                    label="GCPInstance",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (n:GCPInstance)<-[:FIREWALL_INGRESS]-(firewall_a:GCPFirewall)<-[:ALLOWED_BY]-(allow_rule:GCPIpRule{protocol:'all'})<-[:MEMBER_OF_IP_RULE]-(:GCPIpRange{id:\"0.0.0.0/0\"}) MATCH (n)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(ac:GCPNicAccessConfig) WHERE ac.public_ip IS NOT NULL AND allow_rule.fromport IS NOT NULL AND allow_rule.toport IS NOT NULL OPTIONAL MATCH (n)<-[:FIREWALL_INGRESS]-(firewall_b:GCPFirewall)<-[:DENIED_BY]-(deny_rule:GCPIpRule{protocol:'all'}) WITH n, firewall_a, allow_rule, deny_rule, firewall_b WHERE deny_rule IS NULL OR firewall_b.priority > firewall_a.priority OR NOT allow_rule.fromport IN RANGE(deny_rule.fromport, deny_rule.toport) OR NOT allow_rule.toport IN RANGE(deny_rule.fromport, deny_rule.toport)",
            effects=(
                SetProperties(
                    "n",
                    {"exposed_internet": True, "exposed_internet_type": "direct"},
                    label="GCPInstance",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (i:GCPInstance) WHERE i.exposed_internet IS NULL",
            effects=(SetProperty("i", "exposed_internet", False, label="GCPInstance"),),
        ),
    ),
)
GCP_COMPUTE_CLOUDRUN_EXPOSURE = AnalysisJob(
    name="GCP CloudRunService internet exposure",
    short_name="gcp_compute_cloudrun_exposure",
    scope=ScopeById("GCPProject", "PROJECT_ID", scope_on="svc"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (svc:GCPCloudRunService) WHERE svc.ingress = 'INGRESS_TRAFFIC_ALL'",
            effects=(
                SetProperties(
                    "svc",
                    {"exposed_internet": True, "exposed_internet_type": "direct"},
                    label="GCPCloudRunService",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (svc:GCPCloudRunService) WHERE svc.exposed_internet IS NULL AND svc.ingress IN ['INGRESS_TRAFFIC_INTERNAL_ONLY', 'INGRESS_TRAFFIC_NONE']",
            effects=(
                SetProperty(
                    "svc", "exposed_internet", False, label="GCPCloudRunService"
                ),
            ),
        ),
    ),
)
GCP_COMPUTE_EXPOSURE_JOBS = (
    GCP_COMPUTE_FORWARDING_RULE_EXPOSURE,
    GCP_COMPUTE_FIREWALL_INGRESS,
    GCP_COMPUTE_INSTANCE_EXPOSURE,
    GCP_COMPUTE_CLOUDRUN_EXPOSURE,
)
GCP_LB_EXPOSURE = AnalysisJob(
    name="GCP BackendService to Instance EXPOSE relationship (scoped per project)",
    short_name="gcp_lb_exposure",
    scope=ScopeById("GCPProject", "PROJECT_ID", scope_on="bs"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (bs:GCPBackendService)-[:ROUTES_TO]->(ig:GCPInstanceGroup)-[:HAS_MEMBER]->(i:GCPInstance) WHERE bs.load_balancing_scheme = 'EXTERNAL' OR bs.load_balancing_scheme = 'EXTERNAL_MANAGED'",
            effects=(
                AddRelationship(
                    "bs",
                    "EXPOSE",
                    "i",
                    properties={"exposure_type": "gcp_lb"},
                    source_label="GCPBackendService",
                    target_label="GCPInstance",
                ),
            ),
        ),
    ),
)
