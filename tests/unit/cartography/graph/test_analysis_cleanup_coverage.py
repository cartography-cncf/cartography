import pytest

from cartography.graph.analysis import CleanupScopedTo
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipEffect
from cartography.graph.analysisbuilder import cleanup_query

AWS = CleanupScopedTo("AWSAccount", "AWS_ID")
AZURE = CleanupScopedTo("AzureSubscription", "AZURE_SUBSCRIPTION_ID")
ENTRA = CleanupScopedTo("EntraTenant", "TENANT_ID")
GCP = CleanupScopedTo("GCPProject", "PROJECT_ID")
K8S = CleanupScopedTo("KubernetesCluster", "CLUSTER_ID")
SEMGREP = CleanupScopedTo("SemgrepDeployment", "DEPLOYMENT_ID")


def _rel_cleanup(
    source: str,
    rel: str,
    target: str,
    *,
    scope: CleanupScopedTo | None = None,
    scoped_to: str = "source",
) -> str:
    match = f"MATCH (source:{source})-[r:{rel}]->(target:{target})"
    if scope:
        match = (
            f"MATCH (scope:{scope.label} {{id: ${scope.id_param}}})"
            f"-[:RESOURCE]->({scoped_to})\n"
            f"{match}"
        )
    return (
        f"{match}\n"
        "WHERE r.lastupdated <> $UPDATE_TAG\n"
        "WITH r LIMIT $LIMIT_SIZE\n"
        "DELETE r"
    )


def _prop_cleanup(
    label: str,
    *props: str,
    scope: CleanupScopedTo | None = None,
) -> str:
    node = f"(node:{label})"
    match = f"MATCH {node}"
    if scope:
        match = (
            f"MATCH (scope:{scope.label} {{id: ${scope.id_param}}})-[:RESOURCE]->{node}"
        )
    filters = " OR ".join(f"node.{prop} IS NOT NULL" for prop in props)
    return (
        f"{match}\n"
        f"WHERE {filters}\n"
        "WITH node LIMIT $LIMIT_SIZE\n"
        f"REMOVE {', '.join(f'node.{prop}' for prop in props)}"
    )


