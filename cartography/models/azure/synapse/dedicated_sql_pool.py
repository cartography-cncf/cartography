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
    id: PropertyRef = PropertyRef(
        "id", description="Full Azure resource ID of the dedicated SQL pool."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name of the dedicated SQL pool."
    )
    location: PropertyRef = PropertyRef(
        "location",
        description="Azure region where the dedicated SQL pool is deployed.",
    )
    state: PropertyRef = PropertyRef(
        "provisioning_state",
        description="Current provisioning state of the dedicated SQL pool.",
    )
    sku: PropertyRef = PropertyRef(
        "sku", description="SKU name that defines the pool's service tier and capacity."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseDedicatedSqlPoolToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseDedicatedSqlPoolToWorkspaceRel(CartographyRelSchema):
    """An Azure Synapse workspace contains this dedicated SQL pool."""

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
    """An Azure subscription contains this dedicated SQL pool resource."""

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
    """An Azure Synapse dedicated SQL pool for enterprise data warehousing."""

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
