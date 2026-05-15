from dataclasses import dataclass

from cartography.models.azure.tags.tag import AzureTagProperties
from cartography.models.azure.tags.tag import AzureTagToSubscriptionRel
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class LoadBalancerToTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LoadBalancerToTagRel(CartographyRelSchema):
    target_node_label: str = "AzureLoadBalancer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: LoadBalancerToTagRelProperties = LoadBalancerToTagRelProperties()


@dataclass(frozen=True)
class AzureLoadBalancerTagsSchema(CartographyNodeSchema):
    label: str = "AzureTag"
    properties: AzureTagProperties = AzureTagProperties()
    sub_resource_relationship: AzureTagToSubscriptionRel = AzureTagToSubscriptionRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LoadBalancerToTagRel(),
        ],
    )
