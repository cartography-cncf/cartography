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
    id: PropertyRef = PropertyRef(
        "id",
        description="Posture ID from the ACL, for example `posture:healthySentinelOneMac`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Posture name without the `posture:` prefix."
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable description generated from the ACL conditions.",
    )


@dataclass(frozen=True)
class TailscaleDevicePostureConditionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable condition identifier derived from the posture ID and condition index.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="The posture attribute being evaluated, for example `sentinelOne:infected` or `node:os`.",
    )
    provider: PropertyRef = PropertyRef(
        "provider",
        description="The provider/namespace inferred from the attribute, for example `sentinelone` or `node`.",
    )
    operator: PropertyRef = PropertyRef(
        "operator", description="Comparison operator such as `==`, `IN`, or `IS SET`."
    )
    value: PropertyRef = PropertyRef(
        "value", description="Expected comparison value serialized as a string."
    )


@dataclass(frozen=True)
class _ToTailnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
class TailscaleDevicePostureToTailnetRel(CartographyRelSchema):
    """Defines the RESOURCE relationship to TailscaleTailnet nodes."""

    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: _ToTailnetRelProperties = _ToTailnetRelProperties()


@dataclass(frozen=True)
class TailscaleDevicePostureConditionToTailnetRel(CartographyRelSchema):
    """Defines the RESOURCE relationship to TailscaleTailnet nodes."""

    target_node_label: str = "TailscaleTailnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: _ToTailnetRelProperties = _ToTailnetRelProperties()


@dataclass(frozen=True)
class TailscaleDevicePostureHasConditionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
class TailscaleDevicePostureHasConditionRel(CartographyRelSchema):
    """Defines the HAS_CONDITION relationship to TailscaleDevicePostureCondition nodes."""

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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )


@dataclass(frozen=True)
class TailscaleDevicePostureConditionRequiresRel(CartographyRelSchema):
    """Defines the REQUIRES relationship to TailscalePostureIntegration nodes."""

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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
        description="Label used to scope relationship cleanup.",
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
        description="Identifier used to scope relationship cleanup.",
    )


@dataclass(frozen=True)
class TailscaleDeviceToPostureConditionMatchLink(CartographyRelSchema):
    """Defines the CONFORMS_TO relationship to TailscaleDevicePostureCondition nodes."""

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
    """Defines the CONFORMS_TO relationship to TailscaleDevicePosture nodes."""

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
    """Logical posture policy blocks defined in the ACL."""

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
    """Atomic posture assertions extracted from ACL posture definitions."""

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
