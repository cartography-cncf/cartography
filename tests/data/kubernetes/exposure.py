import copy
import datetime
from uuid import uuid4

TEST_AWS_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_GCP_ZONE = "us-central1-a"
COMPUTE_URL = "https://www.googleapis.com/compute/v1"


def build_exposure_test_data() -> dict:
    case_id = uuid4().hex[:8]
    update_tag = 123456789

    cluster_id = f"arn:aws:eks:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:cluster/test-cluster-{case_id}"
    cluster_name = f"test-cluster-{case_id}"
    other_cluster_id = f"arn:aws:eks:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:cluster/other-cluster-{case_id}"
    other_cluster_name = f"other-cluster-{case_id}"
    binding_name = f"public-{case_id}"

    pod_lb_id = f"pod-lb-{case_id}"
    pod_ing_id = f"pod-ing-{case_id}"
    cont_lb_id = f"cont-lb-{case_id}"
    cont_ing_id = f"cont-ing-{case_id}"

    svc_lb_id = f"svc-lb-{case_id}"
    svc_ing_id = f"svc-clusterip-{case_id}"

    nlb_dns = f"nlb-{case_id}.elb.{TEST_REGION}.amazonaws.com"
    alb_dns = f"alb-{case_id}.elb.{TEST_REGION}.amazonaws.com"
    alb_tg_arn = f"arn:aws:elasticloadbalancing:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:targetgroup/test-alb-tg/{case_id}"

    gcp_project_id = f"test-project-{case_id}"
    gcp_negs_url = (
        f"projects/{gcp_project_id}/zones/{TEST_GCP_ZONE}/networkEndpointGroups"
    )
    neg_ext_id = f"{gcp_negs_url}/neg-ext-{case_id}"
    neg_int_id = f"{gcp_negs_url}/neg-int-{case_id}"
    ext_bs_id = f"projects/{gcp_project_id}/global/backendServices/ext-bs"

    test_cluster = [
        {
            "id": cluster_id,
            "name": cluster_name,
            "creation_timestamp": 1234567890,
            "external_id": cluster_id,
            "git_version": "v1.30.0",
            "version_major": 1,
            "version_minor": 30,
            "go_version": "go1.16.5",
            "compiler": "gc",
            "platform": "linux/amd64",
        },
    ]

    test_namespaces = [
        {
            "uid": f"default-ns-{case_id}",
            "name": "default",
            "creation_timestamp": 1633581666,
            "deletion_timestamp": None,
            "status_phase": "Active",
        },
    ]

    test_pods = [
        {
            "uid": pod_lb_id,
            "name": f"pod-lb-{case_id}",
            "status_phase": "running",
            "creation_timestamp": 1633581666,
            "deletion_timestamp": None,
            "namespace": "default",
            "node": "node-1",
            "labels": '{"app": "lb-app"}',
            "containers": [],
            "secret_volume_ids": [],
            "secret_env_ids": [],
        },
        {
            "uid": pod_ing_id,
            "name": f"pod-ing-{case_id}",
            "status_phase": "running",
            "creation_timestamp": 1633581666,
            "deletion_timestamp": None,
            "namespace": "default",
            "node": "node-1",
            "labels": '{"app": "ing-app"}',
            "containers": [],
            "secret_volume_ids": [],
            "secret_env_ids": [],
        },
    ]

    test_containers = [
        {
            "uid": cont_lb_id,
            "name": "web",
            "image": "example/web:latest",
            "namespace": "default",
            "pod_id": pod_lb_id,
            "image_pull_policy": "Always",
            "status_image_id": "img-1",
            "status_image_sha": "sha256:1",
            "status_ready": True,
            "status_started": True,
            "status_state": "running",
            "memory_request": "128Mi",
            "cpu_request": "100m",
            "memory_limit": "256Mi",
            "cpu_limit": "500m",
        },
        {
            "uid": cont_ing_id,
            "name": "api",
            "image": "example/api:latest",
            "namespace": "default",
            "pod_id": pod_ing_id,
            "image_pull_policy": "Always",
            "status_image_id": "img-2",
            "status_image_sha": "sha256:2",
            "status_ready": True,
            "status_started": True,
            "status_state": "running",
            "memory_request": "128Mi",
            "cpu_request": "100m",
            "memory_limit": "256Mi",
            "cpu_limit": "500m",
        },
    ]

    test_services = [
        {
            "uid": svc_lb_id,
            "name": f"my-lb-svc-{case_id}",
            "qualified_name": f"default/my-lb-svc-{case_id}",
            "creation_timestamp": 1633581666,
            "deletion_timestamp": None,
            "namespace": "default",
            "type": "LoadBalancer",
            "selector": '{"app":"lb-app"}',
            "cluster_ip": "10.0.0.10",
            "pod_ids": [pod_lb_id],
            "load_balancer_ip": None,
            "load_balancer_ingress": f'[{{"hostname":"{nlb_dns}"}}]',
            "load_balancer_dns_names": [nlb_dns],
            "gcp_neg_ids": [neg_int_id],
        },
        {
            "uid": svc_ing_id,
            "name": f"my-clusterip-svc-{case_id}",
            "qualified_name": f"default/my-clusterip-svc-{case_id}",
            "creation_timestamp": 1633581666,
            "deletion_timestamp": None,
            "namespace": "default",
            "type": "ClusterIP",
            "selector": '{"app":"ing-app"}',
            "cluster_ip": "10.0.0.20",
            "pod_ids": [pod_ing_id],
            "load_balancer_ip": None,
            "gcp_neg_ids": [neg_ext_id],
        },
    ]

    test_ingress = {
        "uid": f"ing-{case_id}",
        "name": f"my-ingress-{case_id}",
        "namespace": "default",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "annotations": "{}",
        "ingress_class_name": "alb",
        "rules": "[]",
        "default_backend": "{}",
        "target_services": [f"my-clusterip-svc-{case_id}"],
        "ingress_group_name": None,
        "load_balancer_dns_names": [alb_dns],
    }

    test_duplicate_ingress = {
        "uid": f"ing-dup-{case_id}",
        "name": f"my-ingress-dup-{case_id}",
        "namespace": "default",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "annotations": "{}",
        "ingress_class_name": "alb",
        "rules": "[]",
        "default_backend": "{}",
        "target_services": [f"my-clusterip-svc-{case_id}"],
        "ingress_group_name": None,
        "load_balancer_dns_names": [alb_dns],
    }

    test_lb_data = [
        {
            "LoadBalancerArn": f"arn:aws:elasticloadbalancing:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:loadbalancer/net/test-nlb/{case_id}",
            "DNSName": nlb_dns,
            "CanonicalHostedZoneId": "Z26RNL4JYFTOTI",
            "CreatedTime": datetime.datetime(2021, 1, 1, 12, 0, 0),
            "LoadBalancerName": f"test-nlb-{case_id}",
            "Scheme": "internet-facing",
            "VpcId": "vpc-12345678",
            "State": {"Code": "active"},
            "Type": "network",
            "AvailabilityZones": [
                {"ZoneName": "us-east-1a", "SubnetId": "subnet-11111111"}
            ],
            "Listeners": [
                {
                    "ListenerArn": f"arn:aws:elasticloadbalancing:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:listener/net/test-nlb/{case_id}/abcdef",
                    "LoadBalancerArn": f"arn:aws:elasticloadbalancing:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:loadbalancer/net/test-nlb/{case_id}",
                    "Port": 80,
                    "Protocol": "TCP",
                },
            ],
            "TargetGroups": [],
        },
        {
            "LoadBalancerArn": f"arn:aws:elasticloadbalancing:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:loadbalancer/app/test-alb/{case_id}",
            "DNSName": alb_dns,
            "CanonicalHostedZoneId": "Z35SXDOTRQ7X7K",
            "CreatedTime": datetime.datetime(2021, 1, 1, 12, 0, 0),
            "LoadBalancerName": f"test-alb-{case_id}",
            "Scheme": "internet-facing",
            "VpcId": "vpc-12345678",
            "State": {"Code": "active"},
            "Type": "application",
            "AvailabilityZones": [
                {"ZoneName": "us-east-1a", "SubnetId": "subnet-22222222"}
            ],
            "SecurityGroups": ["sg-12345678"],
            "Listeners": [
                {
                    "ListenerArn": f"arn:aws:elasticloadbalancing:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:listener/app/test-alb/{case_id}/abcdef",
                    "LoadBalancerArn": f"arn:aws:elasticloadbalancing:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:loadbalancer/app/test-alb/{case_id}",
                    "Port": 80,
                    "Protocol": "HTTP",
                },
            ],
            "TargetGroups": [
                {
                    "TargetGroupArn": alb_tg_arn,
                    "TargetGroupName": f"test-alb-tg-{case_id}",
                    "TargetType": "ip",
                    "Protocol": "HTTP",
                    "Port": 3000,
                    "VpcId": "vpc-12345678",
                    "Targets": [],
                },
            ],
        },
    ]

    test_other_cluster = [
        {
            "id": other_cluster_id,
            "name": other_cluster_name,
            "creation_timestamp": 1234567890,
            "external_id": other_cluster_id,
            "git_version": "v1.30.0",
            "version_major": 1,
            "version_minor": 30,
            "go_version": "go1.16.5",
            "compiler": "gc",
            "platform": "linux/amd64",
        },
    ]

    # Same namespace and name as the bound service, in another cluster.
    test_other_cluster_services = [
        {
            "uid": f"svc-clusterip-other-{case_id}",
            "name": f"my-clusterip-svc-{case_id}",
            "qualified_name": f"default/my-clusterip-svc-{case_id}",
            "creation_timestamp": 1633581666,
            "deletion_timestamp": None,
            "namespace": "default",
            "type": "ClusterIP",
            "selector": '{"app":"ing-app"}',
            "cluster_ip": "10.0.0.20",
            "pod_ids": [],
            "load_balancer_ip": None,
        },
    ]

    test_target_group_bindings = [
        {
            "apiVersion": "elbv2.k8s.aws/v1beta1",
            "kind": "TargetGroupBinding",
            "metadata": {"name": binding_name, "namespace": "default"},
            "spec": {
                "targetGroupARN": alb_tg_arn,
                "targetType": "ip",
                "serviceRef": {"name": f"my-clusterip-svc-{case_id}", "port": 80},
            },
        },
    ]

    test_gcp_negs = {
        "id": f"projects/{gcp_project_id}/aggregated/networkEndpointGroups",
        "items": {
            f"zones/{TEST_GCP_ZONE}": {
                "networkEndpointGroups": [
                    {"name": f"neg-ext-{case_id}"},
                    {"name": f"neg-int-{case_id}"},
                ],
            },
        },
    }

    test_gcp_backend_services = {
        "id": f"projects/{gcp_project_id}/global/backendServices",
        "items": [
            {
                "name": "ext-bs",
                "loadBalancingScheme": "EXTERNAL_MANAGED",
                "backends": [{"group": f"{COMPUTE_URL}/{neg_ext_id}"}],
            },
            {
                "name": "int-bs",
                "loadBalancingScheme": "INTERNAL_MANAGED",
                "backends": [{"group": f"{COMPUTE_URL}/{neg_int_id}"}],
            },
        ],
    }

    return {
        "update_tag": update_tag,
        "cluster_id": cluster_id,
        "cluster_name": cluster_name,
        "other_cluster_id": other_cluster_id,
        "other_cluster_name": other_cluster_name,
        "other_cluster": test_other_cluster,
        "other_cluster_services": test_other_cluster_services,
        "binding_name": binding_name,
        "aws_account_id": TEST_AWS_ACCOUNT_ID,
        "region": TEST_REGION,
        "nlb_dns": nlb_dns,
        "alb_dns": alb_dns,
        "alb_tg_arn": alb_tg_arn,
        "pod_lb_id": pod_lb_id,
        "pod_ing_id": pod_ing_id,
        "cont_lb_id": cont_lb_id,
        "cont_ing_id": cont_ing_id,
        "svc_lb_id": svc_lb_id,
        "svc_ing_id": svc_ing_id,
        "cluster": test_cluster,
        "namespaces": test_namespaces,
        "pods": test_pods,
        "containers": test_containers,
        "services": test_services,
        "ingress": test_ingress,
        "duplicate_ingress": test_duplicate_ingress,
        "lb_data": test_lb_data,
        "target_group_bindings": test_target_group_bindings,
        "gcp_project_id": gcp_project_id,
        "ext_bs_id": ext_bs_id,
        "gcp_negs": test_gcp_negs,
        "gcp_backend_services": test_gcp_backend_services,
    }


