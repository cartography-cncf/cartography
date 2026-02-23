import datetime

TEST_CLUSTER_ID = "arn:aws:eks:us-east-1:000000000000:cluster/test-cluster"
TEST_CLUSTER_NAME = "test-cluster"
TEST_AWS_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

TEST_CLUSTER = [
    {
        "id": TEST_CLUSTER_ID,
        "name": TEST_CLUSTER_NAME,
        "creation_timestamp": 1234567890,
        "external_id": TEST_CLUSTER_ID,
        "git_version": "v1.30.0",
        "version_major": 1,
        "version_minor": 30,
        "go_version": "go1.16.5",
        "compiler": "gc",
        "platform": "linux/amd64",
    },
]

TEST_NAMESPACES = [
    {
        "uid": "default-ns-uid",
        "name": "default",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "status_phase": "Active",
    },
]

TEST_PODS = [
    {
        "uid": "pod-lb-uid",
        "name": "pod-lb",
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
        "uid": "pod-ing-uid",
        "name": "pod-ing",
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

TEST_CONTAINERS = [
    {
        "uid": "cont-lb-uid",
        "name": "web",
        "image": "example/web:latest",
        "namespace": "default",
        "pod_id": "pod-lb-uid",
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
        "uid": "cont-ing-uid",
        "name": "api",
        "image": "example/api:latest",
        "namespace": "default",
        "pod_id": "pod-ing-uid",
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

TEST_SERVICES = [
    {
        "uid": "svc-lb-uid",
        "name": "my-lb-svc",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": "default",
        "type": "LoadBalancer",
        "selector": '{"app":"lb-app"}',
        "cluster_ip": "10.0.0.10",
        "pod_ids": ["pod-lb-uid"],
        "load_balancer_ip": None,
        "load_balancer_ingress": '[{"hostname":"nlb-dns.elb.amazonaws.com"}]',
        "load_balancer_dns_names": ["nlb-dns.elb.amazonaws.com"],
    },
    {
        "uid": "svc-clusterip-uid",
        "name": "my-clusterip-svc",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": "default",
        "type": "ClusterIP",
        "selector": '{"app":"ing-app"}',
        "cluster_ip": "10.0.0.20",
        "pod_ids": ["pod-ing-uid"],
        "load_balancer_ip": None,
    },
]

TEST_INGRESS = {
    "uid": "ing-uid",
    "name": "my-ingress",
    "namespace": "default",
    "creation_timestamp": 1633581666,
    "deletion_timestamp": None,
    "annotations": "{}",
    "ingress_class_name": "alb",
    "rules": "[]",
    "default_backend": "{}",
    "target_services": ["my-clusterip-svc"],
    "ingress_group_name": None,
    "load_balancer_dns_names": ["alb-dns.elb.amazonaws.com"],
}

TEST_DUPLICATE_INGRESS = {
    "uid": "ing-uid-2",
    "name": "my-ingress-2",
    "namespace": "default",
    "creation_timestamp": 1633581666,
    "deletion_timestamp": None,
    "annotations": "{}",
    "ingress_class_name": "alb",
    "rules": "[]",
    "default_backend": "{}",
    "target_services": ["my-clusterip-svc"],
    "ingress_group_name": None,
    "load_balancer_dns_names": ["alb-dns.elb.amazonaws.com"],
}

TEST_LB_DATA = [
    {
        "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/net/test-nlb/1234567890",
        "DNSName": "nlb-dns.elb.amazonaws.com",
        "CanonicalHostedZoneId": "Z26RNL4JYFTOTI",
        "CreatedTime": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "LoadBalancerName": "test-nlb",
        "Scheme": "internet-facing",
        "VpcId": "vpc-12345678",
        "State": {"Code": "active"},
        "Type": "network",
        "AvailabilityZones": [
            {
                "ZoneName": "us-east-1a",
                "SubnetId": "subnet-11111111",
            },
        ],
        "Listeners": [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/net/test-nlb/1234567890/abcdef",
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/net/test-nlb/1234567890",
                "Port": 80,
                "Protocol": "TCP",
            },
        ],
        "TargetGroups": [],
    },
    {
        "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/test-alb/1234567890",
        "DNSName": "alb-dns.elb.amazonaws.com",
        "CanonicalHostedZoneId": "Z35SXDOTRQ7X7K",
        "CreatedTime": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "LoadBalancerName": "test-alb",
        "Scheme": "internet-facing",
        "VpcId": "vpc-12345678",
        "State": {"Code": "active"},
        "Type": "application",
        "AvailabilityZones": [
            {
                "ZoneName": "us-east-1a",
                "SubnetId": "subnet-22222222",
            },
        ],
        "SecurityGroups": ["sg-12345678"],
        "Listeners": [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-alb/1234567890/abcdef",
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/test-alb/1234567890",
                "Port": 80,
                "Protocol": "HTTP",
            },
        ],
        "TargetGroups": [],
    },
]
