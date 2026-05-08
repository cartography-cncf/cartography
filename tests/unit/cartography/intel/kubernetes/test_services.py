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
