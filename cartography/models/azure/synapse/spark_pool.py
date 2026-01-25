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
class AzureSynapseSparkPoolProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    state: PropertyRef = PropertyRef("provisioning_state")
    node_size: PropertyRef = PropertyRef("node_size")
    node_count: PropertyRef = PropertyRef("node_count")
    spark_version: PropertyRef = PropertyRef("spark_version")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseSparkPoolToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseSparkPoolToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "AzureSynapseWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureSynapseSparkPoolToWorkspaceRelProperties = (
        AzureSynapseSparkPoolToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapseSparkPoolToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureSynapseSparkPoolToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSynapseSparkPoolToSubscriptionRelProperties = (
        AzureSynapseSparkPoolToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSynapseSparkPoolSchema(CartographyNodeSchema):
    label: str = "AzureSynapseSparkPool"
    properties: AzureSynapseSparkPoolProperties = AzureSynapseSparkPoolProperties()
    sub_resource_relationship: AzureSynapseSparkPoolToSubscriptionRel = (
        AzureSynapseSparkPoolToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureSynapseSparkPoolToWorkspaceRel(),
        ],
    )