TEST_AKS_SUBSCRIPTION_ID = "00000000-0000-0000-0000-00000000a115"
TEST_OTHER_SUBSCRIPTION_ID = "00000000-0000-0000-0000-00000000b226"


def _azure_lb(subscription_id: str, resource_group: str, name: str, frontend: dict):
    lb_id = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.Network/loadBalancers/{name}"
    )
    return {
        "id": lb_id,
        "name": name,
        "location": "eastus",
        "sku": {"name": "Standard"},
        "frontend_ip_configurations": [
            {"id": f"{lb_id}/frontendIPConfigurations/fe", "name": "fe", **frontend}
        ],
    }


def _azure_public_ip(subscription_id: str, resource_group: str, name: str, ip: str):
    return {
        "id": (
            f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
            f"/providers/Microsoft.Network/publicIPAddresses/{name}"
        ),
        "name": name,
        "location": "eastus",
        "ip_address": ip,
    }


def build_aks_exposure_test_data() -> dict:
    """
    An AKS cluster whose LoadBalancer Services and AGIC Ingress are fronted by Azure
    load balancers and an Application Gateway, plus decoys that reuse the same
    addresses outside the cluster's subscription or node resource group.
    """
    case = build_exposure_test_data()
    case_id = case["cluster_name"].rsplit("-", 1)[-1]
    node_rg = f"MC_rg-aks_aks-{case_id}_eastus"
    public_ip = "20.42.0.10"
    agic_ip = "20.42.0.11"
    internal_ip = "10.224.0.50"

    sub, other_sub = TEST_AKS_SUBSCRIPTION_ID, TEST_OTHER_SUBSCRIPTION_ID
    lb_pip = _azure_public_ip(sub, node_rg, f"kubernetes-{case_id}", public_ip)
    agic_pip = _azure_public_ip(sub, "rg-ingress", f"appgw-pip-{case_id}", agic_ip)
    decoy_pip = _azure_public_ip(other_sub, "rg-other", f"reused-{case_id}", public_ip)

    public_lb = _azure_lb(
        sub, node_rg, "kubernetes", {"public_ip_address": {"id": lb_pip["id"]}}
    )
    internal_lb = _azure_lb(
        sub, node_rg, "kubernetes-internal", {"private_ip_address": internal_ip}
    )
    decoy_public_lb = _azure_lb(
        other_sub, "rg-other", "reused", {"public_ip_address": {"id": decoy_pip["id"]}}
    )
    decoy_internal_lb = _azure_lb(
        sub, "rg-other-vnet", "internal", {"private_ip_address": internal_ip}
    )

    appgw_id = (
        f"/subscriptions/{sub}/resourceGroups/rg-ingress"
        f"/providers/Microsoft.Network/applicationGateways/agic-{case_id}"
    )
    appgw = {
        "id": appgw_id,
        "name": f"agic-{case_id}",
        "location": "eastus",
        "sku": {"name": "Standard_v2", "tier": "Standard_v2"},
        "frontend_ip_configurations": [
            {
                "id": f"{appgw_id}/frontendIPConfigurations/public",
                "name": "public",
                "public_ip_address": {"id": agic_pip["id"]},
            },
        ],
    }

    svc_internal_id = f"svc-internal-{case_id}"
    services = copy.deepcopy(case["services"])
    services[0].update(
        load_balancer_ips=[public_ip],
        load_balancer_ingress=f'[{{"ip":"{public_ip}"}}]',
        load_balancer_dns_names=[],
    )
    services.append(
        {
            **services[0],
            "uid": svc_internal_id,
            "name": f"my-internal-svc-{case_id}",
            "load_balancer_ips": [internal_ip],
            "load_balancer_ingress": f'[{{"ip":"{internal_ip}"}}]',
        },
    )
    ingress = {
        **case["ingress"],
        "ingress_class_name": "azure-application-gateway",
        "load_balancer_ips": [agic_ip],
        "load_balancer_dns_names": [],
    }

    return {
        **case,
        "subscription_id": sub,
        "other_subscription_id": other_sub,
        "node_provider_id": (
            f"azure:///subscriptions/{sub}/resourceGroups/{node_rg}/providers"
            "/Microsoft.Compute/virtualMachineScaleSets/aks-nodepool1-vmss"
            "/virtualMachines/0"
        ),
        "public_ips": {sub: [lb_pip, agic_pip], other_sub: [decoy_pip]},
        "load_balancers": {
            sub: [public_lb, internal_lb, decoy_internal_lb],
            other_sub: [decoy_public_lb],
        },
        "application_gateway": appgw,
        "public_lb_id": public_lb["id"],
        "internal_lb_id": internal_lb["id"],
        "appgw_id": appgw_id,
        "svc_internal_id": svc_internal_id,
        "services": services,
        "ingress": ingress,
    }
