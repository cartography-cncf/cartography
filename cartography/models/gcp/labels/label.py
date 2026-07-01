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


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
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


@dataclass(frozen=True)
class GCPLabelToBucketTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToBucketTaggedRel(CartographyRelSchema):
    """(:GCPBucket)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GCPBucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToBucketTaggedRelProperties = (
        GCPLabelToBucketTaggedRelProperties()
    )


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
        ["Label", "GCPBucketLabel", "Tag"]
    )
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToBucketRel(), GCPLabelToBucketTaggedRel()],
    )


# --- GCPInstance label schema ---


@dataclass(frozen=True)
class GCPLabelToInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
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
class GCPLabelToInstanceTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToInstanceTaggedRel(CartographyRelSchema):
    """(:GCPInstance)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GCPInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToInstanceTaggedRelProperties = (
        GCPLabelToInstanceTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPInstanceGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPInstance resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToInstanceRel(), GCPLabelToInstanceTaggedRel()],
    )


# --- GKECluster label schema ---


@dataclass(frozen=True)
class GCPLabelToGKEClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToGKEClusterRel(CartographyRelSchema):
    """(:GKECluster)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GKECluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToGKEClusterRelProperties = GCPLabelToGKEClusterRelProperties()


@dataclass(frozen=True)
class GCPLabelToGKEClusterTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToGKEClusterTaggedRel(CartographyRelSchema):
    """(:GKECluster)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GKECluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToGKEClusterTaggedRelProperties = (
        GCPLabelToGKEClusterTaggedRelProperties()
    )


@dataclass(frozen=True)
class GKEClusterGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GKECluster resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToGKEClusterRel(), GCPLabelToGKEClusterTaggedRel()],
    )


# --- GCPCloudSQLInstance label schema ---


@dataclass(frozen=True)
class GCPLabelToCloudSQLInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToCloudSQLInstanceRel(CartographyRelSchema):
    """(:GCPCloudSQLInstance)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToCloudSQLInstanceRelProperties = (
        GCPLabelToCloudSQLInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToCloudSQLInstanceTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToCloudSQLInstanceTaggedRel(CartographyRelSchema):
    """(:GCPCloudSQLInstance)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToCloudSQLInstanceTaggedRelProperties = (
        GCPLabelToCloudSQLInstanceTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudSQLInstanceGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPCloudSQLInstance resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToCloudSQLInstanceRel(), GCPLabelToCloudSQLInstanceTaggedRel()],
    )


# --- GCPBigtableInstance label schema ---


@dataclass(frozen=True)
class GCPLabelToBigtableInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToBigtableInstanceRel(CartographyRelSchema):
    """(:GCPBigtableInstance)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPBigtableInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToBigtableInstanceRelProperties = (
        GCPLabelToBigtableInstanceRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToBigtableInstanceTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToBigtableInstanceTaggedRel(CartographyRelSchema):
    """(:GCPBigtableInstance)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GCPBigtableInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToBigtableInstanceTaggedRelProperties = (
        GCPLabelToBigtableInstanceTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPBigtableInstanceGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPBigtableInstance resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToBigtableInstanceRel(), GCPLabelToBigtableInstanceTaggedRel()],
    )


# --- GCPDNSZone label schema ---


@dataclass(frozen=True)
class GCPLabelToDNSZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToDNSZoneRel(CartographyRelSchema):
    """(:GCPDNSZone)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToDNSZoneRelProperties = GCPLabelToDNSZoneRelProperties()


@dataclass(frozen=True)
class GCPLabelToDNSZoneTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToDNSZoneTaggedRel(CartographyRelSchema):
    """(:GCPDNSZone)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GCPDNSZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToDNSZoneTaggedRelProperties = (
        GCPLabelToDNSZoneTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPDNSZoneGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPDNSZone resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToDNSZoneRel(), GCPLabelToDNSZoneTaggedRel()],
    )


# --- GCPSecretManagerSecret label schema ---


@dataclass(frozen=True)
class GCPLabelToSecretManagerSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToSecretManagerSecretRel(CartographyRelSchema):
    """(:GCPSecretManagerSecret)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPSecretManagerSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToSecretManagerSecretRelProperties = (
        GCPLabelToSecretManagerSecretRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToSecretManagerSecretTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToSecretManagerSecretTaggedRel(CartographyRelSchema):
    """(:GCPSecretManagerSecret)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GCPSecretManagerSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToSecretManagerSecretTaggedRelProperties = (
        GCPLabelToSecretManagerSecretTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPSecretManagerSecretGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPSecretManagerSecret resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToSecretManagerSecretRel(), GCPLabelToSecretManagerSecretTaggedRel()],
    )


# --- GCPCloudRunService label schema ---


@dataclass(frozen=True)
class GCPLabelToCloudRunServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToCloudRunServiceRel(CartographyRelSchema):
    """(:GCPCloudRunService)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToCloudRunServiceRelProperties = (
        GCPLabelToCloudRunServiceRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToCloudRunServiceTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToCloudRunServiceTaggedRel(CartographyRelSchema):
    """(:GCPCloudRunService)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GCPCloudRunService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToCloudRunServiceTaggedRelProperties = (
        GCPLabelToCloudRunServiceTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunServiceGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPCloudRunService resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToCloudRunServiceRel(), GCPLabelToCloudRunServiceTaggedRel()],
    )


# --- GCPCloudRunJob label schema ---


@dataclass(frozen=True)
class GCPLabelToCloudRunJobRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by :TAGGED, will be removed in v1.0.0
@dataclass(frozen=True)
class GCPLabelToCloudRunJobRel(CartographyRelSchema):
    """(:GCPCloudRunJob)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPCloudRunJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToCloudRunJobRelProperties = (
        GCPLabelToCloudRunJobRelProperties()
    )


@dataclass(frozen=True)
class GCPLabelToCloudRunJobTaggedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToCloudRunJobTaggedRel(CartographyRelSchema):
    """(:GCPCloudRunJob)-[:TAGGED]->(:GCPLabel)"""

    target_node_label: str = "GCPCloudRunJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAGGED"
    properties: GCPLabelToCloudRunJobTaggedRelProperties = (
        GCPLabelToCloudRunJobTaggedRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudRunJobGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPCloudRunJob resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label", "Tag"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToCloudRunJobRel(), GCPLabelToCloudRunJobTaggedRel()],
    )


# --- GCPCloudFunction label schema ---


@dataclass(frozen=True)
class GCPLabelToCloudFunctionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPLabelToCloudFunctionRel(CartographyRelSchema):
    """(:GCPCloudFunction)-[:LABELED]->(:GCPLabel)"""

    target_node_label: str = "GCPCloudFunction"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LABELED"
    properties: GCPLabelToCloudFunctionRelProperties = (
        GCPLabelToCloudFunctionRelProperties()
    )


@dataclass(frozen=True)
class GCPCloudFunctionGCPLabelSchema(CartographyNodeSchema):
    """
    GCPLabel nodes sourced from GCPCloudFunction resources.
    """

    label: str = "GCPLabel"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Label"])
    properties: GCPLabelNodeProperties = GCPLabelNodeProperties()
    sub_resource_relationship: GCPLabelToProjectRel = GCPLabelToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPLabelToCloudFunctionRel()],
    )
