import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import COMPUTE_CLUSTER

logger = logging.getLogger(__name__)


# --- Node Definitions ---
@dataclass(frozen=True)
class AzureKubernetesClusterProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the AKS cluster."
    )
    name: PropertyRef = PropertyRef("name", description="Name of the AKS cluster.")
    location: PropertyRef = PropertyRef(
        "location", description="Azure region where the cluster is deployed."
    )
    provisioning_state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the cluster.",
    )
    kubernetes_version: PropertyRef = PropertyRef(
        "kubernetes_version",
        description="Kubernetes version running on the cluster.",
    )
    fqdn: PropertyRef = PropertyRef(
        "fqdn", description="Fully qualified domain name of the API server."
    )
    api_server_public_access: PropertyRef = PropertyRef(
        "api_server_public_access",
        description="Whether the Kubernetes API server is reachable from public networks.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# --- Relationship Definitions ---
@dataclass(frozen=True)
class AzureKubernetesClusterToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKubernetesClusterToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the AKS cluster as a resource."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureKubernetesClusterToSubscriptionRelProperties = (
        AzureKubernetesClusterToSubscriptionRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class AzureKubernetesClusterSchema(CartographyNodeSchema):
    """An Azure Kubernetes Service cluster."""

    label: str = "AzureKubernetesCluster"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([COMPUTE_CLUSTER])
    properties: AzureKubernetesClusterProperties = AzureKubernetesClusterProperties()
    sub_resource_relationship: AzureKubernetesClusterToSubscriptionRel = (
        AzureKubernetesClusterToSubscriptionRel()
    )