CLEANUP_CASES = [
    pytest.param(
        RelationshipEffect("AIBOMSource", "RUNS_ON", "Container"),
        None,
        _rel_cleanup("AIBOMSource", "RUNS_ON", "Container"),
        id="aibom_runs_on_container_analysis",
    ),
    pytest.param(
        PropertyEffect(
            "AutoScalingGroup", ("exposed_internet", "exposed_internet_type")
        ),
        None,
        _prop_cleanup("AutoScalingGroup", "exposed_internet", "exposed_internet_type"),
        id="aws_ec2_asset_exposure_asg",
    ),
    pytest.param(
        PropertyEffect("EC2Instance", ("exposed_internet", "exposed_internet_type")),
        None,
        _prop_cleanup("EC2Instance", "exposed_internet", "exposed_internet_type"),
        id="aws_ec2_asset_exposure_instance",
    ),
    pytest.param(
        PropertyEffect(
            "AWSLoadBalancer", ("exposed_internet", "exposed_internet_type")
        ),
        None,
        _prop_cleanup("AWSLoadBalancer", "exposed_internet", "exposed_internet_type"),
        id="aws_ec2_asset_exposure_elb",
    ),
    pytest.param(
        PropertyEffect(
            "AWSLoadBalancerV2", ("exposed_internet", "exposed_internet_type")
        ),
        None,
        _prop_cleanup("AWSLoadBalancerV2", "exposed_internet", "exposed_internet_type"),
        id="aws_ec2_asset_exposure_elbv2",
    ),
    pytest.param(
        PropertyEffect("EC2KeyPair", ("user_uploaded", "duplicate_keyfingerprint")),
        None,
        _prop_cleanup("EC2KeyPair", "user_uploaded", "duplicate_keyfingerprint"),
        id="aws_ec2_keypair_analysis_props",
    ),
    pytest.param(
        RelationshipEffect("EC2KeyPair", "MATCHING_FINGERPRINT", "EC2KeyPair"),
        None,
        _rel_cleanup("EC2KeyPair", "MATCHING_FINGERPRINT", "EC2KeyPair"),
        id="aws_ec2_keypair_analysis_rel",
    ),
    pytest.param(
        PropertyEffect("ECSContainer", ("exposed_internet", "exposed_internet_type")),
        None,
        _prop_cleanup("ECSContainer", "exposed_internet", "exposed_internet_type"),
        id="aws_ecs_asset_exposure",
    ),
    pytest.param(
        PropertyEffect("EKSCluster", ("exposed_internet",)),
        None,
        _prop_cleanup("EKSCluster", "exposed_internet"),
        id="aws_eks_asset_exposure",
    ),
    pytest.param(
        PropertyEffect("AWSAccount", ("foreign",)),
        None,
        _prop_cleanup("AWSAccount", "foreign"),
        id="aws_foreign_accounts",
    ),
    pytest.param(
        RelationshipEffect("AWSLambda", "HAS", "ECRImage"),
        None,
        _rel_cleanup("AWSLambda", "HAS", "ECRImage"),
        id="aws_lambda_ecr",
    ),
    pytest.param(
        PropertyEffect(
            "AzureVirtualMachine", ("exposed_internet", "exposed_internet_type")
        ),
        None,
        _prop_cleanup(
            "AzureVirtualMachine", "exposed_internet", "exposed_internet_type"
        ),
        id="azure_compute_asset_exposure_vm",
    ),
    pytest.param(
        PropertyEffect(
            "AzureLoadBalancer", ("exposed_internet", "exposed_internet_type")
        ),
        None,
        _prop_cleanup("AzureLoadBalancer", "exposed_internet", "exposed_internet_type"),
        id="azure_compute_asset_exposure_lb",
    ),
    pytest.param(
        PropertyEffect(
            "AzureGroupContainer", ("exposed_internet", "exposed_internet_type")
        ),
        None,
        _prop_cleanup(
            "AzureGroupContainer", "exposed_internet", "exposed_internet_type"
        ),
        id="azure_compute_asset_exposure_container",
    ),
    pytest.param(
        PropertyEffect("GCPBucket", ("_ont_public",)),
        None,
        _prop_cleanup("GCPBucket", "_ont_public"),
        id="gcp_bucket_public_projection",
    ),
    pytest.param(
        RelationshipEffect("GCPInstance", "MEMBER_OF_GCP_VPC", "GCPVpc"),
        None,
        _rel_cleanup("GCPInstance", "MEMBER_OF_GCP_VPC", "GCPVpc"),
        id="gcp_compute_instance_vpc_analysis",
    ),
    pytest.param(
        RelationshipEffect("Human", "IDENTITY_GSUITE", "GSuiteUser"),
        None,
        _rel_cleanup("Human", "IDENTITY_GSUITE", "GSuiteUser"),
        id="gsuite_human_link",
    ),
    pytest.param(
        PropertyEffect("GKECluster", ("exposed_internet",)),
        None,
        _prop_cleanup("GKECluster", "exposed_internet"),
        id="gcp_gke_asset_exposure",
    ),
    pytest.param(
        PropertyEffect("GKECluster", ("basic_auth",)),
        None,
        _prop_cleanup("GKECluster", "basic_auth"),
        id="gcp_gke_basic_auth",
    ),
    pytest.param(
        PropertyEffect("AWSUser", ("_ont_has_mfa", "_ont_active")),
        None,
        _prop_cleanup("AWSUser", "_ont_has_mfa", "_ont_active"),
        id="ontology_aws_user_projection",
    ),
    pytest.param(
        RelationshipEffect("User", "OWNS", "Device"),
        None,
        _rel_cleanup("User", "OWNS", "Device"),
        id="ontology_devices_linking",
    ),
    pytest.param(
        RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "KubernetesIngress"),
        None,
        _rel_cleanup("DNSRecord", "DNS_POINTS_TO", "KubernetesIngress"),
        id="ontology_dnsrecords_to_kubernetes_ingress",
    ),
    pytest.param(
        RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "AWSLoadBalancerV2"),
        None,
        _rel_cleanup("DNSRecord", "DNS_POINTS_TO", "AWSLoadBalancerV2"),
        id="ontology_dnsrecords_to_aws_elbv2",
    ),
    pytest.param(
        RelationshipEffect("GCPRecordSet", "DNS_POINTS_TO", "AWSLoadBalancerV2"),
        None,
        _rel_cleanup("GCPRecordSet", "DNS_POINTS_TO", "AWSLoadBalancerV2"),
        id="ontology_gcp_recordset_to_aws_elbv2",
    ),
    pytest.param(
        RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "AWSLoadBalancer"),
        None,
        _rel_cleanup("DNSRecord", "DNS_POINTS_TO", "AWSLoadBalancer"),
        id="ontology_dnsrecords_to_aws_elb",
    ),
    pytest.param(
        RelationshipEffect("GCPRecordSet", "DNS_POINTS_TO", "AWSLoadBalancer"),
        None,
        _rel_cleanup("GCPRecordSet", "DNS_POINTS_TO", "AWSLoadBalancer"),
        id="ontology_gcp_recordset_to_aws_elb",
    ),
    pytest.param(
        RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "CloudFrontDistribution"),
        None,
        _rel_cleanup("DNSRecord", "DNS_POINTS_TO", "CloudFrontDistribution"),
        id="ontology_dnsrecords_to_cloudfront",
    ),
    pytest.param(
        RelationshipEffect("GCPRecordSet", "DNS_POINTS_TO", "CloudFrontDistribution"),
        None,
        _rel_cleanup("GCPRecordSet", "DNS_POINTS_TO", "CloudFrontDistribution"),
        id="ontology_gcp_recordset_to_cloudfront",
    ),
    pytest.param(
        RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "EC2Instance"),
        None,
        _rel_cleanup("DNSRecord", "DNS_POINTS_TO", "EC2Instance"),
        id="ontology_dnsrecords_to_ec2",
    ),
    pytest.param(
        RelationshipEffect("GCPRecordSet", "DNS_POINTS_TO", "EC2Instance"),
        None,
        _rel_cleanup("GCPRecordSet", "DNS_POINTS_TO", "EC2Instance"),
        id="ontology_gcp_recordset_to_ec2",
    ),
    pytest.param(
        RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "GCPInstance"),
        None,
        _rel_cleanup("DNSRecord", "DNS_POINTS_TO", "GCPInstance"),
        id="ontology_dnsrecords_to_gcp_instance",
    ),
    pytest.param(
        RelationshipEffect("GCPRecordSet", "DNS_POINTS_TO", "GCPInstance"),
        None,
        _rel_cleanup("GCPRecordSet", "DNS_POINTS_TO", "GCPInstance"),
        id="ontology_gcp_recordset_to_gcp_instance",
    ),
    pytest.param(
        RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "AzureAppService"),
        None,
        _rel_cleanup("DNSRecord", "DNS_POINTS_TO", "AzureAppService"),
        id="ontology_dnsrecords_to_azure_app_service",
    ),
    pytest.param(
        RelationshipEffect("GCPRecordSet", "DNS_POINTS_TO", "AzureAppService"),
        None,
        _rel_cleanup("GCPRecordSet", "DNS_POINTS_TO", "AzureAppService"),
        id="ontology_gcp_recordset_to_azure_app_service",
    ),
    pytest.param(
        RelationshipEffect("DNSRecord", "DNS_POINTS_TO", "AzureFunctionApp"),
        None,
        _rel_cleanup("DNSRecord", "DNS_POINTS_TO", "AzureFunctionApp"),
        id="ontology_dnsrecords_to_azure_function",
    ),
    pytest.param(
        RelationshipEffect("GCPRecordSet", "DNS_POINTS_TO", "AzureFunctionApp"),
        None,
        _rel_cleanup("GCPRecordSet", "DNS_POINTS_TO", "AzureFunctionApp"),
        id="ontology_gcp_recordset_to_azure_function",
    ),
    pytest.param(
        PropertyEffect("EntraApplication", ("_ont_enabled",)),
        ENTRA,
        _prop_cleanup("EntraApplication", "_ont_enabled", scope=ENTRA),
        id="ontology_entra_application_projection",
    ),
    pytest.param(
        RelationshipEffect("LoadBalancer", "EXPOSE", "Container"),
        None,
        _rel_cleanup("LoadBalancer", "EXPOSE", "Container"),
        id="ontology_loadbalancers_linking",
    ),
    pytest.param(
        RelationshipEffect("Package", "DEPLOYED", "Image"),
        None,
        _rel_cleanup("Package", "DEPLOYED", "Image"),
        id="ontology_packages_deployed",
    ),
    pytest.param(
        RelationshipEffect("TrivyImageFinding", "AFFECTS", "Package"),
        None,
        _rel_cleanup("TrivyImageFinding", "AFFECTS", "Package"),
        id="ontology_packages_affects",
    ),
    pytest.param(
        RelationshipEffect("Package", "SHOULD_UPDATE_TO", "TrivyFix"),
        None,
        _rel_cleanup("Package", "SHOULD_UPDATE_TO", "TrivyFix"),
        id="ontology_packages_should_update_to",
    ),
    pytest.param(
        RelationshipEffect("Package", "DEPENDS_ON", "Package"),
        None,
        _rel_cleanup("Package", "DEPENDS_ON", "Package"),
        id="ontology_packages_depends_on",
    ),
    pytest.param(
        RelationshipEffect("PublicIP", "POINTS_TO", "Device"),
        None,
        _rel_cleanup("PublicIP", "POINTS_TO", "Device"),
        id="ontology_publicips_linking",
    ),
    pytest.param(
        RelationshipEffect("User", "HAS_ACCOUNT", "AWSSSOUser"),
        None,
        _rel_cleanup("User", "HAS_ACCOUNT", "AWSSSOUser"),
        id="ontology_users_has_awssso",
    ),
    pytest.param(
        RelationshipEffect("User", "HAS_ACCOUNT", "GitHubUser"),
        None,
        _rel_cleanup("User", "HAS_ACCOUNT", "GitHubUser"),
        id="ontology_users_has_github",
    ),
    pytest.param(
        RelationshipEffect("User", "OWNS", "APIKey"),
        None,
        _rel_cleanup("User", "OWNS", "APIKey"),
        id="ontology_users_owns_apikey",
    ),
    pytest.param(
        RelationshipEffect("User", "AUTHORIZED", "ThirdPartyApp"),
        None,
        _rel_cleanup("User", "AUTHORIZED", "ThirdPartyApp"),
        id="ontology_users_authorized_app",
    ),
    pytest.param(
        RelationshipEffect("Container", "RESOLVED_IMAGE", "Image"),
        None,
        _rel_cleanup("Container", "RESOLVED_IMAGE", "Image"),
        id="resolved_image_container",
    ),
    pytest.param(
        RelationshipEffect("Function", "RESOLVED_IMAGE", "Image"),
        None,
        _rel_cleanup("Function", "RESOLVED_IMAGE", "Image"),
        id="resolved_image_function",
    ),
    pytest.param(
        RelationshipEffect("EC2Instance", "STS_ASSUMEROLE_ALLOW", "AWSRole"),
        AWS,
        _rel_cleanup("EC2Instance", "STS_ASSUMEROLE_ALLOW", "AWSRole", scope=AWS),
        id="aws_ec2_iaminstanceprofile",
    ),
    pytest.param(
        RelationshipEffect("AWSLoadBalancerV2", "EXPOSE", "ECSContainer"),
        AWS,
        _rel_cleanup("AWSLoadBalancerV2", "EXPOSE", "ECSContainer", scope=AWS),
        id="aws_lb_container_exposure",
    ),
    pytest.param(
        RelationshipEffect(
            "EC2NetworkAcl", "PROTECTS", "AWSLoadBalancerV2", scoped_to="target"
        ),
        AWS,
        _rel_cleanup(
            "EC2NetworkAcl",
            "PROTECTS",
            "AWSLoadBalancerV2",
            scope=AWS,
            scoped_to="target",
        ),
        id="aws_lb_nacl_direct",
    ),
    pytest.param(
        PropertyEffect("S3Bucket", ("anonymous_access",)),
        AWS,
        _prop_cleanup("S3Bucket", "anonymous_access", scope=AWS),
        id="aws_s3acl_analysis_access",
    ),
    pytest.param(
        PropertyEffect("S3Bucket", ("anonymous_actions",)),
        AWS,
        _prop_cleanup("S3Bucket", "anonymous_actions", scope=AWS),
        id="aws_s3acl_analysis_actions",
    ),
    pytest.param(
        RelationshipEffect("AzureFirewall", "PROTECTS", "AzureLoadBalancer"),
        AZURE,
        _rel_cleanup("AzureFirewall", "PROTECTS", "AzureLoadBalancer", scope=AZURE),
        id="azure_firewall_lb_protection",
    ),
    pytest.param(
        RelationshipEffect("AzureLoadBalancer", "EXPOSE", "AzureVirtualMachine"),
        AZURE,
        _rel_cleanup("AzureLoadBalancer", "EXPOSE", "AzureVirtualMachine", scope=AZURE),
        id="azure_lb_exposure",
    ),
    pytest.param(
        PropertyEffect(
            "GCPForwardingRule", ("exposed_internet", "exposed_internet_type")
        ),
        GCP,
        _prop_cleanup(
            "GCPForwardingRule", "exposed_internet", "exposed_internet_type", scope=GCP
        ),
        id="gcp_compute_forwarding_rule_exposure",
    ),
    pytest.param(
        PropertyEffect("GCPInstance", ("exposed_internet", "exposed_internet_type")),
        GCP,
        _prop_cleanup(
            "GCPInstance", "exposed_internet", "exposed_internet_type", scope=GCP
        ),
        id="gcp_compute_instance_exposure",
    ),
    pytest.param(
        PropertyEffect(
            "GCPCloudRunService", ("exposed_internet", "exposed_internet_type")
        ),
        GCP,
        _prop_cleanup(
            "GCPCloudRunService", "exposed_internet", "exposed_internet_type", scope=GCP
        ),
        id="gcp_compute_cloudrun_exposure",
    ),
    pytest.param(
        RelationshipEffect(
            "GCPFirewall",
            "FIREWALL_INGRESS",
            "GCPInstance",
            scoped_to="target",
        ),
        GCP,
        _rel_cleanup(
            "GCPFirewall",
            "FIREWALL_INGRESS",
            "GCPInstance",
            scope=GCP,
            scoped_to="target",
        ),
        id="gcp_compute_firewall_ingress",
    ),
    pytest.param(
        RelationshipEffect("GCPBackendService", "EXPOSE", "GCPInstance"),
        GCP,
        _rel_cleanup("GCPBackendService", "EXPOSE", "GCPInstance", scope=GCP),
        id="gcp_lb_exposure",
    ),
    pytest.param(
        RelationshipEffect(
            "IntuneCompliancePolicy", "APPLIES_TO", "IntuneManagedDevice"
        ),
        ENTRA,
        _rel_cleanup(
            "IntuneCompliancePolicy", "APPLIES_TO", "IntuneManagedDevice", scope=ENTRA
        ),
        id="intune_compliance_policy_device",
    ),
    pytest.param(
        PropertyEffect(
            "KubernetesService", ("exposed_internet", "exposed_internet_type")
        ),
        K8S,
        _prop_cleanup(
            "KubernetesService", "exposed_internet", "exposed_internet_type", scope=K8S
        ),
        id="k8s_service_asset_exposure",
    ),
    pytest.param(
        PropertyEffect("KubernetesPod", ("exposed_internet", "exposed_internet_type")),
        K8S,
        _prop_cleanup(
            "KubernetesPod", "exposed_internet", "exposed_internet_type", scope=K8S
        ),
        id="k8s_pod_asset_exposure",
    ),
    pytest.param(
        PropertyEffect(
            "KubernetesContainer", ("exposed_internet", "exposed_internet_type")
        ),
        K8S,
        _prop_cleanup(
            "KubernetesContainer",
            "exposed_internet",
            "exposed_internet_type",
            scope=K8S,
        ),
        id="k8s_container_asset_exposure",
    ),
    pytest.param(
        RelationshipEffect(
            "AWSLoadBalancerV2", "EXPOSE", "KubernetesPod", scoped_to="target"
        ),
        K8S,
        _rel_cleanup(
            "AWSLoadBalancerV2",
            "EXPOSE",
            "KubernetesPod",
            scope=K8S,
            scoped_to="target",
        ),
        id="k8s_lb_pod_exposure",
    ),
    pytest.param(
        RelationshipEffect(
            "AWSLoadBalancerV2", "EXPOSE", "KubernetesContainer", scoped_to="target"
        ),
        K8S,
        _rel_cleanup(
            "AWSLoadBalancerV2",
            "EXPOSE",
            "KubernetesContainer",
            scope=K8S,
            scoped_to="target",
        ),
        id="k8s_lb_container_exposure",
    ),
    pytest.param(
        PropertyEffect("SemgrepSASTFinding", ("risk_severity",)),
        SEMGREP,
        _prop_cleanup("SemgrepSASTFinding", "risk_severity", scope=SEMGREP),
        id="semgrep_sast_risk_analysis",
    ),
    pytest.param(
        PropertyEffect("SemgrepSCAFinding", ("reachability_risk",)),
        SEMGREP,
        _prop_cleanup("SemgrepSCAFinding", "reachability_risk", scope=SEMGREP),
        id="semgrep_sca_risk_analysis",
    ),
]


@pytest.mark.parametrize(("effect", "scope", "expected"), CLEANUP_CASES)
def test_generated_cleanup_queries_cover_existing_analysis_job_shapes(
    effect,
    scope,
    expected,
):
    assert cleanup_query(effect, scope) == expected
