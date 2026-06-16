from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipEffect

GCP_SCOPE = AnalysisScope("GCPProject", "PROJECT_ID")

GCP_COMPUTE_INSTANCE_VPC_ANALYSIS = AnalysisJob(
    name="GCP Instance to VPC derived relationship analysis",
    short_name="gcp_compute_instance_vpc_analysis",
    effect=RelationshipEffect("GCPInstance", "MEMBER_OF_GCP_VPC", "GCPVpc"),
    cleanup_iterationsize=100,
    statements=(
        AnalysisStatement(
            "MATCH (i:GCPInstance)-[:NETWORK_INTERFACE]->(nic:GCPNetworkInterface)-[:PART_OF_SUBNET]->(sn:GCPSubnet)<-[:HAS]-(vpc:GCPVpc) "
            "MERGE (i)-[m:MEMBER_OF_GCP_VPC]->(vpc) ON CREATE SET m.firstseen = timestamp() SET m.lastupdated = $UPDATE_TAG",
        ),
    ),
)

GCP_GKE_ASSET_EXPOSURE = AnalysisJob(
    name="GCP GKE internet exposure",
    short_name="gcp_gke_asset_exposure",
    effect=PropertyEffect("GKECluster", ("exposed_internet",)),
    statements=(
        AnalysisStatement(
            "MATCH (cluster:GKECluster) WHERE cluster.private_nodes = false OR cluster.private_endpoint_enabled = false OR cluster.master_authorized_networks = false SET cluster.exposed_internet = true",
        ),
    ),
)

GCP_GKE_BASIC_AUTH = AnalysisJob(
    name="GCP GKE basic authentication exposure",
    short_name="gcp_gke_basic_auth",
    effect=PropertyEffect("GKECluster", ("basic_auth",)),
    statements=(
        AnalysisStatement(
            "MATCH (cluster:GKECluster) WHERE (cluster.masterauth_username IS NOT NULL AND NOT cluster.masterauth_username = '') AND (cluster.masterauth_password IS NOT NULL AND NOT cluster.masterauth_password = '') SET cluster.basic_auth = true",
        ),
    ),
)

GCP_BUCKET_PUBLIC_PROJECTION = AnalysisJob(
    name="Ontology - GCP bucket public projection",
    short_name="gcp_bucket_public_projection",
    effect=PropertyEffect("GCPBucket", ("_ont_public",)),
    statements=(
        AnalysisStatement(
            "MATCH (b:GCPBucket) SET b._ont_public = CASE WHEN COALESCE(b.iam_config_public_access_prevention, '') = 'enforced' THEN false ELSE COALESCE(b.acl_public, false) OR EXISTS { MATCH (b)<-[:APPLIES_TO]-(binding:GCPPolicyBinding) WHERE binding.is_public = true AND COALESCE(binding.has_condition, false) = false } END",
        ),
    ),
)

GCP_COMPUTE_FORWARDING_RULE_EXPOSURE = AnalysisJob(
    name="GCP ForwardingRule internet exposure",
    short_name="gcp_compute_forwarding_rule_exposure",
    scope=GCP_SCOPE,
    effect=PropertyEffect(
        "GCPForwardingRule",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(fr:GCPForwardingRule) WHERE fr.load_balancing_scheme = 'EXTERNAL' OR fr.load_balancing_scheme = 'EXTERNAL_MANAGED' SET fr.exposed_internet = true, fr.exposed_internet_type = 'direct'",
        ),
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(fr:GCPForwardingRule) WHERE fr.exposed_internet IS NULL SET fr.exposed_internet = false",
        ),
    ),
)

GCP_COMPUTE_FIREWALL_INGRESS = AnalysisJob(
    name="GCP firewall ingress to instance analysis",
    short_name="gcp_compute_firewall_ingress",
    scope=GCP_SCOPE,
    effect=RelationshipEffect(
        "GCPFirewall",
        "FIREWALL_INGRESS",
        "GCPInstance",
        scoped_to="target",
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(vpc:GCPVpc)<-[mem:MEMBER_OF_GCP_VPC]-(inst:GCPInstance)-[t:TAGGED]->(tag:GCPNetworkTag)-[tt:TARGET_TAG]-(fw:GCPFirewall{direction: 'INGRESS'})<-[res:RESOURCE]-(vpc) "
            "MERGE (fw)-[a:FIREWALL_INGRESS]->(inst) ON CREATE SET a.firstseen = timestamp() SET a.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (fw:GCPFirewall{direction: 'INGRESS', has_target_service_accounts: False}) WHERE NOT (fw)-[:TARGET_TAG]->(:GCPNetworkTag) "
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(vpc:GCPVpc)-[res:RESOURCE]->(fw) MATCH (inst:GCPInstance)-[mem:MEMBER_OF_GCP_VPC]->(vpc) "
            "MERGE (fw)-[a:FIREWALL_INGRESS]->(inst) ON CREATE SET a.firstseen = timestamp() SET a.lastupdated = $UPDATE_TAG",
        ),
    ),
)

