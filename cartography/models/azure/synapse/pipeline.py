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
class AzureSynapsePipelineProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapsePipelineToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapsePipelineToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "AzureSynapseWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureSynapsePipelineToWorkspaceRelProperties = (
        AzureSynapsePipelineToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapsePipelineToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapsePipelineToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSynapsePipelineToSubscriptionRelProperties = (
        AzureSynapsePipelineToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapsePipelineSchema(CartographyNodeSchema):
    label: str = "AzureSynapsePipeline"
    properties: AzureSynapsePipelineProperties = AzureSynapsePipelineProperties()
    sub_resource_relationship: AzureSynapsePipelineToSubscriptionRel = (
        AzureSynapsePipelineToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureSynapsePipelineToWorkspaceRel(),
        ],
    )
