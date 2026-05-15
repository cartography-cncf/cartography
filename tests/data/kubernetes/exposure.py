import datetime
from uuid import uuid4

TEST_AWS_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"


def build_exposure_test_data() -> dict:
    case_id = uuid4().hex[:8]
    update_tag = 123456789

    cluster_id = f"arn:aws:eks:{TEST_REGION}:{TEST_AWS_ACCOUNT_ID}:cluster/test-cluster-{case_id}"
    cluster_name = f"test-cluster-{case_id}"

    pod_lb_id = f"pod-lb-{case_id}"
    pod_ing_id = f"pod-ing-{case_id}"
    cont_lb_id = f"cont-lb-{case_id}"
    cont_ing_id = f"cont-ing-{case_id}"

    svc_lb_id = f"svc-lb-{case_id}"
    svc_ing_id = f"svc-clusterip-{case_id}"

    nlb_dns = f"nlb-{case_id}.elb.{TEST_REGION}.amazonaws.com"
    alb_dns = f"alb-{case_id}.elb.{TEST_REGION}.amazonaws.com"

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
        },
        {
            "uid": svc_ing_id,
            "name": f"my-clusterip-svc-{case_id}",
            "creation_timestamp": 1633581666,
            "deletion_timestamp": None,
            "namespace": "default",
            "type": "ClusterIP",
            "selector": '{"app":"ing-app"}',
            "cluster_ip": "10.0.0.20",
            "pod_ids": [pod_ing_id],
            "load_balancer_ip": None,
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
            "TargetGroups": [],
        },
    ]

    return {
        "update_tag": update_tag,
        "cluster_id": cluster_id,
        "cluster_name": cluster_name,
        "aws_account_id": TEST_AWS_ACCOUNT_ID,
        "region": TEST_REGION,
        "nlb_dns": nlb_dns,
        "alb_dns": alb_dns,
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
    }
