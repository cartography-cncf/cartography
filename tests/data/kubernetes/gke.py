from kubernetes.client import V1LoadBalancerIngress
from kubernetes.client import V1LoadBalancerStatus
from kubernetes.client import V1Node
from kubernetes.client import V1NodeSpec
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1Service
from kubernetes.client import V1ServiceAccount
from kubernetes.client import V1ServicePort
from kubernetes.client import V1ServiceSpec
from kubernetes.client import V1ServiceStatus

GKE_PROJECT_ID = "example-project"
GKE_PROJECT_NUMBER = "111122223333"
GKE_OTHER_PROJECT_ID = "other-project"
GKE_LOCATION = "us-central1"
GKE_CLUSTER_NAME = "gke_example-project_us-central1_example"
GKE_CLUSTER_ID = "gke-kube-system-uid"
GKE_RESOURCE_NAME = (
    f"projects/{GKE_PROJECT_ID}/locations/{GKE_LOCATION}/clusters/example"
)
GKE_SELF_LINK = f"https://container.googleapis.com/v1/{GKE_RESOURCE_NAME}"
GKE_WORKLOAD_POOL = f"{GKE_PROJECT_ID}.svc.id.goog"
GKE_POOL_ID = (
    f"projects/{GKE_PROJECT_NUMBER}/locations/global/"
    f"workloadIdentityPools/{GKE_WORKLOAD_POOL}"
)
GKE_GSA_EMAIL = f"workload@{GKE_PROJECT_ID}.iam.gserviceaccount.com"
GKE_LB_IP = "10.0.0.2"
GKE_PUBLIC_LB_IP = "34.120.0.10"
GKE_NETWORK = f"projects/{GKE_PROJECT_ID}/global/networks/default"
GKE_OTHER_NETWORK = f"projects/{GKE_PROJECT_ID}/global/networks/other"

GKE_CLUSTER = {
    "name": "example",
    "selfLink": GKE_SELF_LINK,
    "location": GKE_LOCATION,
    "networkConfig": {"network": GKE_NETWORK},
    "workloadIdentityConfig": {"workloadPool": GKE_WORKLOAD_POOL},
    "nodePools": [
        {
            "name": "pool",
            "config": {
                "serviceAccount": GKE_GSA_EMAIL,
                "workloadMetadataConfig": {"mode": "GKE_METADATA"},
            },
        },
    ],
}

GKE_WORKLOAD_POOLS = [{"name": GKE_POOL_ID, "state": "ACTIVE"}]

GKE_GCP_SERVICE_ACCOUNTS = [{"uniqueId": "1001", "email": GKE_GSA_EMAIL}]

# The private address is reused in another project and in another VPC of the same
# project; only the rule in the cluster's own project and network matches.
GKE_FORWARDING_RULES = {
    GKE_PROJECT_ID: {
        "id": f"projects/{GKE_PROJECT_ID}/regions/{GKE_LOCATION}/forwardingRules",
        "items": [
            {
                "name": "gke-ilb",
                "IPAddress": GKE_LB_IP,
                "IPProtocol": "TCP",
                "loadBalancingScheme": "INTERNAL",
                "ports": ["443"],
                "network": f"https://www.googleapis.com/compute/v1/{GKE_NETWORK}",
            },
            {
                "name": "other-vpc-ilb",
                "IPAddress": GKE_LB_IP,
                "IPProtocol": "TCP",
                "loadBalancingScheme": "INTERNAL",
                "ports": ["443"],
                "network": f"https://www.googleapis.com/compute/v1/{GKE_OTHER_NETWORK}",
            },
            {
                "name": "gke-external-lb",
                "IPAddress": GKE_PUBLIC_LB_IP,
                "IPProtocol": "TCP",
                "loadBalancingScheme": "EXTERNAL",
                "portRange": "80-80",
            },
        ],
    },
    GKE_OTHER_PROJECT_ID: {
        "id": f"projects/{GKE_OTHER_PROJECT_ID}/regions/{GKE_LOCATION}/forwardingRules",
        "items": [
            {
                "name": "other-ilb",
                "IPAddress": GKE_LB_IP,
                "IPProtocol": "TCP",
                "loadBalancingScheme": "INTERNAL",
                "ports": ["443"],
                "network": f"https://www.googleapis.com/compute/v1/projects/{GKE_OTHER_PROJECT_ID}/global/networks/default",
            },
        ],
    },
}


