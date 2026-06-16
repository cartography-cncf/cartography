from dataclasses import dataclass
from pathlib import Path

from cartography.graph.analysis import AnalysisJob
from cartography.graph.analysis import AnalysisScope
from cartography.graph.analysis import AnalysisStatement
from cartography.graph.analysis import PropertyEffect
from cartography.graph.analysis import RelationshipEffect
from cartography.graph.analysis import RelationshipPropertyEffect

STUB_STATEMENTS = (AnalysisStatement("RETURN 1"),)

AWS = AnalysisScope("AWSAccount", "AWS_ID")
AZURE = AnalysisScope("AzureSubscription", "AZURE_SUBSCRIPTION_ID")
ENTRA = AnalysisScope("EntraTenant", "TENANT_ID")
GCP = AnalysisScope("GCPProject", "PROJECT_ID")
K8S = AnalysisScope("KubernetesCluster", "CLUSTER_ID")
SEMGREP = AnalysisScope("SemgrepDeployment", "DEPLOYMENT_ID")


@dataclass(frozen=True)
class LegacyCoverage:
    reason: str


Coverage = AnalysisJob | LegacyCoverage


def prop(
    name: str,
    label: str,
    *properties: str,
    scope: AnalysisScope | None = None,
) -> AnalysisJob:
    return AnalysisJob(
        name=name,
        short_name=name,
        scope=scope,
        effect=PropertyEffect(label, properties),
        statements=STUB_STATEMENTS,
    )


def rel(
    name: str,
    source: str,
    rel_label: str,
    target: str,
    *properties: str,
    scope: AnalysisScope | None = None,
    scoped_to: str = "source",
) -> AnalysisJob:
    return AnalysisJob(
        name=name,
        short_name=name,
        scope=scope,
        effect=RelationshipEffect(
            source,
            rel_label,
            target,
            properties=properties,
            scoped_to=scoped_to,  # type: ignore[arg-type]
        ),
        statements=STUB_STATEMENTS,
    )


def rel_prop(
    name: str,
    source: str,
    rel_label: str,
    *properties: str,
    target: str | None = None,
    scope: AnalysisScope | None = None,
) -> AnalysisJob:
    return AnalysisJob(
        name=name,
        short_name=name,
        scope=scope,
        effect=RelationshipPropertyEffect(
            source,
            rel_label,
            properties,
            target_label=target,
        ),
        statements=STUB_STATEMENTS,
    )


def legacy(reason: str) -> LegacyCoverage:
    return LegacyCoverage(reason)


