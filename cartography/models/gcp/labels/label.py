from dataclasses import dataclass

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

# --- Shared properties ---


@dataclass(frozen=True)
class GCPLabelNodeProperties(CartographyNodeProperties):
    """
    Properties for GCPLabel nodes.

    The id is computed as "{resource_id}:{key}:{value}" during ingestion.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key", extra_index=True)
    value: PropertyRef = PropertyRef("value")
    resource_type: PropertyRef = PropertyRef("resource_type")


@dataclass(frozen=True)
class GCPLabelToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToProjectRel(CartographyRelSchema):
    """(:GCPProject)-[:RESOURCE]->(:GCPLabel)"""

    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPLabelToProjectRelProperties = GCPLabelToProjectRelProperties()


@dataclass(frozen=True)
class GCPLabelToBucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToBucketRel(CartographyRelSchema):
    """(:GCPBucket)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToBucketRelProperties = GCPLabelToBucketRelProperties()


# --- GCPBucket label schema ---


@dataclass(frozen=True)
class GCPBucketGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPBucket resources.

    Carries the extra label GCPBucketLabel for backward compatibility with the
    legacy per-resource label schema.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["Label", "GCPBucketLabel", "ResourceTag"]
    )
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToBucketRel()],
    )


# --- GCPInstance label schema ---


@dataclass(frozen=True)
class GCPLabelToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToInstanceRel(CartographyRelSchema):
    """(:GCPInstance)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToInstanceRelProperties = GCPLabelToInstanceRelProperties()


@dataclass(frozen=True)
class GCPInstanceGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPInstance resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "ResourceTag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToInstanceRel()],
    )
