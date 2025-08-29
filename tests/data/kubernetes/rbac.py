from datetime import datetime

from kubernetes.client import RbacV1Subject
from kubernetes.client import V1ClusterRole
from kubernetes.client import V1ClusterRoleBinding
from kubernetes.client import V1ObjectMeta
from kubernetes.client import V1PolicyRule
from kubernetes.client import V1Role
from kubernetes.client import V1RoleBinding
from kubernetes.client import V1RoleRef
from kubernetes.client import V1ServiceAccount

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
            RbacV1Subject(
                kind="User",
                name="john.doe@company.com",
            ),
            RbacV1Subject(
                kind="Group",
                name="developers",
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

# Raw ClusterRole data as returned by Kubernetes API
KUBERNETES_CLUSTER_1_CLUSTER_ROLES_RAW = [
    V1ClusterRole(
        metadata=V1ObjectMeta(
            name="cluster-admin",
            uid="j0k1l2m3-4567-8901-j456-012345678901",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:30:00+00:00"),
            resource_version="10001",
        ),
        rules=[
            V1PolicyRule(
                api_groups=["*"],
                resources=["*"],
                verbs=["*"],
            ),
        ],
    ),
    V1ClusterRole(
        metadata=V1ObjectMeta(
            name="pod-viewer",
            uid="k1l2m3n4-5678-9012-k567-123456789012",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:30:01+00:00"),
            resource_version="10002",
        ),
        rules=[
            V1PolicyRule(
                api_groups=[""],
                resources=["pods"],
                verbs=["get", "list", "watch"],
            ),
            V1PolicyRule(
                api_groups=["apps"],
                resources=["deployments"],
                verbs=["get", "list"],
            ),
        ],
    ),
]

# Raw ClusterRoleBinding data as returned by Kubernetes API
KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDINGS_RAW = [
    V1ClusterRoleBinding(
        metadata=V1ObjectMeta(
            name="admin-binding",
            uid="l2m3n4o5-6789-0123-l678-234567890123",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:45:03+00:00"),
            resource_version="30001",
        ),
        role_ref=V1RoleRef(
            api_group="rbac.authorization.k8s.io",
            kind="ClusterRole",
            name="cluster-admin",
        ),
        subjects=[
            RbacV1Subject(
                kind="ServiceAccount",
                name="demo-sa",
                namespace="demo-ns",
            ),
            RbacV1Subject(
                kind="User",
                name="admin@company.com",
            ),
            RbacV1Subject(
                kind="Group",
                name="admins",
            ),
        ],
    ),
    V1ClusterRoleBinding(
        metadata=V1ObjectMeta(
            name="viewer-binding",
            uid="m3n4o5p6-7890-1234-m789-345678901234",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:45:04+00:00"),
            resource_version="30002",
        ),
        role_ref=V1RoleRef(
            api_group="rbac.authorization.k8s.io",
            kind="ClusterRole",
            name="pod-viewer",
        ),
        subjects=[
            RbacV1Subject(
                kind="ServiceAccount",
                name="another-sa",
                namespace="demo-ns",
            ),
            RbacV1Subject(
                kind="ServiceAccount",
                name="test-sa",
                namespace="test-ns",
            ),
        ],
    ),
]

# Second cluster ClusterRole and ClusterRoleBinding data (for multi-cluster testing)
KUBERNETES_CLUSTER_2_CLUSTER_ROLES_RAW = [
    V1ClusterRole(
        metadata=V1ObjectMeta(
            name="cluster-viewer",
            uid="n4o5p6q7-8901-2345-n890-456789012345",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:30:02+00:00"),
            resource_version="10003",
        ),
        rules=[
            V1PolicyRule(
                api_groups=[""],
                resources=["pods", "services", "configmaps"],
                verbs=["get", "list", "watch"],
            ),
        ],
    ),
]

KUBERNETES_CLUSTER_2_CLUSTER_ROLE_BINDINGS_RAW = [
    V1ClusterRoleBinding(
        metadata=V1ObjectMeta(
            name="cluster-viewer-binding",
            uid="o5p6q7r8-9012-3456-o901-567890123456",
            creation_timestamp=datetime.fromisoformat("2024-09-04T18:45:05+00:00"),
            resource_version="30003",
        ),
        role_ref=V1RoleRef(
            api_group="rbac.authorization.k8s.io",
            kind="ClusterRole",
            name="cluster-viewer",
        ),
        subjects=[
            RbacV1Subject(
                kind="ServiceAccount",
                name="test-sa",
                namespace="test-ns",
            ),
            RbacV1Subject(
                kind="User",
                name="viewer@company.com",
            ),
            RbacV1Subject(
                kind="Group",
                name="viewers",
            ),
        ],
    ),
]

# Expected node IDs after transformation (for test assertions)
KUBERNETES_CLUSTER_1_SERVICE_ACCOUNT_IDS = [
    "my-cluster-1/demo-ns/demo-sa",
    "my-cluster-1/demo-ns/another-sa",
    "my-cluster-1/test-ns/test-sa",
]

KUBERNETES_CLUSTER_1_ROLE_IDS = [
    "my-cluster-1/demo-ns/pod-reader",
    "my-cluster-1/demo-ns/secret-manager",
]

KUBERNETES_CLUSTER_1_ROLE_BINDING_IDS = [
    "my-cluster-1/demo-ns/bind-demo-sa",
    "my-cluster-1/demo-ns/bind-another-sa",
]

KUBERNETES_CLUSTER_2_SERVICE_ACCOUNT_IDS = [
    "my-cluster-2/test-ns/test-sa",
]

KUBERNETES_CLUSTER_2_ROLE_IDS = [
    "my-cluster-2/test-ns/test-reader",
]

KUBERNETES_CLUSTER_2_ROLE_BINDING_IDS = [
    "my-cluster-2/test-ns/bind-test-sa",
]

# Expected ClusterRole IDs after transformation
KUBERNETES_CLUSTER_1_CLUSTER_ROLE_IDS = [
    "my-cluster-1/cluster-admin",
    "my-cluster-1/pod-viewer",
]

KUBERNETES_CLUSTER_2_CLUSTER_ROLE_IDS = [
    "my-cluster-2/cluster-viewer",
]

# Expected ClusterRoleBinding IDs after transformation
KUBERNETES_CLUSTER_1_CLUSTER_ROLE_BINDING_IDS = [
    "my-cluster-1/admin-binding",
    "my-cluster-1/viewer-binding",
]

KUBERNETES_CLUSTER_2_CLUSTER_ROLE_BINDING_IDS = [
    "my-cluster-2/cluster-viewer-binding",
]

# Expected User IDs after transformation
KUBERNETES_CLUSTER_1_USER_IDS = [
    "my-cluster-1/admin@company.com",
    "my-cluster-1/john.doe@company.com",
]

KUBERNETES_CLUSTER_2_USER_IDS = [
    "my-cluster-2/viewer@company.com",
]

# Expected Group IDs after transformation
KUBERNETES_CLUSTER_1_GROUP_IDS = [
    "my-cluster-1/admins",
    "my-cluster-1/developers",
]

KUBERNETES_CLUSTER_2_GROUP_IDS = [
    "my-cluster-2/viewers",
]

# Test namespace data for RBAC integration tests
RBAC_TEST_NAMESPACES_DATA = [
    {
        "uid": "demo-ns-uid-12345",
        "name": "demo-ns",
        "creation_timestamp": 1725476600,
        "deletion_timestamp": None,
        "status_phase": "Active",
    },
    {
        "uid": "test-ns-uid-67890",
        "name": "test-ns",
        "creation_timestamp": 1725476601,
        "deletion_timestamp": None,
        "status_phase": "Active",
    },
]

# Mock Okta Users for identity mapping tests
# These map to existing Kubernetes users in the RBAC test data
MOCK_OKTA_USERS = [
    {
        "id": "okta-user-1",
        "email": "john.doe@company.com",  # Maps to existing K8s user "john.doe@company.com"
        "firstName": "John",
        "lastName": "Doe",
        "login": "john.doe@company.com",
        "status": "ACTIVE",
    },
    {
        "id": "okta-user-2",
        "email": "admin@company.com",  # Maps to existing K8s user "admin@company.com"
        "firstName": "Admin",
        "lastName": "User",
        "login": "admin@company.com",
        "status": "ACTIVE",
    },
    {
        "id": "okta-user-3",
        "email": "viewer@company.com",  # Maps to existing K8s user "viewer@company.com" (cluster 2)
        "firstName": "Viewer",
        "lastName": "User",
        "login": "viewer@company.com",
        "status": "ACTIVE",
    },
]

# Mock Okta Groups for identity mapping tests
# These map to existing Kubernetes groups in the RBAC test data
MOCK_OKTA_GROUPS = [
    {
        "id": "okta-group-1",
        "name": "developers",  # Maps to existing K8s group "developers"
        "description": "Development team",
        "type": "OKTA_GROUP",
    },
    {
        "id": "okta-group-2",
        "name": "admins",  # Maps to existing K8s group "admins"
        "description": "System administrators",
        "type": "OKTA_GROUP",
    },
    {
        "id": "okta-group-3",
        "name": "viewers",  # Maps to existing K8s group "viewers" (cluster 2)
        "description": "Viewer access group",
        "type": "OKTA_GROUP",
    },
]
