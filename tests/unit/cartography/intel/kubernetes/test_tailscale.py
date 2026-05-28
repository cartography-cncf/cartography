import json

from cartography.intel.kubernetes.tailscale import build_endpoint_candidates


def test_build_endpoint_candidates_normalizes_and_filters_ts_net_hosts():
    rows = [
        {
            "resource_type": "ingress",
            "resource_id": "ingress-1",
            "host_names": ["NODE.tailxxxx.ts.net.", "public.example.com"],
            "load_balancer_dns_names": ["app.tailxxxx.ts.net"],
            "load_balancer_ingress": None,
        },
        {
            "resource_type": "service",
            "resource_id": "service-1",
            "host_names": [],
            "load_balancer_dns_names": ["node.tailxxxx.ts.net"],
            "load_balancer_ingress": json.dumps(
                [
                    {"hostname": "app.tailxxxx.ts.net"},
                    {"ip": "100.64.0.1"},
                ],
            ),
        },
    ]

    assert build_endpoint_candidates(rows) == [
        {
            "resource_type": "ingress",
            "resource_id": "ingress-1",
            "host": "node.tailxxxx.ts.net",
            "short_name": "node",
            "tailnet_suffix": "tailxxxx.ts.net",
            "source_field": "ingress.host_names",
        },
        {
            "resource_type": "ingress",
            "resource_id": "ingress-1",
            "host": "app.tailxxxx.ts.net",
            "short_name": "app",
            "tailnet_suffix": "tailxxxx.ts.net",
            "source_field": "ingress.load_balancer_dns_names",
        },
        {
            "resource_type": "service",
            "resource_id": "service-1",
            "host": "node.tailxxxx.ts.net",
            "short_name": "node",
            "tailnet_suffix": "tailxxxx.ts.net",
            "source_field": "service.load_balancer_dns_names",
        },
        {
            "resource_type": "service",
            "resource_id": "service-1",
            "host": "app.tailxxxx.ts.net",
            "short_name": "app",
            "tailnet_suffix": "tailxxxx.ts.net",
            "source_field": "service.load_balancer_ingress.hostname",
        },
    ]


def test_build_endpoint_candidates_deduplicates_per_resource_and_hostname():
    rows = [
        {
            "resource_type": "service",
            "resource_id": "service-1",
            "host_names": [],
            "load_balancer_dns_names": ["app.tailxxxx.ts.net"],
            "load_balancer_ingress": json.dumps(
                [{"hostname": "app.tailxxxx.ts.net"}],
            ),
        },
    ]

    assert build_endpoint_candidates(rows) == [
        {
            "resource_type": "service",
            "resource_id": "service-1",
            "host": "app.tailxxxx.ts.net",
            "short_name": "app",
            "tailnet_suffix": "tailxxxx.ts.net",
            "source_field": "service.load_balancer_dns_names",
        },
    ]
