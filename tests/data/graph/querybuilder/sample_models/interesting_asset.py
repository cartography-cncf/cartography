from dataclasses import dataclass
from typing import Optional

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
from tests.data.graph.querybuilder.sample_models.simple_node import SimpleNodeProperties


@dataclass(frozen=True)
class InterestingAssetProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    property1: PropertyRef = PropertyRef("property1")
    property2: PropertyRef = PropertyRef("property2")


@dataclass(frozen=True)
class InterestingAssetToSubResourceRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    another_rel_field: PropertyRef = PropertyRef("AnotherField")
    yet_another_rel_field: PropertyRef = PropertyRef("YetAnotherRelField")


@dataclass(frozen=True)
class InterestingAssetToSubResourceRel(CartographyRelSchema):
    """
    Define a sub resource relationship
    (:InterestingAsset)<-[:RELATIONSHIP_LABEL]-(:SubResource)
    """

    target_node_label: str = "SubResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("sub_resource_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RELATIONSHIP_LABEL"
    properties: InterestingAssetToSubResourceRelProps = (
        InterestingAssetToSubResourceRelProps()
    )


@dataclass(frozen=True)
class InterestingAssetToHelloAssetRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InterestingAssetToHelloAssetRel(CartographyRelSchema):
    """
    Define an additional relationship
    (:InterestingAsset)-[:ASSOCIATED_WITH]->(:HelloAsset)
    """

    target_node_label: str = "HelloAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("hello_asset_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: InterestingAssetToHelloAssetRelProps = (
        InterestingAssetToHelloAssetRelProps()
    )


@dataclass(frozen=True)
class InterestingAssetToWorldAssetRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class InterestingAssetToWorldAssetRel(CartographyRelSchema):
    """
    Define yet another relationship.
    (:InterestingAsset)<-[:CONNECTED]-(:WorldAsset)
    """

    target_node_label: str = "WorldAsset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("world_asset_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONNECTED"
    properties: InterestingAssetToWorldAssetRelProps = (
        InterestingAssetToWorldAssetRelProps()
    )


@dataclass(frozen=True)
class InterestingAssetSchema(CartographyNodeSchema):
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        ["AnotherNodeLabel", "YetAnotherNodeLabel"],
    )
    label: str = "InterestingAsset"
    properties: SimpleNodeProperties = SimpleNodeProperties()
    sub_resource_relationship: InterestingAssetToSubResourceRel = (
        InterestingAssetToSubResourceRel()
    )
    other_relationships: Optional[OtherRelationships] = OtherRelationships(
        [
            InterestingAssetToHelloAssetRel(),
            InterestingAssetToWorldAssetRel(),
        ],
    )
