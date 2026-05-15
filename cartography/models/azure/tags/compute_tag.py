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
class VMToTagRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class VMToTagRel(CartographyRelSchema):
    target_node_label: str = "AzureVirtualMachine"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: VMToTagRelProperties = VMToTagRelProperties()


@dataclass(frozen=True)
class AzureVMTagsSchema(CartographyNodeSchema):
    label: str = "AzureTag"
    properties: AzureTagProperties = AzureTagProperties()
    sub_resource_relationship: AzureTagToSubscriptionRel = AzureTagToSubscriptionRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            VMToTagRel(),
        ],
    )
