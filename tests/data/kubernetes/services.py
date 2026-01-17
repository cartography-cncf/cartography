import json
from uuid import uuid4

from tests.data.aws.ec2.load_balancers import LOAD_BALANCER_DATA
from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA

# DNS name from the AWS LoadBalancerV2 test data for cross-module relationship testing
AWS_TEST_LB_DNS_NAME = LOAD_BALANCER_DATA[0]["DNSName"]

# Additional DNS names for testing one-to-many relationships (e.g., frontend NLB + ALB)
AWS_TEST_LB_DNS_NAME_2 = "second-lb.elb.us-east-1.amazonaws.com"

KUBERNETES_SERVICES_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-service",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": 1633581966,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "ClusterIP",
        "selector": json.dumps({"app": "my-app"}),
        "cluster_ip": "1.1.1.1",
        "pod_ids": [
            KUBERNETES_PODS_DATA[0]["uid"],
        ],
        "load_balancer_ip": "1.1.1.1",
    },
]

# Test data for LoadBalancer type service with AWS NLB/ALB
# Uses DNS name from AWS LoadBalancerV2 test data so the relationship test
# stays in sync if the AWS LB test data changes.
KUBERNETES_LOADBALANCER_SERVICE_DATA = [
    {
        "uid": uuid4().hex,
        "name": "my-lb-service",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "LoadBalancer",
        "selector": json.dumps({"app": "my-app"}),
        "cluster_ip": "10.0.0.1",
        "pod_ids": [
            KUBERNETES_PODS_DATA[0]["uid"],
        ],
        "load_balancer_ip": None,
        "load_balancer_ingress": json.dumps(
            [
                {
                    "hostname": AWS_TEST_LB_DNS_NAME,
                    "ip": None,
                    "ip_mode": None,
                    "ports": None,
                },
            ]
        ),
        # DNS names extracted for relationship matching
        "load_balancer_dns_names": [
            AWS_TEST_LB_DNS_NAME,
        ],
    },
]

# Test data for LoadBalancer service with MULTIPLE DNS names (one-to-many scenario)
# Real-world case: AWS frontend NLB feature where service gets both NLB and ALB DNS
KUBERNETES_MULTI_LB_SERVICE_DATA = [
    {
        "uid": uuid4().hex,
        "name": "multi-lb-service",
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "namespace": KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"],
        "type": "LoadBalancer",
        "selector": json.dumps({"app": "multi-lb-app"}),
        "cluster_ip": "10.0.0.2",
        "pod_ids": [],
        "load_balancer_ip": None,
        "load_balancer_ingress": json.dumps(
            [
                {
                    "hostname": AWS_TEST_LB_DNS_NAME,
                    "ip": None,
                    "ip_mode": None,
                    "ports": None,
                },
                {
                    "hostname": AWS_TEST_LB_DNS_NAME_2,
                    "ip": None,
                    "ip_mode": None,
                    "ports": None,
                },
            ]
        ),
        "load_balancer_dns_names": [
            AWS_TEST_LB_DNS_NAME,
            AWS_TEST_LB_DNS_NAME_2,
        ],
    },
]
