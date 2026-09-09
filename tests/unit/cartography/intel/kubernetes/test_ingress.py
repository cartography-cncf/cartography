from kubernetes.client.models import V1Ingress
from kubernetes.client.models import V1IngressLoadBalancerIngress
from kubernetes.client.models import V1IngressLoadBalancerStatus
from kubernetes.client.models import V1IngressRule
from kubernetes.client.models import V1IngressSpec
from kubernetes.client.models import V1IngressStatus
from kubernetes.client.models import V1ObjectMeta

from cartography.intel.kubernetes.ingress import transform_ingresses


def test_transform_ingresses_lowercases_load_balancer_dns_names():
    ingress = V1Ingress(
        metadata=V1ObjectMeta(
            uid="ingress-1",
            name="web",
            namespace="default",
            creation_timestamp=None,
            deletion_timestamp=None,
            annotations={},
        ),
        spec=V1IngressSpec(rules=[], default_backend=None),
        status=V1IngressStatus(
            load_balancer=V1IngressLoadBalancerStatus(
                ingress=[
                    # The AWS Load Balancer Controller copies the ELB DNSName verbatim,
                    # which preserves the load balancer name's case.
                    V1IngressLoadBalancerIngress(
                        hostname="My-ALB-1234567890.us-east-1.elb.amazonaws.com",
                    ),
                ],
            ),
        ),
    )

    [transformed] = transform_ingresses([ingress])

    assert transformed["load_balancer_dns_names"] == [
        "my-alb-1234567890.us-east-1.elb.amazonaws.com"
    ]


def test_transform_ingresses_normalizes_rule_hostnames():
    ingress = V1Ingress(
        metadata=V1ObjectMeta(
            uid="ingress-1",
            name="web",
            namespace="default",
            annotations={},
        ),
        spec=V1IngressSpec(
            rules=[V1IngressRule(host=" App.Example.COM. ")],
            default_backend=None,
        ),
        status=V1IngressStatus(load_balancer=None),
    )

    [transformed] = transform_ingresses([ingress])

    assert transformed["host_names"] == [" App.Example.COM. "]
    assert transformed["host_names_normalized"] == ["app.example.com"]
