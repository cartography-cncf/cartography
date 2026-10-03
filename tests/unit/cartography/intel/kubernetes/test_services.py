import json

from kubernetes.client.models import V1LoadBalancerIngress
from kubernetes.client.models import V1LoadBalancerStatus
from kubernetes.client.models import V1ObjectMeta
from kubernetes.client.models import V1PortStatus
from kubernetes.client.models import V1Service
from kubernetes.client.models import V1ServiceSpec
from kubernetes.client.models import V1ServiceStatus

from cartography.intel.kubernetes.services import transform_services


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
                        ip="8.8.8.8",
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
            "ip": "8.8.8.8",
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
    assert transformed["load_balancer_ip_addresses"] == ["8.8.8.8"]


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


def test_transform_services_prefers_endpoint_slice_backends():
    service = V1Service(
        metadata=V1ObjectMeta(
            uid="service-3",
            name="selectorless",
            namespace="default",
        ),
        spec=V1ServiceSpec(
            type="ClusterIP",
            selector={"app": "selectorless"},
            cluster_ip="10.0.0.3",
            ports=[],
        ),
        status=V1ServiceStatus(),
    )

    [transformed] = transform_services(
        [service],
        all_pods=[],
        endpoint_slice_pod_ids={"default/selectorless": ["pod-uid"]},
    )

    assert transformed["pod_ids"] == ["pod-uid"]

    [without_ready_backends] = transform_services(
        [service],
        all_pods=[
            {
                "namespace": "default",
                "labels": json.dumps({"app": "selectorless"}),
                "uid": "selector-match",
            }
        ],
        endpoint_slice_pod_ids={},
    )

    assert without_ready_backends["pod_ids"] == []
