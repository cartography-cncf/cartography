import json

import pytest
from kubernetes.client.models import V1LoadBalancerIngress
from kubernetes.client.models import V1LoadBalancerStatus
from kubernetes.client.models import V1ObjectMeta
from kubernetes.client.models import V1PortStatus
from kubernetes.client.models import V1Service
from kubernetes.client.models import V1ServiceSpec
from kubernetes.client.models import V1ServiceStatus

from cartography.intel.kubernetes.services import transform_services
from cartography.intel.kubernetes.util import GKENetworkScope


def test_transform_services_formats_load_balancer_port_status():
    service = V1Service(
        metadata=V1ObjectMeta(
            uid="service-1",
            name="web",
            namespace="default",
            creation_timestamp=None,
            deletion_timestamp=None,
        ),
        spec=V1ServiceSpec(
            type="LoadBalancer",
            selector={"app": "web"},
            cluster_ip="10.0.0.1",
            load_balancer_ip=None,
        ),
        status=V1ServiceStatus(
            load_balancer=V1LoadBalancerStatus(
                ingress=[
                    V1LoadBalancerIngress(
                        hostname="lb.example.com",
                        ports=[
                            V1PortStatus(
                                error="PortAllocationFailed",
                                port=443,
                                protocol="TCP",
                            ),
                        ],
                    ),
                ],
            ),
        ),
    )

    [transformed] = transform_services([service], all_pods=[])

    assert json.loads(transformed["load_balancer_ingress"]) == [
        {
            "hostname": "lb.example.com",
            "ip": None,
            "ip_mode": None,
            "ports": [
                {
                    "error": "PortAllocationFailed",
                    "port": 443,
                    "protocol": "TCP",
                },
            ],
        },
    ]
    assert transformed["load_balancer_dns_names"] == ["lb.example.com"]


def test_transform_services_lowercases_load_balancer_dns_names():
    service = V1Service(
        metadata=V1ObjectMeta(
            uid="service-2",
            name="api",
            namespace="default",
            creation_timestamp=None,
            deletion_timestamp=None,
        ),
        spec=V1ServiceSpec(
            type="LoadBalancer",
            selector={"app": "api"},
            cluster_ip="10.0.0.2",
            load_balancer_ip=None,
        ),
        status=V1ServiceStatus(
            load_balancer=V1LoadBalancerStatus(
                ingress=[
                    # The AWS Load Balancer Controller copies the ELB DNSName verbatim,
                    # which preserves the load balancer name's case.
                    V1LoadBalancerIngress(
                        hostname="My-NLB-1234567890.us-east-1.elb.amazonaws.com",
                    ),
                ],
            ),
        ),
    )

    [transformed] = transform_services([service], all_pods=[])

    assert transformed["load_balancer_dns_names"] == [
        "my-nlb-1234567890.us-east-1.elb.amazonaws.com"
    ]


def test_transform_services_needs_gke_metadata_for_neg_ids():
    service = V1Service(
        metadata=V1ObjectMeta(
            uid="service-3",
            name="neg",
            namespace="default",
            annotations={
                "cloud.google.com/neg-status": '{"network_endpoint_groups": {"80": "neg"}, "zones": ["us-central1-a"]}'
            },
        ),
        spec=V1ServiceSpec(type="ClusterIP", selector={"app": "neg"}),
    )

    [transformed] = transform_services([service], all_pods=[], gke_scope=None)

    assert transformed["gcp_neg_ids"] == []


def test_transform_services_fails_on_unparseable_neg_status():
    service = V1Service(
        metadata=V1ObjectMeta(
            uid="service-4",
            name="neg",
            namespace="default",
            annotations={"cloud.google.com/neg-status": "{not json"},
        ),
        spec=V1ServiceSpec(type="ClusterIP", selector={"app": "neg"}),
    )

    with pytest.raises(json.JSONDecodeError):
        transform_services(
            [service],
            all_pods=[],
            gke_scope=GKENetworkScope("example-project", None),
        )