GCP_COMPUTE_INSTANCE_EXPOSURE = AnalysisJob(
    name="GCP Instance internet exposure",
    short_name="gcp_compute_instance_exposure",
    scope=GCP_SCOPE,
    effect=PropertyEffect("GCPInstance", ("exposed_internet", "exposed_internet_type")),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(bs:GCPBackendService)-[:ROUTES_TO]->(ig:GCPInstanceGroup)-[:HAS_MEMBER]->(i:GCPInstance) WHERE bs.load_balancing_scheme = 'EXTERNAL' OR bs.load_balancing_scheme = 'EXTERNAL_MANAGED' SET i.exposed_internet = true, i.exposed_internet_type = 'gcp_lb'",
        ),
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(n:GCPInstance)<-[:FIREWALL_INGRESS]-(firewall_a:GCPFirewall)<-[:ALLOWED_BY]-(allow_rule:GCPIpRule{protocol:'tcp'})<-[:MEMBER_OF_IP_RULE]-(:GCPIpRange{id:\"0.0.0.0/0\"}) MATCH (n)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(ac:GCPNicAccessConfig) WHERE ac.public_ip IS NOT NULL OPTIONAL MATCH (n)<-[:FIREWALL_INGRESS]-(firewall_b:GCPFirewall)<-[:DENIED_BY]-(deny_rule:GCPIpRule{protocol:'tcp'}) WITH n, firewall_a, allow_rule, deny_rule, firewall_b WHERE deny_rule IS NULL OR firewall_b.priority > firewall_a.priority OR NOT allow_rule.fromport IN RANGE(deny_rule.fromport, deny_rule.toport) OR NOT allow_rule.toport IN RANGE(deny_rule.fromport, deny_rule.toport) SET n.exposed_internet = true, n.exposed_internet_type = 'direct'",
        ),
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(n:GCPInstance)<-[:FIREWALL_INGRESS]-(firewall_a:GCPFirewall)<-[:ALLOWED_BY]-(allow_rule:GCPIpRule{protocol:'udp'})<-[:MEMBER_OF_IP_RULE]-(:GCPIpRange{id:\"0.0.0.0/0\"}) MATCH (n)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(ac:GCPNicAccessConfig) WHERE ac.public_ip IS NOT NULL OPTIONAL MATCH (n)<-[:FIREWALL_INGRESS]-(firewall_b:GCPFirewall)<-[:DENIED_BY]-(deny_rule:GCPIpRule{protocol:'udp'}) WITH n, firewall_a, allow_rule, deny_rule, firewall_b WHERE deny_rule IS NULL OR firewall_b.priority > firewall_a.priority OR NOT allow_rule.fromport IN RANGE(deny_rule.fromport, deny_rule.toport) OR NOT allow_rule.toport IN RANGE(deny_rule.fromport, deny_rule.toport) SET n.exposed_internet = true, n.exposed_internet_type = 'direct'",
        ),
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(n:GCPInstance)<-[:FIREWALL_INGRESS]-(firewall_a:GCPFirewall)<-[:ALLOWED_BY]-(allow_rule:GCPIpRule{protocol:'all'})<-[:MEMBER_OF_IP_RULE]-(:GCPIpRange{id:\"0.0.0.0/0\"}) MATCH (n)-[:NETWORK_INTERFACE]->(:GCPNetworkInterface)-[:RESOURCE]->(ac:GCPNicAccessConfig) WHERE ac.public_ip IS NOT NULL AND allow_rule.fromport IS NOT NULL AND allow_rule.toport IS NOT NULL OPTIONAL MATCH (n)<-[:FIREWALL_INGRESS]-(firewall_b:GCPFirewall)<-[:DENIED_BY]-(deny_rule:GCPIpRule{protocol:'all'}) WITH n, firewall_a, allow_rule, deny_rule, firewall_b WHERE deny_rule IS NULL OR firewall_b.priority > firewall_a.priority OR NOT allow_rule.fromport IN RANGE(deny_rule.fromport, deny_rule.toport) OR NOT allow_rule.toport IN RANGE(deny_rule.fromport, deny_rule.toport) SET n.exposed_internet = true, n.exposed_internet_type = 'direct'",
        ),
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(i:GCPInstance) WHERE i.exposed_internet IS NULL SET i.exposed_internet = false",
        ),
    ),
)

GCP_COMPUTE_CLOUDRUN_EXPOSURE = AnalysisJob(
    name="GCP CloudRunService internet exposure",
    short_name="gcp_compute_cloudrun_exposure",
    scope=GCP_SCOPE,
    effect=PropertyEffect(
        "GCPCloudRunService",
        ("exposed_internet", "exposed_internet_type"),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(svc:GCPCloudRunService) WHERE svc.ingress = 'INGRESS_TRAFFIC_ALL' SET svc.exposed_internet = true, svc.exposed_internet_type = 'direct'",
        ),
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(svc:GCPCloudRunService) WHERE svc.exposed_internet IS NULL AND svc.ingress IN ['INGRESS_TRAFFIC_INTERNAL_ONLY', 'INGRESS_TRAFFIC_NONE'] SET svc.exposed_internet = false",
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
    scope=GCP_SCOPE,
    effect=RelationshipEffect(
        "GCPBackendService",
        "EXPOSE",
        "GCPInstance",
        properties=("exposure_type",),
    ),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (p:GCPProject{id: $PROJECT_ID})-[:RESOURCE]->(bs:GCPBackendService)-[:ROUTES_TO]->(ig:GCPInstanceGroup)-[:HAS_MEMBER]->(i:GCPInstance) WHERE bs.load_balancing_scheme = 'EXTERNAL' OR bs.load_balancing_scheme = 'EXTERNAL_MANAGED' MERGE (bs)-[r:EXPOSE]->(i) SET r.lastupdated = $UPDATE_TAG, r.exposure_type = 'gcp_lb'",
        ),
    ),
)
