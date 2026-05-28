from kubernetes.client.models import V1Ingress
from kubernetes.client.models import V1IngressLoadBalancerIngress
from kubernetes.client.models import V1IngressLoadBalancerStatus
from kubernetes.client.models import V1IngressSpec
from kubernetes.client.models import V1IngressStatus
from kubernetes.client.models import V1ObjectMeta

from cartography.intel.kubernetes.ingress import transform_ingresses


def test_transform_ingresses_extracts_tailscale_load_balancer_dns_names():
    ingress = V1Ingress(
        metadata=V1ObjectMeta(
            uid="ingress-1",
            name="demo-app",
            namespace="demo-app",
            creation_timestamp=None,
            deletion_timestamp=None,
            annotations={"tailscale.com/hostname": "demo-app-cluster-a"},
        ),
        spec=V1IngressSpec(ingress_class_name="tailscale", rules=[]),
        status=V1IngressStatus(
            load_balancer=V1IngressLoadBalancerStatus(
                ingress=[
                    V1IngressLoadBalancerIngress(
                        hostname="Demo-App-Cluster-A.tailabc123.ts.net.",
                    ),
                    V1IngressLoadBalancerIngress(hostname="lb.example.com"),
                    V1IngressLoadBalancerIngress(ip="192.0.2.10"),
                ],
            ),
        ),
    )

    [transformed] = transform_ingresses([ingress])

    assert transformed["load_balancer_dns_names"] == [
        "Demo-App-Cluster-A.tailabc123.ts.net.",
        "lb.example.com",
    ]
    assert transformed["tailscale_device_dns_names"] == [
        "demo-app-cluster-a.tailabc123.ts.net",
    ]
