from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipEffect
from cartography.graph.analysis import RelationshipPropertyEffect

AWS_USER_PROJECTION = AnalysisJob(
    name="Ontology - AWS user projection",
    short_name="ontology_aws_user_projection",
    effect=PropertyEffect("AWSUser", ("_ont_has_mfa", "_ont_active")),
    statements=(
        AnalysisStatement(
            "MATCH (u:AWSUser) "
            "SET u._ont_has_mfa = EXISTS((u)-[:MFA_DEVICE]->(:AWSMfaDevice))",
        ),
        AnalysisStatement(
            "MATCH (u:AWSUser) "
            "SET u._ont_active = CASE WHEN (u.passwordlastused_dt IS NOT NULL) OR EXISTS((u)-[:AWS_ACCESS_KEY]->(:AccountAccessKey {status: 'Active'})) THEN true ELSE NULL END",
        ),
    ),
)

DEVICE_OWNS_LINKING = AnalysisJob(
    name="Ontology - Devices OWNS relationship linking",
    short_name="ontology_devices_linking",
    effect=RelationshipEffect("User", "OWNS", "Device"),
    statements=(
        AnalysisStatement(
            "MATCH (host:CrowdstrikeHost)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE host.email IS NOT NULL AND trim(host.email) <> '' AND obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG "
            "WITH d, toLower(trim(host.email)) AS host_email "
            "MATCH (u:User) WHERE u.email IS NOT NULL AND trim(u.email) <> '' AND toLower(trim(u.email)) = host_email "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:DuoUser)-[:HAS_DUO_PHONE]-(:DuoPhone)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:DuoUser)-[:HAS_DUO_ENDPOINT]-(:DuoEndpoint)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:SnipeitUser)-[:HAS_CHECKED_OUT]-(:SnipeitAsset)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:TailscaleUser)-[:OWNS]-(:TailscaleDevice)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:GoogleWorkspaceUser)-[:OWNS]-(:GoogleWorkspaceDevice)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (j)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE (j:JamfComputer OR j:JamfMobileDevice) AND j.email IS NOT NULL AND trim(j.email) <> '' AND obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG "
            "WITH d, toLower(trim(j.email)) AS jamf_email "
            "MATCH (u:User) WHERE u.email IS NOT NULL AND trim(u.email) <> '' AND toLower(trim(u.email)) = jamf_email "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:EntraUser)-[:ENROLLED_TO]->(device:IntuneManagedDevice)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG AND device.lastupdated = $UPDATE_TAG "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:JumpCloudUser)-[:OWNS]->(:JumpCloudSystem)<-[obs:OBSERVED_AS]-(d:Device) "
            "WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG "
            "MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

