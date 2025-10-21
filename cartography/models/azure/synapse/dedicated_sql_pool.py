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
class AzureSynapseDedicatedSqlPoolProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    state: PropertyRef = PropertyRef("provisioning_state")
    sku: PropertyRef = PropertyRef("sku")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseDedicatedSqlPoolToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseDedicatedSqlPoolToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "AzureSynapseWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureSynapseDedicatedSqlPoolToWorkspaceRelProperties = (
        AzureSynapseDedicatedSqlPoolToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapseDedicatedSqlPoolToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseDedicatedSqlPoolToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSynapseDedicatedSqlPoolToSubscriptionRelProperties = (
        AzureSynapseDedicatedSqlPoolToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapseDedicatedSqlPoolSchema(CartographyNodeSchema):
    label: str = "AzureSynapseDedicatedSqlPool"
    properties: AzureSynapseDedicatedSqlPoolProperties = (
        AzureSynapseDedicatedSqlPoolProperties()
    )
    sub_resource_relationship: AzureSynapseDedicatedSqlPoolToSubscriptionRel = (
        AzureSynapseDedicatedSqlPoolToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureSynapseDedicatedSqlPoolToWorkspaceRel(),
        ],
    )
