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


@dataclass(frozen=True)
class DockerScoutFixNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    version: PropertyRef = PropertyRef("fixed_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutFixToPackageRelProperties(CartographyRelProperties):
    version: PropertyRef = PropertyRef("fixed_by")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutFixToPackageRel(CartographyRelSchema):
    target_node_label: str = "DockerScoutPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PackageId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SHOULD_UPDATE_TO"
    properties: DockerScoutFixToPackageRelProperties = (
        DockerScoutFixToPackageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutFixToFindingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutFixToFindingRel(CartographyRelSchema):
    target_node_label: str = "DockerScoutFinding"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FindingId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: DockerScoutFixToFindingRelProperties = (
        DockerScoutFixToFindingRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutFixSchema(CartographyNodeSchema):
    label: str = "DockerScoutFix"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Fix"])
    properties: DockerScoutFixNodeProperties = DockerScoutFixNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DockerScoutFixToPackageRel(),
            DockerScoutFixToFindingRel(),
        ],
    )
