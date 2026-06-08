from dataclasses import dataclass

from cartography.models.aws.cloudtrail.management_events import (
    AssumedRoleWithSAMLMatchLink,
)
from cartography.models.aws.ecs.containers import ECSContainerToTaskRel
from cartography.models.aws.ecs.services import ECSServiceToECSClusterRel
from cartography.models.aws.ecs.services import ECSServiceToECSTaskRel
from cartography.models.aws.ecs.tasks import ECSTaskToECSClusterRel
from cartography.models.aws.identitycenter.awspermissionset import (
    AWSRoleToSSOUserMatchLink,
)
from cartography.models.aws.identitycenter.awsssouser import (
    AWSSSOUserToPermissionSetRel,
)
from cartography.models.azure.container_instance import (
    AzureGroupContainerToContainerInstanceRel,
)
from cartography.models.gcp.cloudrun.job_container import CloudRunJobToContainerRel
from cartography.models.gcp.cloudrun.service_container import (
    CloudRunServiceToContainerRel,
)
from cartography.models.keycloak.role import KeycloakRoleToUserRel
from cartography.models.kubernetes.containers import (
    KubernetesContainerToKubernetesPodRel,
)
from cartography.models.kubernetes.namespaces import (
    KubernetesNamespaceToKubernetesClusterRel,
)
from cartography.models.kubernetes.pods import KubernetesPodToKubernetesClusterRel
from cartography.models.kubernetes.pods import KubernetesPodToKubernetesNamespaceRel
from cartography.models.kubernetes.serviceaccounts import (
    KubernetesServiceAccountToAWSRoleRel,
)
from cartography.models.kubernetes.users import KubernetesUserToAWSRoleRel


@dataclass(frozen=True)
class RelConstraint:
    """If a node carrying ontology label `src` has an outward edge toward a
    node carrying ontology label `dst`, that edge MUST be named `label`.

    The constraint never requires the edge to exist; it only constrains the
    name when both endpoints carry the listed ontology labels. Both abstract
    ontology nodes (User, Device, PublicIP, Package) and semantic extra
    labels (Container, ComputePod, ...) are valid src/dst values.
    """

    src: str
    dst: str
    label: str


# Canonical relationship names enforced by test_ontology_rel_constraints.
ONTOLOGY_REL_CONSTRAINTS: tuple[RelConstraint, ...] = (
    # User has one or many UserAccount on different platforms.
    RelConstraint(src="User", dst="UserAccount", label="HAS_ACCOUNT"),
    # Unified workload chain: child workload points at its parent.
    RelConstraint(src="Container", dst="ComputePod", label="WORKLOAD_PARENT"),
    RelConstraint(src="Container", dst="ComputeService", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeService", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeNamespace", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputePod", dst="ComputeCluster", label="WORKLOAD_PARENT"),
    RelConstraint(src="ComputeService", dst="ComputeCluster", label="WORKLOAD_PARENT"),
    RelConstraint(
        src="ComputeNamespace", dst="ComputeCluster", label="WORKLOAD_PARENT"
    ),
    # A user account is granted a role.
    RelConstraint(src="UserAccount", dst="PermissionRole", label="HAS_ROLE"),
    # A service account (workload identity) is granted a role. No provider
    # currently wires a direct edge (all go through binding nodes), so this is
    # forward-looking governance for future modules.
    RelConstraint(src="ServiceAccount", dst="PermissionRole", label="HAS_ROLE"),
)


# DEPRECATED: pre-V1 rel classes tolerated until they are removed in v1.0.0.
LEGACY_REL_WHITELIST: frozenset[type] = frozenset(
    {
        # DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0.
        AzureGroupContainerToContainerInstanceRel,
        CloudRunJobToContainerRel,
        CloudRunServiceToContainerRel,
        ECSContainerToTaskRel,
        ECSServiceToECSClusterRel,
        ECSServiceToECSTaskRel,
        ECSTaskToECSClusterRel,
        KubernetesContainerToKubernetesPodRel,
        KubernetesPodToKubernetesNamespaceRel,
        # Kubernetes models its cluster as the tenant, so the pod's and
        # namespace's sub_resource_relationship uses RESOURCE on a pair that
        # the ontology also constrains as WORKLOAD_PARENT. Whitelisted until
        # tenant scoping and the workload chain are reconciled.
        KubernetesNamespaceToKubernetesClusterRel,
        KubernetesPodToKubernetesClusterRel,
        # DEPRECATED: replaced by HAS_ROLE, will be removed in v1.0.0.
        AWSSSOUserToPermissionSetRel,
        KeycloakRoleToUserRel,
        # ALLOWED_BY is a distinct "this role is assumable by that SSO user"
        # semantic (PermissionRole->UserAccount), not a role assignment, so it
        # intentionally runs counter to the HAS_ROLE (UserAccount->PermissionRole)
        # direction. Whitelisted so the constraint does not flag it.
        AWSRoleToSSOUserMatchLink,
        # MAPS_TO is an identity-federation mapping (a Kubernetes user authenticates
        # as an AWS role/user), not a role grant. Distinct from HAS_ROLE.
        KubernetesUserToAWSRoleRel,
        # ASSUMED_ROLE_WITH_SAML records a CloudTrail-observed runtime assumption
        # event, not a static role assignment. Distinct from HAS_ROLE.
        AssumedRoleWithSAMLMatchLink,
        # ASSUMES_ROLE is workload-identity federation (a Kubernetes service
        # account assumes an AWS IAM role, IRSA-style). This is the canonical
        # ASSUMES semantic, not a static role grant. Distinct from HAS_ROLE.
        KubernetesServiceAccountToAWSRoleRel,
    }
)
