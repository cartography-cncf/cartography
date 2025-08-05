from datetime import datetime
from kubernetes.client import V1ObjectMeta, V1Role, V1RoleBinding, V1RoleRef, V1ServiceAccount, RbacV1Subject, V1PolicyRule

from cartography.intel.kubernetes.util import get_epoch
from tests.data.kubernetes.clusters import KUBERNETES_CLUSTER_NAMES

# Raw ServiceAccount data as returned by Kubernetes API
KUBERNETES_CLUSTER_1_SERVICE_ACCOUNTS_RAW = [
    V1ServiceAccount(
        metadata=V1ObjectMeta(
            name="demo-sa",
            namespace="demo-ns",
            uid="a1b2c3d4-5e6f-7890-abcd-ef1234567890",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:44:56+00:00"),
            resource_version="12345",
        ),
        automount_service_account_token=True,
    ),
    V1ServiceAccount(
        metadata=V1ObjectMeta(
            name="another-sa", 
            namespace="demo-ns",
            uid="b2c3d4e5-6f70-8901-bcde-f23456789012",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:44:57+00:00"),
            resource_version="12346",
        ),
        automount_service_account_token=False,
    ),
]

# Raw Role data as returned by Kubernetes API  
KUBERNETES_CLUSTER_1_ROLES_RAW = [
    V1Role(
        metadata=V1ObjectMeta(
            name="pod-reader",
            namespace="demo-ns", 
            uid="c3d4e5f6-7890-1234-cdef-345678901234",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:40:46+00:00"),
            resource_version="28797",
        ),
        rules=[
            V1PolicyRule(
                api_groups=[""],
                resources=["pods"],
                verbs=["get", "list", "watch"],
            ),
        ],
    ),
    V1Role(
        metadata=V1ObjectMeta(
            name="secret-manager",
            namespace="demo-ns",
            uid="d4e5f6g7-8901-2345-def0-456789012345",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:40:47+00:00"),
            resource_version="28798", 
        ),
        rules=[
            V1PolicyRule(
                api_groups=[""],
                resources=["secrets"],
                verbs=["get", "list", "create", "update", "delete"],
            ),
        ],
    ),
]

# Raw RoleBinding data as returned by Kubernetes API
KUBERNETES_CLUSTER_1_ROLE_BINDINGS_RAW = [
    V1RoleBinding(
        metadata=V1ObjectMeta(
            name="bind-demo-sa",
            namespace="demo-ns",
            uid="e5f6g7h8-9012-3456-ef01-567890123456", 
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:44:58+00:00"),
            resource_version="29000",
        ),
        role_ref=V1RoleRef(
            api_group="rbac.authorization.k8s.io",
            kind="Role",
            name="pod-reader",
        ),
        subjects=[
            RbacV1Subject(
                kind="ServiceAccount",
                name="demo-sa",
                namespace="demo-ns",
            ),
        ],
    ),
    V1RoleBinding(
        metadata=V1ObjectMeta(
            name="bind-another-sa", 
            namespace="demo-ns",
            uid="f6g7h8i9-0123-4567-f012-678901234567",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:44:59+00:00"),
            resource_version="29001",
        ),
        role_ref=V1RoleRef(
            api_group="rbac.authorization.k8s.io",
            kind="Role",
            name="secret-manager",
        ),
        subjects=[
            RbacV1Subject(
                kind="ServiceAccount",
                name="another-sa",
                namespace="demo-ns",
            ),
        ],
    ),
]

# Second cluster raw data (for multi-cluster testing)
KUBERNETES_CLUSTER_2_SERVICE_ACCOUNTS_RAW = [
    V1ServiceAccount(
        metadata=V1ObjectMeta(
            name="test-sa",
            namespace="test-ns", 
            uid="g7h8i9j0-1234-5678-g123-789012345678",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:45:00+00:00"),
            resource_version="12347",
        ),
        automount_service_account_token=True,
    ),
]

KUBERNETES_CLUSTER_2_ROLES_RAW = [
    V1Role(
        metadata=V1ObjectMeta(
            name="test-reader",
            namespace="test-ns",
            uid="h8i9j0k1-2345-6789-h234-890123456789", 
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:45:01+00:00"),
            resource_version="28799",
        ),
        rules=[
            V1PolicyRule(
                api_groups=[""],
                resources=["pods", "services"],
                verbs=["get", "list"],
            ),
        ],
    ),
]

KUBERNETES_CLUSTER_2_ROLE_BINDINGS_RAW = [
    V1RoleBinding(
        metadata=V1ObjectMeta(
            name="bind-test-sa",
            namespace="test-ns",
            uid="i9j0k1l2-3456-7890-i345-901234567890",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:45:02+00:00"), 
            resource_version="29002",
        ),
        role_ref=V1RoleRef(
            api_group="rbac.authorization.k8s.io",
            kind="Role",
            name="test-reader",
        ),
        subjects=[
            RbacV1Subject(
                kind="ServiceAccount",
                name="test-sa",
                namespace="test-ns",
            ),
        ],
    ),
]

# Expected node IDs after transformation (for test assertions)
KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS = [
    "demo-ns/demo-sa",
    "demo-ns/another-sa",
]

KUBERNETES_CLUSTER_1_ROLE_IDS = [
    "demo-ns/pod-reader",
    "demo-ns/secret-manager",
]

KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS = [
    "demo-ns/bind-demo-sa/demo-ns/demo-sa",
    "demo-ns/bind-another-sa/demo-ns/another-sa",
]

KUBERNETES_CLUSTER_2_SERVICE_ACCOUNT_IDS = [
    "test-ns/test-sa",
]

KUBERNETES_CLUSTER_2_ROLE_IDS = [
    "test-ns/test-reader",
]

KUBERNETES_CLUSTER_2_ROLE_BINDING_IDS = [
    "test-ns/bind-test-sa/test-ns/test-sa",
] 