from cartography.graph.analysis import AddRelationship
from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import RawCypher
from cartography.graph.analysis import SetProperty

AWS_USER_PROJECTION = AnalysisJob(
    name="Ontology - AWS user projection",
    short_name="ontology_aws_user_projection",
    statements=(
        AnalysisStatement(
            match="MATCH (u:AWSUser)",
            effects=(
                SetProperty(
                    "u",
                    "_ont_has_mfa",
                    RawCypher("EXISTS((u)-[:MFA_DEVICE]->(:AWSMfaDevice))"),
                    label="AWSUser",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:AWSUser)",
            effects=(
                SetProperty(
                    "u",
                    "_ont_active",
                    RawCypher(
                        "CASE WHEN (u.passwordlastused_dt IS NOT NULL) OR EXISTS((u)-[:AWS_ACCESS_KEY]->(:AccountAccessKey {status: 'Active'})) THEN true ELSE NULL END"
                    ),
                    label="AWSUser",
                ),
            ),
        ),
    ),
)
DEVICE_OWNS_LINKING = AnalysisJob(
    name="Ontology - Devices OWNS relationship linking",
    short_name="ontology_devices_linking",
    statements=(
        AnalysisStatement(
            match="MATCH (host:CrowdstrikeHost)<-[obs:OBSERVED_AS]-(d:Device) WHERE host.email IS NOT NULL AND trim(host.email) <> '' AND obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG WITH d, toLower(trim(host.email)) AS host_email MATCH (u:User) WHERE u.email IS NOT NULL AND trim(u.email) <> '' AND toLower(trim(u.email)) = host_email",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:DuoUser)-[:HAS_DUO_PHONE]-(:DuoPhone)<-[obs:OBSERVED_AS]-(d:Device) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:DuoUser)-[:HAS_DUO_ENDPOINT]-(:DuoEndpoint)<-[obs:OBSERVED_AS]-(d:Device) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:SnipeitUser)-[:HAS_CHECKED_OUT]-(:SnipeitAsset)<-[obs:OBSERVED_AS]-(d:Device) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:TailscaleUser)-[:OWNS]-(:TailscaleDevice)<-[obs:OBSERVED_AS]-(d:Device) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:GoogleWorkspaceUser)-[:OWNS]-(:GoogleWorkspaceDevice)<-[obs:OBSERVED_AS]-(d:Device) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (j)<-[obs:OBSERVED_AS]-(d:Device) WHERE (j:JamfComputer OR j:JamfMobileDevice) AND j.email IS NOT NULL AND trim(j.email) <> '' AND obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG WITH d, toLower(trim(j.email)) AS jamf_email MATCH (u:User) WHERE u.email IS NOT NULL AND trim(u.email) <> '' AND toLower(trim(u.email)) = jamf_email",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:EntraUser)-[:ENROLLED_TO]->(device:IntuneManagedDevice)<-[obs:OBSERVED_AS]-(d:Device) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG AND device.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:JumpCloudUser)-[:OWNS]->(:JumpCloudSystem)<-[obs:OBSERVED_AS]-(d:Device) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "u", "OWNS", "d", source_label="User", target_label="Device"
                ),
            ),
        ),
    ),
)
DEVICE_AFFECTS_S1_FINDING = AnalysisJob(
    name="Ontology - S1AppFinding AFFECTS Device linking",
    short_name="ontology_devices_s1_app_finding_affects",
    statements=(
        AnalysisStatement(
            match="MATCH (d:Device)-[obs:OBSERVED_AS]->(:S1Agent)<-[:AFFECTS]-(f:S1AppFinding) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "f",
                    "AFFECTS",
                    "d",
                    source_label="S1AppFinding",
                    target_label="Device",
                ),
            ),
        ),
    ),
)
DEVICE_AFFECTS_CROWDSTRIKE_FINDING = AnalysisJob(
    name="Ontology - CrowdstrikeFinding AFFECTS Device linking",
    short_name="ontology_devices_crowdstrike_finding_affects",
    statements=(
        AnalysisStatement(
            match="MATCH (d:Device)-[obs:OBSERVED_AS]->(:CrowdstrikeHost)-[:HAS_VULNERABILITY]->(:SpotlightVulnerability)-[:HAS_CVE]->(f:CrowdstrikeFinding) WHERE obs.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG",
            effects=(
                AddRelationship(
                    "f",
                    "AFFECTS",
                    "d",
                    source_label="CrowdstrikeFinding",
                    target_label="Device",
                ),
            ),
        ),
    ),
)
DEVICE_LINKING_JOBS = (
    DEVICE_OWNS_LINKING,
    DEVICE_AFFECTS_S1_FINDING,
    DEVICE_AFFECTS_CROWDSTRIKE_FINDING,
)
DNS_RECORD_GCP_RECORD_SET_ONT_VALUE_CLEANUP = AnalysisJob(
    name="Ontology - GCPRecordSet stale _ont_value cleanup",
    short_name="ontology_dnsrecords_gcp_record_set_ont_value_cleanup",
    statements=(
        AnalysisStatement(
            query="MATCH (n:GCPRecordSet) WHERE n._ont_value IS NOT NULL REMOVE n._ont_value",
        ),
    ),
)
DNS_RECORD_TO_KUBERNETES_INGRESS = AnalysisJob(
    name="Ontology - DNSRecord to KubernetesIngress linking",
    short_name="ontology_dnsrecords_kubernetes_ingress",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (dns:DNSRecord) WHERE dns._ont_name IS NOT NULL WITH dns MATCH (ing:KubernetesIngress) WHERE dns._ont_name IN ing.host_names",
            effects=(
                AddRelationship(
                    "dns",
                    "DNS_POINTS_TO",
                    "ing",
                    source_label="DNSRecord",
                    target_label="KubernetesIngress",
                ),
            ),
        ),
    ),
)
DNS_RECORD_TARGETS = (
    (
        "AWSLoadBalancerV2",
        "dnsname",
        "AND NOT dns:AWSDNSRecord AND NOT dns:GCPRecordSet",
        "NOT source:AWSDNSRecord",
    ),
    (
        "AWSLoadBalancer",
        "dnsname",
        "AND NOT dns:AWSDNSRecord AND NOT dns:GCPRecordSet",
        "NOT source:AWSDNSRecord",
    ),
    ("CloudFrontDistribution", "domain_name", "AND NOT dns:GCPRecordSet", ""),
    (
        "EC2Instance",
        "publicdnsname",
        "AND NOT dns:AWSDNSRecord AND NOT dns:GCPRecordSet",
        "NOT source:AWSDNSRecord",
    ),
    ("GCPInstance", "hostname", "AND NOT dns:GCPRecordSet", ""),
    ("AzureAppService", "default_host_name", "AND NOT dns:GCPRecordSet", ""),
    ("AzureFunctionApp", "default_host_name", "AND NOT dns:GCPRecordSet", ""),
)
DNS_RECORD_LINKING_JOBS = (
    DNS_RECORD_GCP_RECORD_SET_ONT_VALUE_CLEANUP,
    DNS_RECORD_TO_KUBERNETES_INGRESS,
) + tuple(
    (
        AnalysisJob(
            name=f"Ontology - DNSRecord to {target_label} linking",
            short_name=f"ontology_dnsrecords_{target_label.lower()}",
            cleanup_iterationsize=1000,
            statements=(
                AnalysisStatement(
                    match=f"MATCH (dns:DNSRecord) WHERE dns._ont_value IS NOT NULL {match_filter} WITH dns MATCH (target:{target_label}) WHERE toLower(toString(dns._ont_value)) = toLower(target.{target_property})",
                    effects=(
                        AddRelationship(
                            "dns",
                            "DNS_POINTS_TO",
                            "target",
                            source_label="DNSRecord",
                            target_label=target_label,
                            cleanup_where=cleanup_where,
                        ),
                    ),
                ),
                AnalysisStatement(
                    match=f"MATCH (dns:GCPRecordSet) WHERE dns.data IS NOT NULL UNWIND dns.data AS val WITH dns, val MATCH (target:{target_label}) WHERE toLower(val) = toLower(target.{target_property})",
                    effects=(
                        AddRelationship(
                            "dns",
                            "DNS_POINTS_TO",
                            "target",
                            source_label="DNSRecord",
                            target_label=target_label,
                        ),
                    ),
                ),
            ),
        )
        for target_label, target_property, match_filter, cleanup_where in DNS_RECORD_TARGETS
    )
)
LOADBALANCER_EXPOSE_CONTAINER = AnalysisJob(
    name="Ontology - LoadBalancer to Container linking",
    short_name="ontology_loadbalancers_linking",
    statements=(
        AnalysisStatement(
            match="MATCH (lb:LoadBalancer {lastupdated: $UPDATE_TAG})-[:EXPOSE]->(ip:EC2PrivateIp)<-[:PRIVATE_IP_ADDRESS]-(ni:NetworkInterface)<-[:NETWORK_INTERFACE]-(task:ECSTask)-[:HAS_CONTAINER]->(c:Container)",
            effects=(
                AddRelationship(
                    "lb",
                    "EXPOSE",
                    "c",
                    source_label="LoadBalancer",
                    target_label="Container",
                ),
            ),
        ),
    ),
)
PACKAGE_DEPLOYED_IMAGE_JOBS = (
    AnalysisJob(
        name="Ontology - Trivy Package DEPLOYED Image linking",
        short_name="ontology_packages_trivy_deployed",
        statements=(
            AnalysisStatement(
                match="MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)-[:DEPLOYED]->(img:Image)",
                effects=(
                    AddRelationship(
                        "p",
                        "DEPLOYED",
                        "img",
                        source_label="Package",
                        target_label="Image",
                    ),
                ),
            ),
        ),
    ),
    AnalysisJob(
        name="Ontology - Syft Package DEPLOYED Image linking",
        short_name="ontology_packages_syft_deployed",
        statements=(
            AnalysisStatement(
                match="MATCH (p:Package)-[:DETECTED_AS]->(sp:SyftPackage)-[:DEPLOYED]->(img:Image)",
                effects=(
                    AddRelationship(
                        "p",
                        "DEPLOYED",
                        "img",
                        source_label="Package",
                        target_label="Image",
                    ),
                ),
            ),
        ),
    ),
)
PACKAGE_AFFECTS_LINKING = AnalysisJob(
    name="Ontology - TrivyImageFinding AFFECTS Package linking",
    short_name="ontology_packages_affects",
    statements=(
        AnalysisStatement(
            match="MATCH (f:TrivyImageFinding)-[:AFFECTS]->(tp:TrivyPackage)<-[:DETECTED_AS]-(p:Package)",
            effects=(
                AddRelationship(
                    "f",
                    "AFFECTS",
                    "p",
                    source_label="TrivyImageFinding",
                    target_label="Package",
                ),
            ),
        ),
    ),
)
PACKAGE_AFFECTS_SEMGREP_SCA_LINKING = AnalysisJob(
    name="Ontology - SemgrepSCAFinding AFFECTS Package linking",
    short_name="ontology_packages_semgrep_sca_affects",
    statements=(
        AnalysisStatement(
            match="MATCH (f:SemgrepSCAFinding)-[:AFFECTS]->(d:SemgrepDependency)<-[:DETECTED_AS]-(p:Package)",
            effects=(
                AddRelationship(
                    "f",
                    "AFFECTS",
                    "p",
                    source_label="SemgrepSCAFinding",
                    target_label="Package",
                ),
            ),
        ),
    ),
)
PACKAGE_SHOULD_UPDATE_TO_LINKING = AnalysisJob(
    name="Ontology - Package SHOULD_UPDATE_TO TrivyFix linking",
    short_name="ontology_packages_should_update_to",
    statements=(
        AnalysisStatement(
            match="MATCH (p:Package)-[:DETECTED_AS]->(tp:TrivyPackage)-[:SHOULD_UPDATE_TO]->(fix:TrivyFix)",
            effects=(
                AddRelationship(
                    "p",
                    "SHOULD_UPDATE_TO",
                    "fix",
                    source_label="Package",
                    target_label="TrivyFix",
                ),
            ),
        ),
    ),
)
PACKAGE_DEPENDS_ON_LINKING = AnalysisJob(
    name="Ontology - Package DEPENDS_ON Package linking",
    short_name="ontology_packages_depends_on",
    statements=(
        AnalysisStatement(
            match="MATCH (p1:Package)-[:DETECTED_AS]->(sp1:SyftPackage)-[:DEPENDS_ON]->(sp2:SyftPackage)<-[:DETECTED_AS]-(p2:Package)",
            effects=(
                AddRelationship(
                    "p1",
                    "DEPENDS_ON",
                    "p2",
                    source_label="Package",
                    target_label="Package",
                ),
            ),
        ),
    ),
)
PACKAGE_LINKING_JOBS = (
    *PACKAGE_DEPLOYED_IMAGE_JOBS,
    PACKAGE_AFFECTS_LINKING,
    PACKAGE_AFFECTS_SEMGREP_SCA_LINKING,
    PACKAGE_SHOULD_UPDATE_TO_LINKING,
    PACKAGE_DEPENDS_ON_LINKING,
)
PUBLIC_IP_POINTS_TO_DEVICE = AnalysisJob(
    name="Ontology - PublicIP POINTS_TO Device linking",
    short_name="ontology_publicips_linking",
    statements=(
        AnalysisStatement(
            match="MATCH (p:PublicIP), (host:CrowdstrikeHost)<-[:OBSERVED_AS]-(d:Device) WHERE p.lastupdated = $UPDATE_TAG AND host.lastupdated = $UPDATE_TAG AND d.lastupdated = $UPDATE_TAG AND host.external_ip = p.ip_address",
            effects=(
                AddRelationship(
                    "p",
                    "POINTS_TO",
                    "d",
                    source_label="PublicIP",
                    target_label="Device",
                ),
            ),
        ),
    ),
)
USER_HAS_AWS_SSO_ACCOUNT = AnalysisJob(
    name="Ontology - AWSSSOUser HAS_ACCOUNT User linking",
    short_name="ontology_users_aws_sso",
    statements=(
        AnalysisStatement(
            match="MATCH (sso:AWSSSOUser) MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount {id: sso.external_id})",
            effects=(
                AddRelationship(
                    "u",
                    "HAS_ACCOUNT",
                    "sso",
                    source_label="User",
                    target_label="AWSSSOUser",
                ),
            ),
        ),
    ),
)
USER_HAS_GITHUB_ACCOUNT = AnalysisJob(
    name="Ontology - GitHubUser HAS_ACCOUNT User linking",
    short_name="ontology_users_github",
    statements=(
        AnalysisStatement(
            match="MATCH (u:User) WHERE u.email is not NULL MATCH (g:GitHubUser) WHERE u.email in g.organization_verified_domain_emails",
            effects=(
                AddRelationship(
                    "u",
                    "HAS_ACCOUNT",
                    "g",
                    source_label="User",
                    target_label="GitHubUser",
                ),
            ),
        ),
    ),
)
USER_OWNS_API_KEY = AnalysisJob(
    name="Ontology - User OWNS APIKey linking",
    short_name="ontology_users_api_key",
    statements=(
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount)<-[:OWNED_BY]-(k:APIKey)",
            effects=(
                AddRelationship(
                    "u", "OWNS", "k", source_label="User", target_label="APIKey"
                ),
            ),
        ),
    ),
)
USER_AUTHORIZED_THIRD_PARTY_APP = AnalysisJob(
    name="Ontology - User AUTHORIZED ThirdPartyApp linking",
    short_name="ontology_users_third_party_app",
    statements=(
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:UserAccount)-[authr:AUTHORIZED|APPLICATION]->(a:ThirdPartyApp)",
            effects=(
                AddRelationship(
                    "u",
                    "AUTHORIZED",
                    "a",
                    properties={"scopes": RawCypher("coalesce(authr.scopes, [])")},
                    source_label="User",
                    target_label="ThirdPartyApp",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (u:User)-[:HAS_ACCOUNT]->(:OktaUser)-[:MEMBER_OF_OKTA_GROUP]->(:OktaGroup)-[:APPLICATION]->(a:ThirdPartyApp)",
            effects=(
                AddRelationship(
                    "u",
                    "AUTHORIZED",
                    "a",
                    source_label="User",
                    target_label="ThirdPartyApp",
                ),
            ),
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
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (c:Container)-[:HAS_IMAGE]->(i:Image) WHERE NOT i:ImageManifestList",
            effects=(
                AddRelationship(
                    "c",
                    "RESOLVED_IMAGE",
                    "i",
                    source_label="Container",
                    target_label="Image",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (c:Container)-[:HAS_IMAGE]->(:ImageManifestList)-[:CONTAINS_IMAGE]->(i:Image) WHERE c.architecture_normalized IS NOT NULL AND i._ont_architecture = c.architecture_normalized WITH c, collect(DISTINCT i) AS candidates WHERE size(candidates) = 1 WITH c, candidates[0] AS img",
            effects=(
                AddRelationship(
                    "c",
                    "RESOLVED_IMAGE",
                    "img",
                    source_label="Container",
                    target_label="Image",
                ),
            ),
        ),
    ),
)
FUNCTION_RESOLVED_IMAGE = AnalysisJob(
    name="Function RESOLVED_IMAGE analysis",
    short_name="resolved_image_analysis_function",
    cleanup_iterationsize=1000,
    statements=(
        AnalysisStatement(
            match="MATCH (f:Function)-[:HAS_IMAGE]->(i:Image) WHERE NOT i:ImageManifestList",
            effects=(
                AddRelationship(
                    "f",
                    "RESOLVED_IMAGE",
                    "i",
                    source_label="Function",
                    target_label="Image",
                ),
            ),
        ),
        AnalysisStatement(
            match="MATCH (f:Function)-[:HAS_IMAGE]->(:ImageManifestList)-[:CONTAINS_IMAGE]->(i:Image) WHERE f.architecture_normalized IS NOT NULL AND i._ont_architecture = f.architecture_normalized WITH f, collect(DISTINCT i) AS candidates WHERE size(candidates) = 1 WITH f, candidates[0] AS img",
            effects=(
                AddRelationship(
                    "f",
                    "RESOLVED_IMAGE",
                    "img",
                    source_label="Function",
                    target_label="Image",
                ),
            ),
        ),
    ),
)
RESOLVED_IMAGE_JOBS = (CONTAINER_RESOLVED_IMAGE, FUNCTION_RESOLVED_IMAGE)
SUPPLY_CHAIN_SOURCE_FILE = AnalysisJob(
    name="Enrich PACKAGED_FROM with source_file from Image provenance",
    short_name="supply_chain_source_file",
    statements=(
        AnalysisStatement(
            query="MATCH (i:Image)-[r:PACKAGED_FROM]->() WHERE r.dockerfile_path IS NULL AND i.source_file IS NOT NULL SET r.dockerfile_path = i.source_file",
        ),
    ),
)
