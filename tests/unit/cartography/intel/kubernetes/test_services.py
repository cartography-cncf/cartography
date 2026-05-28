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
    assert transformed["tailscale_device_dns_names"] == []


def test_transform_services_extracts_tailscale_load_balancer_dns_names():
    service = V1Service(
        metadata=V1ObjectMeta(
            uid="service-2",
            name="private-gateway",
            namespace="gateway-system",
            creation_timestamp=None,
            deletion_timestamp=None,
        ),
        spec=V1ServiceSpec(
            type="LoadBalancer",
            selector={"app": "gateway"},
            cluster_ip="10.0.0.2",
            load_balancer_ip=None,
        ),
        status=V1ServiceStatus(
            load_balancer=V1LoadBalancerStatus(
                ingress=[
                    V1LoadBalancerIngress(
                        hostname="Private-Gateway.tailabc123.ts.net."
                    ),
                    V1LoadBalancerIngress(hostname="lb.example.com"),
                    V1LoadBalancerIngress(ip="192.0.2.10"),
                ],
            ),
        ),
    )

    [transformed] = transform_services([service], all_pods=[])

    assert transformed["load_balancer_dns_names"] == [
        "Private-Gateway.tailabc123.ts.net.",
        "lb.example.com",
    ]
    assert transformed["tailscale_device_dns_names"] == [
        "private-gateway.tailabc123.ts.net",
    ]