def gke_policy_results(include_impersonation: bool = True) -> dict:
    sa_resource = f"//iam.googleapis.com/projects/{GKE_PROJECT_ID}/serviceAccounts/{GKE_GSA_EMAIL}"
    bindings = [
        # Direct WIF access by namespace/name subject.
        {
            "role": "roles/storage.objectViewer",
            "members": [
                f"principal://iam.googleapis.com/{GKE_POOL_ID}/subject/ns/ns/sa/direct",
            ],
        },
        # Conditional impersonation grant: retained as policy evidence only.
        {
            "role": "roles/iam.workloadIdentityUser",
            "members": [f"serviceAccount:{GKE_WORKLOAD_POOL}[ns/conditional]"],
            "condition": {"title": "never", "expression": "false"},
        },
    ]
    if include_impersonation:
        bindings.append(
            {
                "role": "roles/iam.workloadIdentityUser",
                "members": [f"serviceAccount:{GKE_WORKLOAD_POOL}[ns/linked]"],
            },
        )
    return {
        "project_id": GKE_PROJECT_ID,
        "policy_results": [
            {
                "policies": [
                    {
                        "attached_resource": sa_resource,
                        "policy": {"bindings": bindings},
                    },
                ],
            },
        ],
    }


def _service_account(name: str, annotated: bool) -> V1ServiceAccount:
    annotations = (
        {"iam.gke.io/gcp-service-account": GKE_GSA_EMAIL} if annotated else None
    )
    return V1ServiceAccount(
        metadata=V1ObjectMeta(
            name=name,
            namespace="ns",
            uid=f"{name}-uid",
            annotations=annotations,
        ),
    )


# `direct` has a direct WIF grant; `linked` is annotated and granted impersonation;
# `conditional` is annotated with only a conditional grant; `annotation-only` has no grant.
GKE_SERVICE_ACCOUNTS = [
    _service_account("direct", annotated=False),
    _service_account("linked", annotated=True),
    _service_account("conditional", annotated=True),
    _service_account("annotation-only", annotated=True),
]

GKE_NODES = [
    V1Node(
        metadata=V1ObjectMeta(
            name="node",
            labels={"cloud.google.com/gke-nodepool": "pool"},
        ),
        spec=V1NodeSpec(provider_id=f"gce://{GKE_PROJECT_ID}/us-central1-a/node"),
    ),
]

GKE_SERVICES = [
    V1Service(
        metadata=V1ObjectMeta(name="ilb", namespace="ns", uid="ilb-uid"),
        spec=V1ServiceSpec(
            type="LoadBalancer",
            ports=[V1ServicePort(port=443, protocol="TCP")],
        ),
        status=V1ServiceStatus(
            load_balancer=V1LoadBalancerStatus(
                ingress=[V1LoadBalancerIngress(ip=GKE_LB_IP)],
            ),
        ),
    ),
    V1Service(
        metadata=V1ObjectMeta(name="public", namespace="ns", uid="public-uid"),
        spec=V1ServiceSpec(
            type="LoadBalancer",
            ports=[V1ServicePort(port=80, protocol="TCP")],
        ),
        status=V1ServiceStatus(
            load_balancer=V1LoadBalancerStatus(
                ingress=[V1LoadBalancerIngress(ip=GKE_PUBLIC_LB_IP)],
            ),
        ),
    ),
]
