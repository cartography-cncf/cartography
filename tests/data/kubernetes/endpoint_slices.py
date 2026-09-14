from datetime import datetime
from datetime import timezone

from kubernetes.client import DiscoveryV1EndpointPort
from kubernetes.client import V1Endpoint
from kubernetes.client import V1EndpointConditions
from kubernetes.client import V1EndpointSlice
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1ObjectReference

from tests.data.kubernetes.namespaces import KUBERNETES_CLUSTER_1_NAMESPACES_DATA
from tests.data.kubernetes.pods import KUBERNETES_PODS_DATA

NAMESPACE = KUBERNETES_CLUSTER_1_NAMESPACES_DATA[-1]["name"]
SERVICE_NAME = "my-service"

KUBERNETES_ENDPOINT_SLICES_RAW = [
    V1EndpointSlice(
        metadata=V1ObjectMeta(
            uid="endpoint-slice-uid",
            name="my-service-abc12",
            namespace=NAMESPACE,
            labels={
                "kubernetes.io/service-name": SERVICE_NAME,
                "endpointslice.kubernetes.io/managed-by": (
                    "endpointslice-controller.k8s.io"
                ),
            },
            creation_timestamp=datetime(2026, 8, 1, tzinfo=timezone.utc),
        ),
        address_type="IPv4",
        ports=[
            DiscoveryV1EndpointPort(
                name="http",
                port=8080,
                protocol="TCP",
                app_protocol="http",
            )
        ],
        endpoints=[
            V1Endpoint(
                addresses=["10.0.1.10"],
                conditions=V1EndpointConditions(ready=True),
                node_name="worker-a",
                zone="example-zone-a",
                target_ref=V1ObjectReference(
                    api_version="v1",
                    kind="Pod",
                    name=KUBERNETES_PODS_DATA[0]["name"],
                    namespace=NAMESPACE,
                    uid=KUBERNETES_PODS_DATA[0]["uid"],
                ),
            ),
            V1Endpoint(
                addresses=["10.0.1.11"],
                conditions=V1EndpointConditions(ready=False),
                node_name="worker-b",
                zone="example-zone-b",
                target_ref=V1ObjectReference(
                    api_version="v1",
                    kind="Pod",
                    name=KUBERNETES_PODS_DATA[1]["name"],
                    namespace=NAMESPACE,
                    uid=KUBERNETES_PODS_DATA[1]["uid"],
                ),
            ),
        ],
    )
]
