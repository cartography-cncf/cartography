from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SERVICE_ACCOUNT


@dataclass(frozen=True)
class KubernetesServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Identifier for the ServiceAccount derived from cluster_name, namespace and name (e.g. `my-cluster/default/my-service-account`).",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the Kubernetes ServiceAccount."
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        description="The Kubernetes namespace where this ServiceAccount is deployed.",
    )
    automount_service_account_token: PropertyRef = PropertyRef(
        "automount_service_account_token",
        description="Whether the ServiceAccount token should be automatically mounted in pods.",
    )
    aws_role_arn: PropertyRef = PropertyRef(
        "aws_role_arn",
        description="ARN from the IRSA annotation `eks.amazonaws.com/role-arn`, when present. Used to link the ServiceAccount to an `AWSRole`.",
    )
    gcp_service_account: PropertyRef = PropertyRef(
        "gcp_service_account",
        description="Email from the GKE Workload Identity annotation `iam.gke.io/gcp-service-account`, when present. Used to link the ServiceAccount to a `GCPServiceAccount`.",
    )
    uid: PropertyRef = PropertyRef(
        "uid", description="UID of the Kubernetes ServiceAccount."
    )
    creation_timestamp: PropertyRef = PropertyRef(
        "creation_timestamp",
        description="Timestamp of the creation time of the Kubernetes ServiceAccount.",
    )
    resource_version: PropertyRef = PropertyRef(
        "resource_version",
        description="The resource version of the ServiceAccount for optimistic concurrency control.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceAccountToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceAccountToNamespaceRel(CartographyRelSchema):
    """Links a namespace to a service account it contains."""

    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesServiceAccountToNamespaceRelProperties = (
        KubernetesServiceAccountToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceAccountToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceAccountToClusterRel(CartographyRelSchema):
    """Links a cluster to one of its service accounts."""

    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesServiceAccountToClusterRelProperties = (
        KubernetesServiceAccountToClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceAccountToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceAccountToAWSRoleRel(CartographyRelSchema):
    """Links a service account to the AWS IAM role it can assume through IRSA."""

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_role_arn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES_ROLE"
    properties: KubernetesServiceAccountToAWSRoleRelProperties = (
        KubernetesServiceAccountToAWSRoleRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceAccountToGCPServiceAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesServiceAccountToGCPServiceAccountRel(CartographyRelSchema):
    """Links a service account to the Google Cloud service account it impersonates through Workload Identity."""

    target_node_label: str = "GCPServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("gcp_service_account")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_IDENTITY_BINDING"
    properties: KubernetesServiceAccountToGCPServiceAccountRelProperties = (
        KubernetesServiceAccountToGCPServiceAccountRelProperties()
    )


@dataclass(frozen=True)
class KubernetesServiceAccountSchema(CartographyNodeSchema):
    "A service account used by workloads in a Kubernetes cluster."

    label: str = "KubernetesServiceAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
    properties: KubernetesServiceAccountNodeProperties = (
        KubernetesServiceAccountNodeProperties()
    )
    sub_resource_relationship: KubernetesServiceAccountToClusterRel = (
        KubernetesServiceAccountToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesServiceAccountToNamespaceRel(),
            KubernetesServiceAccountToAWSRoleRel(),
            KubernetesServiceAccountToGCPServiceAccountRel(),
        ]
    )
