from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class TailscaleDevicePostureNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")


@dataclass(frozen=True)
class TailscaleDevicePostureConditionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    provider: PropertyRef = PropertyRef("provider")
    operator: PropertyRef = PropertyRef("operator")
    value: PropertyRef = PropertyRef("value")


@dataclass(frozen=True)
class _ToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TailscaleDevicePostureToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: _ToTailnetRelProperties = _ToTailnetRelProperties()


@dataclass(frozen=True)
class TailscaleDevicePostureConditionToTailnetRel(CartographyRelSchema):
    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: _ToTailnetRelProperties = _ToTailnetRelProperties()


@dataclass(frozen=True)
class TailscaleDevicePostureHasConditionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TailscaleDevicePostureHasConditionRel(CartographyRelSchema):
    target_node_label: str = "TailscaleDevicePostureCondition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("condition_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_CONDITION"
    properties: TailscaleDevicePostureHasConditionRelProperties = (
        TailscaleDevicePostureHasConditionRelProperties()
    )


@dataclass(frozen=True)
class TailscaleDevicePostureConditionRequiresRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TailscaleDevicePostureConditionRequiresRel(CartographyRelSchema):
    target_node_label: str = "TailscalePostureIntegration"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"provider": PropertyRef("provider")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REQUIRES"
    properties: TailscaleDevicePostureConditionRequiresRelProperties = (
        TailscaleDevicePostureConditionRequiresRelProperties()
    )


@dataclass(frozen=True)
class TailscaleDeviceConformsToRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class TailscaleDeviceToPostureConditionMatchLink(CartographyRelSchema):
    source_node_label: str = "TailscaleDevice"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    target_node_label: str = "TailscaleDevicePostureCondition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("condition_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONFORMS_TO"
    properties: TailscaleDeviceConformsToRelProperties = (
        TailscaleDeviceConformsToRelProperties()
    )


@dataclass(frozen=True)
class TailscaleDeviceToPostureMatchLink(CartographyRelSchema):
    source_node_label: str = "TailscaleDevice"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("device_id")},
    )
    target_node_label: str = "TailscaleDevicePosture"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("posture_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONFORMS_TO"
    properties: TailscaleDeviceConformsToRelProperties = (
        TailscaleDeviceConformsToRelProperties()
    )


@dataclass(frozen=True)
class TailscaleDevicePostureSchema(CartographyNodeSchema):
    label: str = "TailscaleDevicePosture"
    properties: TailscaleDevicePostureNodeProperties = (
        TailscaleDevicePostureNodeProperties()
    )
    sub_resource_relationship: TailscaleDevicePostureToTailnetRel = (
        TailscaleDevicePostureToTailnetRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [TailscaleDevicePostureHasConditionRel()],
    )


@dataclass(frozen=True)
class TailscaleDevicePostureConditionSchema(CartographyNodeSchema):
    label: str = "TailscaleDevicePostureCondition"
    properties: TailscaleDevicePostureConditionNodeProperties = (
        TailscaleDevicePostureConditionNodeProperties()
    )
    sub_resource_relationship: TailscaleDevicePostureConditionToTailnetRel = (
        TailscaleDevicePostureConditionToTailnetRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [TailscaleDevicePostureConditionRequiresRel()],
    )