EXISTING_ANALYSIS_JOB_COVERAGE: dict[str, tuple[Coverage, ...]] = {
    "analysis/aibom_runs_on_container_analysis.json": (
        rel("aibom_runs_on_container_analysis", "AIBOMSource", "RUNS_ON", "Container"),
    ),
    "analysis/aws_ec2_asset_exposure.json": (
        prop(
            "aws_ec2_asset_exposure_asg",
            "AutoScalingGroup",
            "exposed_internet",
            "exposed_internet_type",
        ),
        prop(
            "aws_ec2_asset_exposure_instance",
            "EC2Instance",
            "exposed_internet",
            "exposed_internet_type",
        ),
        prop(
            "aws_ec2_asset_exposure_elb",
            "LoadBalancer",
            "exposed_internet",
            "exposed_internet_type",
        ),
        prop(
            "aws_ec2_asset_exposure_elbv2",
            "LoadBalancerV2",
            "exposed_internet",
            "exposed_internet_type",
        ),
    ),
    "analysis/aws_ec2_keypair_analysis.json": (
        prop(
            "aws_ec2_keypair_analysis_props",
            "EC2KeyPair",
            "user_uploaded",
            "duplicate_keyfingerprint",
        ),
        rel(
            "aws_ec2_keypair_analysis_matching",
            "EC2KeyPair",
            "MATCHING_FINGERPRINT",
            "EC2KeyPair",
        ),
    ),
    "analysis/aws_ecs_asset_exposure.json": (
        prop(
            "aws_ecs_asset_exposure",
            "ECSContainer",
            "exposed_internet",
            "exposed_internet_type",
        ),
    ),
    "analysis/aws_eks_asset_exposure.json": (
        prop("aws_eks_asset_exposure", "EKSCluster", "exposed_internet"),
    ),
    "analysis/aws_foreign_accounts.json": (
        prop("aws_foreign_accounts", "AWSAccount", "foreign"),
    ),
    "analysis/aws_ip_node_label_migration.json": (
        legacy("deletes obsolete mixed AWS/GCP IP labels and RESOURCE edges"),
    ),
    "analysis/aws_lambda_ecr.json": (
        rel("aws_lambda_ecr", "AWSLambda", "HAS", "ECRImage"),
    ),
    "analysis/azure_compute_asset_exposure.json": (
        prop(
            "azure_compute_asset_exposure_vm",
            "AzureVirtualMachine",
            "exposed_internet",
            "exposed_internet_type",
        ),
        prop(
            "azure_compute_asset_exposure_lb",
            "AzureLoadBalancer",
            "exposed_internet",
            "exposed_internet_type",
        ),
        prop(
            "azure_compute_asset_exposure_container",
            "AzureGroupContainer",
            "exposed_internet",
            "exposed_internet_type",
        ),
    ),
    "analysis/azure_container_label_swap_migration.json": (
        legacy("swaps labels during Azure container migration"),
    ),
    "analysis/crowdstrike_tenant_resource_edge_migration.json": (
        legacy("creates CrowdstrikeTenant nodes before backfilling RESOURCE edges"),
        rel(
            "crowdstrike_tenant_host_resource",
            "CrowdstrikeTenant",
            "RESOURCE",
            "CrowdstrikeHost",
        ),
        rel(
            "crowdstrike_tenant_vulnerability_resource",
            "CrowdstrikeTenant",
            "RESOURCE",
            "SpotlightVulnerability",
        ),
    ),
    "analysis/gcp_bucket_public_projection.json": (
        prop("gcp_bucket_public_projection", "GCPBucket", "_ont_public"),
    ),
    "analysis/gcp_cloudrun_label_migration.json": (
        legacy("removes stale ontology labels from GCP Cloud Run nodes"),
    ),
    "analysis/gcp_compute_instance_vpc_analysis.json": (
        rel(
            "gcp_compute_instance_vpc_analysis",
            "GCPInstance",
            "MEMBER_OF_GCP_VPC",
            "GCPVpc",
        ),
    ),
    "analysis/gcp_gke_asset_exposure.json": (
        prop("gcp_gke_asset_exposure", "GKECluster", "exposed_internet"),
    ),
    "analysis/gcp_gke_basic_auth.json": (
        prop("gcp_gke_basic_auth", "GKECluster", "basic_auth"),
    ),
    "analysis/gcp_ip_node_label_migration.json": (
        legacy("deletes obsolete mixed GCP/AWS IP labels and RESOURCE edges"),
    ),
    "analysis/gcp_role_resource_edge_migration.json": (
        legacy(
            "deletes obsolete RESOURCE edges for global and organization GCPRole nodes"
        ),
    ),
    "analysis/github_branch_protection_rule_resource_edge_migration.json": (
        rel(
            "github_branch_protection_rule_resource_edge_migration",
            "GitHubOrganization",
            "RESOURCE",
            "GitHubBranchProtectionRule",
        ),
    ),
    "analysis/github_dependency_manifest_resource_edge_migration.json": (
        rel(
            "github_dependency_manifest_resource_edge_migration",
            "GitHubOrganization",
            "RESOURCE",
            "DependencyGraphManifest",
        ),
    ),
    "analysis/github_repo_actions_secret_resource_edge_migration.json": (
        rel(
            "github_repo_actions_secret_resource_edge_migration_secret",
            "GitHubOrganization",
            "RESOURCE",
            "GitHubActionsSecret",
        ),
        rel(
            "github_repo_actions_secret_resource_edge_migration_variable",
            "GitHubOrganization",
            "RESOURCE",
            "GitHubActionsVariable",
        ),
    ),
    "analysis/gsuite_human_link.json": (
        rel("gsuite_human_link", "Human", "IDENTITY_GSUITE", "GSuiteUser"),
    ),
    "analysis/gsuite_resource_edge_direction_migration.json": (
        rel(
            "gsuite_resource_edge_direction_migration_user",
            "GSuiteTenant",
            "RESOURCE",
            "GSuiteUser",
        ),
        rel(
            "gsuite_resource_edge_direction_migration_group",
            "GSuiteTenant",
            "RESOURCE",
            "GSuiteGroup",
        ),
    ),
    "analysis/ontology_aws_user_projection.json": (
        prop("ontology_aws_user_projection", "AWSUser", "_ont_has_mfa", "_ont_active"),
    ),
    "analysis/ontology_devices_linking.json": (
        rel("ontology_devices_linking", "User", "OWNS", "Device"),
    ),
    "analysis/ontology_dnsrecords_linking.json": (
        rel(
            "ontology_dnsrecords_to_kubernetes_ingress",
            "DNSRecord",
            "DNS_POINTS_TO",
            "KubernetesIngress",
        ),
        rel(
            "ontology_dnsrecords_to_aws_elbv2",
            "DNSRecord",
            "DNS_POINTS_TO",
            "AWSLoadBalancerV2",
        ),
        rel(
            "ontology_gcp_recordset_to_aws_elbv2",
            "GCPRecordSet",
            "DNS_POINTS_TO",
            "AWSLoadBalancerV2",
        ),
        rel(
            "ontology_dnsrecords_to_aws_elb",
            "DNSRecord",
            "DNS_POINTS_TO",
            "AWSLoadBalancer",
        ),
        rel(
            "ontology_gcp_recordset_to_aws_elb",
            "GCPRecordSet",
            "DNS_POINTS_TO",
            "AWSLoadBalancer",
        ),
        rel(
            "ontology_dnsrecords_to_cloudfront",
            "DNSRecord",
            "DNS_POINTS_TO",
            "CloudFrontDistribution",
        ),
        rel(
            "ontology_gcp_recordset_to_cloudfront",
            "GCPRecordSet",
            "DNS_POINTS_TO",
            "CloudFrontDistribution",
        ),
        rel("ontology_dnsrecords_to_ec2", "DNSRecord", "DNS_POINTS_TO", "EC2Instance"),
        rel(
            "ontology_gcp_recordset_to_ec2",
            "GCPRecordSet",
            "DNS_POINTS_TO",
            "EC2Instance",
        ),
        rel(
            "ontology_dnsrecords_to_gcp_instance",
            "DNSRecord",
            "DNS_POINTS_TO",
            "GCPInstance",
        ),
        rel(
            "ontology_gcp_recordset_to_gcp_instance",
            "GCPRecordSet",
            "DNS_POINTS_TO",
            "GCPInstance",
        ),
        rel(
            "ontology_dnsrecords_to_azure_app_service",
            "DNSRecord",
            "DNS_POINTS_TO",
            "AzureAppService",
        ),
        rel(
            "ontology_gcp_recordset_to_azure_app_service",
            "GCPRecordSet",
            "DNS_POINTS_TO",
            "AzureAppService",
        ),
        rel(
            "ontology_dnsrecords_to_azure_function",
            "DNSRecord",
            "DNS_POINTS_TO",
            "AzureFunctionApp",
        ),
        rel(
            "ontology_gcp_recordset_to_azure_function",
            "GCPRecordSet",
            "DNS_POINTS_TO",
            "AzureFunctionApp",
        ),
    ),
    "analysis/ontology_entra_application_projection.json": (
        prop(
            "ontology_entra_application_projection",
            "EntraApplication",
            "_ont_enabled",
            scope=ENTRA,
        ),
    ),
    "analysis/ontology_loadbalancers_linking.json": (
        rel("ontology_loadbalancers_linking", "LoadBalancer", "EXPOSE", "Container"),
    ),
    "analysis/ontology_packages_linking.json": (
        rel("ontology_packages_deployed", "Package", "DEPLOYED", "Image"),
        rel("ontology_packages_affects", "TrivyImageFinding", "AFFECTS", "Package"),
        rel(
            "ontology_packages_should_update_to",
            "Package",
            "SHOULD_UPDATE_TO",
            "TrivyFix",
        ),
        rel("ontology_packages_depends_on", "Package", "DEPENDS_ON", "Package"),
    ),
    "analysis/ontology_publicips_linking.json": (
        rel("ontology_publicips_linking", "PublicIP", "POINTS_TO", "Device"),
    ),
    "analysis/ontology_users_linking.json": (
        rel("ontology_users_has_awssso", "User", "HAS_ACCOUNT", "AWSSSOUser"),
        rel("ontology_users_has_github", "User", "HAS_ACCOUNT", "GitHubUser"),
        rel("ontology_users_owns_apikey", "User", "OWNS", "APIKey"),
        rel("ontology_users_authorized_app", "User", "AUTHORIZED", "ThirdPartyApp"),
    ),
    "analysis/resolved_image_analysis.json": (
        rel(
            "resolved_container_image_analysis", "Container", "RESOLVED_IMAGE", "Image"
        ),
        rel("resolved_function_image_analysis", "Function", "RESOLVED_IMAGE", "Image"),
    ),
    "analysis/supply_chain_source_file.json": (
        rel_prop(
            "supply_chain_source_file", "Image", "PACKAGED_FROM", "dockerfile_path"
        ),
    ),
    "scoped_analysis/aws_ec2_iaminstanceprofile.json": (
        rel(
            "aws_ec2_iaminstanceprofile",
            "EC2Instance",
            "STS_ASSUMEROLE_ALLOW",
            "AWSRole",
            scope=AWS,
        ),
    ),
    "scoped_analysis/aws_lb_container_exposure.json": (
        rel(
            "aws_lb_container_exposure",
            "AWSLoadBalancerV2",
            "EXPOSE",
            "ECSContainer",
            "exposure_type",
            scope=AWS,
        ),
    ),
    "scoped_analysis/aws_lb_nacl_direct.json": (
        rel(
            "aws_lb_nacl_direct",
            "EC2NetworkAcl",
            "PROTECTS",
            "AWSLoadBalancerV2",
            scope=AWS,
            scoped_to="target",
        ),
    ),
    "scoped_analysis/aws_s3acl_analysis.json": (
        prop(
            "aws_s3acl_analysis",
            "S3Bucket",
            "anonymous_access",
            "anonymous_actions",
            scope=AWS,
        ),
    ),
    "scoped_analysis/azure_firewall_lb_protection.json": (
        rel(
            "azure_firewall_lb_protection",
            "AzureFirewall",
            "PROTECTS",
            "AzureLoadBalancer",
            scope=AZURE,
        ),
    ),
    "scoped_analysis/azure_lb_exposure.json": (
        rel(
            "azure_lb_exposure",
            "AzureLoadBalancer",
            "EXPOSE",
            "AzureVirtualMachine",
            "exposure_type",
            scope=AZURE,
        ),
    ),
    "scoped_analysis/gcp_artifact_registry_image_migration_cleanup.json": (
        legacy("deletes obsolete GCP Artifact Registry image nodes"),
    ),
    "scoped_analysis/gcp_artifact_registry_orphan_image_cleanup.json": (
        legacy("deletes orphan GCP Artifact Registry image nodes"),
    ),
    "scoped_analysis/gcp_compute_exposure.json": (
        prop(
            "gcp_compute_forwarding_rule_exposure",
            "GCPForwardingRule",
            "exposed_internet",
            "exposed_internet_type",
            scope=GCP,
        ),
        prop(
            "gcp_compute_instance_exposure",
            "GCPInstance",
            "exposed_internet",
            "exposed_internet_type",
            scope=GCP,
        ),
        prop(
            "gcp_compute_cloudrun_exposure",
            "GCPCloudRunService",
            "exposed_internet",
            "exposed_internet_type",
            scope=GCP,
        ),
        rel(
            "gcp_compute_firewall_ingress",
            "GCPFirewall",
            "FIREWALL_INGRESS",
            "GCPInstance",
            scope=GCP,
        ),
    ),
    "scoped_analysis/gcp_lb_exposure.json": (
        rel(
            "gcp_lb_exposure",
            "GCPBackendService",
            "EXPOSE",
            "GCPInstance",
            "exposure_type",
            scope=GCP,
        ),
    ),
    "scoped_analysis/intune_compliance_policy_device.json": (
        rel(
            "intune_compliance_policy_device",
            "IntuneCompliancePolicy",
            "APPLIES_TO",
            "IntuneManagedDevice",
            scope=ENTRA,
        ),
    ),
    "scoped_analysis/k8s_compute_asset_exposure.json": (
        prop(
            "k8s_service_asset_exposure",
            "KubernetesService",
            "exposed_internet",
            "exposed_internet_type",
            scope=K8S,
        ),
        prop(
            "k8s_pod_asset_exposure",
            "KubernetesPod",
            "exposed_internet",
            "exposed_internet_type",
            scope=K8S,
        ),
        prop(
            "k8s_container_asset_exposure",
            "KubernetesContainer",
            "exposed_internet",
            "exposed_internet_type",
            scope=K8S,
        ),
    ),
    "scoped_analysis/k8s_lb_exposure.json": (
        rel(
            "k8s_lb_pod_exposure",
            "AWSLoadBalancerV2",
            "EXPOSE",
            "KubernetesPod",
            "exposure_type",
            scope=K8S,
            scoped_to="target",
        ),
        rel(
            "k8s_lb_container_exposure",
            "AWSLoadBalancerV2",
            "EXPOSE",
            "KubernetesContainer",
            "exposure_type",
            scope=K8S,
            scoped_to="target",
        ),
    ),
    "scoped_analysis/semgrep_sast_risk_analysis.json": (
        prop(
            "semgrep_sast_risk_analysis",
            "SemgrepSASTFinding",
            "risk_severity",
            scope=SEMGREP,
        ),
    ),
    "scoped_analysis/semgrep_sca_risk_analysis.json": (
        prop(
            "semgrep_sca_risk_analysis",
            "SemgrepSCAFinding",
            "reachability_risk",
            scope=SEMGREP,
        ),
    ),
}


def _existing_analysis_job_keys() -> set[str]:
    keys: set[str] = set()
    for directory in (
        Path("cartography/data/jobs/analysis"),
        Path("cartography/data/jobs/scoped_analysis"),
    ):
        for path in directory.glob("*.json"):
            keys.add(f"{directory.name}/{path.name}")
    return keys


def test_all_existing_analysis_jobs_have_effect_coverage():
    # Arrange
    expected = _existing_analysis_job_keys()
    covered = set(EXISTING_ANALYSIS_JOB_COVERAGE)

    # Act
    missing = expected - covered
    stale = covered - expected

    # Assert
    assert missing == set()
    assert stale == set()


def test_existing_analysis_job_effect_coverage_is_introspectable():
    for job_key, coverage_items in EXISTING_ANALYSIS_JOB_COVERAGE.items():
        assert coverage_items, job_key
        for item in coverage_items:
            if isinstance(item, LegacyCoverage):
                assert item.reason
                continue

            assert item.relationships_added() or item.properties_set(), job_key
            assert item.to_graph_job().statements, job_key
