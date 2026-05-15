from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureSynapseManagedPrivateEndpointProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    target_resource_id: PropertyRef = PropertyRef("target_resource_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseManagedPrivateEndpointToWorkspaceRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseManagedPrivateEndpointToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "AzureSynapseWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureSynapseManagedPrivateEndpointToWorkspaceRelProperties = (
        AzureSynapseManagedPrivateEndpointToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapseManagedPrivateEndpointToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseManagedPrivateEndpointToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSynapseManagedPrivateEndpointToSubscriptionRelProperties = (
        AzureSynapseManagedPrivateEndpointToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapseManagedPrivateEndpointSchema(CartographyNodeSchema):
    label: str = "AzureSynapseManagedPrivateEndpoint"
    properties: AzureSynapseManagedPrivateEndpointProperties = (
        AzureSynapseManagedPrivateEndpointProperties()
    )
    sub_resource_relationship: AzureSynapseManagedPrivateEndpointToSubscriptionRel = (
        AzureSynapseManagedPrivateEndpointToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureSynapseManagedPrivateEndpointToWorkspaceRel(),
        ],
    )