DNS_RECORD_TO_KUBERNETES_INGRESS = AnalysisJob(
    name="Ontology - DNSRecord to KubernetesIngress linking",
    short_name="ontology_dnsrecords_kubernetes_ingress",
    effect=RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "KubernetesIngress"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (dns:DNSRecord) WHERE dns.lastupdated = $UPDATE_TAG AND dns._ont_name IS NOT NULL "
            "WITH dns MATCH (ing:KubernetesIngress) WHERE dns._ont_name IN ing.host_names "
            "MERGE (dns)-[r:DNS_POINTS_TO]->(ing) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

DNS_RECORD_TARGETS = (
    ("AWSLoadBalancerV2", "dnsname"),
    ("AWSLoadBalancer", "dnsname"),
    ("CloudFrontDistribution", "domain_name"),
    ("EC2Instance", "publicdnsname"),
    ("GCPInstance", "hostname"),
    ("AzureAppService", "default_host_name"),
    ("AzureFunctionApp", "default_host_name"),
)

DNS_RECORD_LINKING_JOBS = (DNS_RECORD_TO_KUBERNETES_INGRESS,) + tuple(
    AnalysisJob(
        name=f"Ontology - DNSRecord to {target_label} linking",
        short_name=f"ontology_dnsrecords_{target_label.lower()}",
        effect=RelationshipEffect("DNSRecord", "DNS_POINTS_TO", target_label),
        cleanup_iterationsize=1000,
        statements=(
            AnalysisStatement(
                f"MATCH (dns:DNSRecord) WHERE dns.lastupdated = $UPDATE_TAG AND dns._ont_value IS NOT NULL "
                f"WITH dns MATCH (target:{target_label}) "
                f"WHERE toLower(toString(dns._ont_value)) = toLower(target.{target_property}) "
                f"MERGE (dns)-[r:DNS_POINTS_TO]->(target) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            ),
            AnalysisStatement(
                f"MATCH (dns:GCPRecordSet) WHERE dns.lastupdated = $UPDATE_TAG AND dns.data IS NOT NULL "
                f"UNWIND dns.data AS val WITH dns, val MATCH (target:{target_label}) "
                f"WHERE toLower(val) = toLower(target.{target_property}) "
                f"MERGE (dns)-[r:DNS_POINTS_TO]->(target) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            ),
        ),
    )
    for target_label, target_property in DNS_RECORD_TARGETS
)

LOADBALANCER_EXPOSE_CONTAINER = AnalysisJob(
    name="Ontology - LoadBalancer to Container linking",
    short_name="ontology_loadbalancers_linking",
    effect=RelationshipEffect("LoadBalancer", "EXPOSE", "Container"),
    statements=(
        AnalysisStatement(
            "MATCH (lb:LoadBalancer {lastupdated: $UPDATE_TAG})-[:EXPOSE]->(ip:EC2PrivateIp)<-[:PRIVATE_IP_ADDRESS]-(ni:NetworkInterface)<-[:NETWORK_INTERFACE]-(task:ECSTask)-[:HAS_CONTAINER]->(c:Container) "
            "MERGE (lb)-[r:EXPOSE]->(c) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

PACKAGE_DEPLOYED_IMAGE_JOBS = (
    AnalysisJob(
        name="Ontology - Trivy Package DEPLOYED Image linking",
        short_name="ontology_packages_trivy_deployed",
        effect=RelationshipEffect("Package", "DEPLOYED", "Image"),
        statements=(
            AnalysisStatement(
                "MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)-[:DEPLOYED]->(img:Image) "
                "MERGE (p)-[r:DEPLOYED]->(img) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            ),
        ),
    ),
    AnalysisJob(
        name="Ontology - Syft Package DEPLOYED Image linking",
        short_name="ontology_packages_syft_deployed",
        effect=RelationshipEffect("Package", "DEPLOYED", "Image"),
        statements=(
            AnalysisStatement(
                "MATCH (p:Package)-[:DETECTED_AS]->(sp:SyftPackage)-[:DEPLOYED]->(img:Image) "
                "MERGE (p)-[r:DEPLOYED]->(img) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            ),
        ),
    ),
)

PACKAGE_AFFECTS_LINKING = AnalysisJob(
    name="Ontology - TrivyImageFinding AFFECTS Package linking",
    short_name="ontology_packages_affects",
    effect=RelationshipEffect("TrivyImageFinding", "AFFECTS", "Package"),
    statements=(
        AnalysisStatement(
            "MATCH (f:TrivyImageFinding)-[:AFFECTS]->(tp:TrivyPackage)<-[:DETECTED_AS]-(p:Package) "
            "MERGE (f)-[r:AFFECTS]->(p) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

PACKAGE_SHOULD_UPDATE_TO_LINKING = AnalysisJob(
    name="Ontology - Package SHOULD_UPDATE_TO TrivyFix linking",
    short_name="ontology_packages_should_update_to",
    effect=RelationshipEffect("Package", "SHOULD_UPDATE_TO", "TrivyFix"),
    statements=(
        AnalysisStatement(
            "MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)-[:SHOULD_UPDATE_TO]->(fix:TrivyFix) "
            "MERGE (p)-[r:SHOULD_UPDATE_TO]->(fix) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

PACKAGE_DEPENDS_ON_LINKING = AnalysisJob(
    name="Ontology - Package DEPENDS_ON Package linking",
    short_name="ontology_packages_depends_on",
    effect=RelationshipEffect("Package", "DEPENDS_ON", "Package"),
    statements=(
        AnalysisStatement(
            "MATCH (p1:Package)-[:DETECTED_AS]->(sp1:SyftPackage)-[:DEPENDS_ON]->(sp2:SyftPackage)<-[:DETECTED_AS]-(p2:Package) "
            "MERGE (p1)-[r:DEPENDS_ON]->(p2) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

PACKAGE_LINKING_JOBS = (
    *PACKAGE_DEPLOYED_IMAGE_JOBS,
    PACKAGE_AFFECTS_LINKING,
    PACKAGE_SHOULD_UPDATE_TO_LINKING,
    PACKAGE_DEPENDS_ON_LINKING,
)

PUBLIC_IP_POINTS_TO_DEVICE = AnalysisJob(
    name="Ontology - PublicIP POINTS_TO Device linking",
    short_name="ontology_publicips_linking",
    effect=RelationshipEffect("PublicIP", "POINTS_TO", "Device"),
    statements=(
        AnalysisStatement(
            "MATCH (p:PublicIP), (host:CrowdstrikeHost)<-[:OBSERVED_AS]-(d:Device) "
            "WHERE p.lastupdated = $UPDATE_TAG AND host.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG AND host.external_ip = p.ip_address "
            "MERGE (p)-[r:POINTS_TO]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

USER_HAS_AWS_SSO_ACCOUNT = AnalysisJob(
    name="Ontology - AWSSSOUser HAS_ACCOUNT User linking",
    short_name="ontology_users_aws_sso",
    effect=RelationshipEffect("User", "HAS_ACCOUNT", "AWSSSOUser"),
    statements=(
        AnalysisStatement(
            "MATCH (sso:AWSSSOUser) MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount {id: sso.external_id}) "
            "MERGE (u)-[r:HAS_ACCOUNT]->(sso) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

USER_HAS_GITHUB_ACCOUNT = AnalysisJob(
    name="Ontology - GitHubUser HAS_ACCOUNT User linking",
    short_name="ontology_users_github",
    effect=RelationshipEffect("User", "HAS_ACCOUNT", "GitHubUser"),
    statements=(
        AnalysisStatement(
            "MATCH (u:User) WHERE u.email is not NULL MATCH (g:GitHubUser) WHERE u.email in g.organization_verified_domain_emails "
            "MERGE (u)-[r:HAS_ACCOUNT]->(g) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

USER_OWNS_API_KEY = AnalysisJob(
    name="Ontology - User OWNS APIKey linking",
    short_name="ontology_users_api_key",
    effect=RelationshipEffect("User", "OWNS", "APIKey"),
    statements=(
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount)<-[:OWNED_BY]-(k:APIKey) "
            "MERGE (u)-[r:OWNS]->(k) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

USER_AUTHORIZED_THIRD_PARTY_APP = AnalysisJob(
    name="Ontology - User AUTHORIZED ThirdPartyApp linking",
    short_name="ontology_users_third_party_app",
    effect=RelationshipEffect(
        "User",
        "AUTHORIZED",
        "ThirdPartyApp",
        properties=("scopes",),
    ),
    statements=(
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount)-[authr:AUTHORIZED|APPLICATION]->(a:ThirdPartyApp) "
            "MERGE (u)-[r:AUTHORIZED]->(a) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG, r.scopes = coalesce(authr.scopes, [])",
        ),
        AnalysisStatement(
            "MATCH (u:User)-[:HAS_ACCOUNT]->(:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(:OktaGroup)-[:APPLICATION]->(a:ThirdPartyApp) "
            "MERGE (u)-[r:AUTHORIZED]->(a) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG, r.scopes = []",
        ),
    ),
)

USER_LINKING_JOBS = (
    USER_HAS_AWS_SSO_ACCOUNT,
    USER_HAS_GITHUB_ACCOUNT,
    USER_OWNS_API_KEY,
    USER_AUTHORIZED_THIRD_PARTY_APP,
)

CONTAINER_RESOLVED_IMAGE = AnalysisJob(
    name="Container RESOLVED_IMAGE analysis",
    short_name="resolved_image_analysis_container",
    effect=RelationshipEffect("Container", "RESOLVED_IMAGE", "Image"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (c:Container)-[:HAS_IMAGE]->(i:Image) WHERE NOT i:ImageManifestList "
            "MERGE (c)-[r:RESOLVED_IMAGE]->(i) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (c:Container)-[:HAS_IMAGE]->(:ImageManifestList)-[:CONTAINS_IMAGE]->(i:Image) "
            "WHERE c.architecture_normalized IS NOT NULL AND i._ont_architecture = c.architecture_normalized "
            "WITH c, collect(DISTINCT i) AS candidates WHERE size(candidates) = 1 "
            "WITH c, candidates[0] AS img "
            "MERGE (c)-[r:RESOLVED_IMAGE]->(img) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

FUNCTION_RESOLVED_IMAGE = AnalysisJob(
    name="Function RESOLVED_IMAGE analysis",
    short_name="resolved_image_analysis_function",
    effect=RelationshipEffect("Function", "RESOLVED_IMAGE", "Image"),
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            "MATCH (f:Function)-[:HAS_IMAGE]->(i:Image) WHERE NOT i:ImageManifestList "
            "MERGE (f)-[r:RESOLVED_IMAGE]->(i) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
        AnalysisStatement(
            "MATCH (f:Function)-[:HAS_IMAGE]->(:ImageManifestList)-[:CONTAINS_IMAGE]->(i:Image) "
            "WHERE f.architecture_normalized IS NOT NULL AND i._ont_architecture = f.architecture_normalized "
            "WITH f, collect(DISTINCT i) AS candidates WHERE size(candidates) = 1 "
            "WITH f, candidates[0] AS img "
            "MERGE (f)-[r:RESOLVED_IMAGE]->(img) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
        ),
    ),
)

RESOLVED_IMAGE_JOBS = (
    CONTAINER_RESOLVED_IMAGE,
    FUNCTION_RESOLVED_IMAGE,
)

SUPPLY_CHAIN_SOURCE_FILE = AnalysisJob(
    name="Enrich PACKAGED_FROM with source_file from Image provenance",
    short_name="supply_chain_source_file",
    effect=RelationshipPropertyEffect(
        "Image",
        "PACKAGED_FROM",
        ("dockerfile_path",),
    ),
    statements=(
        AnalysisStatement(
            "MATCH (i:Image)-[r:PACKAGED_FROM]->() "
            "WHERE r.dockerfile_path IS NULL AND i.source_file IS NOT NULL "
            "SET r.dockerfile_path = i.source_file",
        ),
    ),
)
