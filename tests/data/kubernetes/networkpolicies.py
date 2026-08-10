import json
from uuid import uuid4

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA

_NAMESPACE = KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"]

# Three policies exercising the transition-relevant shapes:
# - a default-deny ingress policy (empty podSelector => selects every pod in the ns)
# - a label-scoped ingress policy (selects only the first pod)
# - an egress policy (selects only the second pod)
KUBERNETES_NETWORK_POLICIES_DATA = [
    {
        "uid": uuid4().hex,
        "name": "default-deny-ingress",
        "namespace": _NAMESPACE,
        "creation_timestamp": 1633581666,
        "deletion_timestamp": None,
        "pod_selector": json.dumps({"match_labels": None, "match_expressions": None}),
        "policy_types": ["Ingress"],
        "ingress_rules": json.dumps([]),
        "egress_rules": json.dumps([]),
        "restricts_ingress": True,
        "restricts_egress": False,
        # Empty selector => all pods in the namespace.
        "pod_ids": [
            KUBERNETES_PODS_DATA[0]["uid"],
            KUBERNETES_PODS_DATA[1]["uid"],
        ],
    },
    {
        "uid": uuid4().hex,
        "name": "allow-web-ingress",
        "namespace": _NAMESPACE,
        "creation_timestamp": 1633581667,
        "deletion_timestamp": None,
        "pod_selector": json.dumps(
            {"match_labels": {"key1": "val1"}, "match_expressions": None}
        ),
        "policy_types": ["Ingress"],
        "ingress_rules": json.dumps(
            [
                {
                    "from": [
                        {
                            "ip_block": None,
                            "namespace_selector": None,
                            "pod_selector": {
                                "match_labels": {"key1": "val3"},
                                "match_expressions": None,
                            },
                        }
                    ],
                    "ports": [{"port": 8080, "protocol": "TCP", "end_port": None}],
                }
            ]
        ),
        "egress_rules": json.dumps([]),
        "restricts_ingress": True,
        "restricts_egress": False,
        "pod_ids": [
            KUBERNETES_PODS_DATA[0]["uid"],
        ],
    },
    {
        "uid": uuid4().hex,
        "name": "restrict-egress",
        "namespace": _NAMESPACE,
        "creation_timestamp": 1633581668,
        "deletion_timestamp": None,
        "pod_selector": json.dumps(
            {"match_labels": {"key1": "val3"}, "match_expressions": None}
        ),
        "policy_types": ["Egress"],
        "ingress_rules": json.dumps([]),
        "egress_rules": json.dumps(
            [
                {
                    "to": [
                        {
                            "ip_block": {"cidr": "10.0.0.0/24", "except": None},
                            "namespace_selector": None,
                            "pod_selector": None,
                        }
                    ],
                    "ports": None,
                }
            ]
        ),
        "restricts_ingress": False,
        "restricts_egress": True,
        "pod_ids": [
            KUBERNETES_PODS_DATA[1]["uid"],
        ],
    },
]
