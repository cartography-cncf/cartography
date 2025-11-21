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
class TrivyPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    installed_version: PropertyRef = PropertyRef("InstalledVersion")
    name: PropertyRef = PropertyRef("PkgName")
    version: PropertyRef = PropertyRef("InstalledVersion")
    class_name: PropertyRef = PropertyRef("Class")
    type: PropertyRef = PropertyRef("Type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyPackageToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyPackageToImage(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: TrivyPackageToImageRelProperties = TrivyPackageToImageRelProperties()


@dataclass(frozen=True)
class TrivyPackageToFindingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyPackageToFinding(CartographyRelSchema):
    target_node_label: str = "TrivyImageFinding"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FindingId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "AFFECTS"
    properties: TrivyPackageToFindingRelProperties = (
        TrivyPackageToFindingRelProperties()
    )


@dataclass(frozen=True)
class TrivyPackageSchema(CartographyNodeSchema):
    label: str = "Package"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["TrivyPackage"])
    properties: TrivyPackageNodeProperties = TrivyPackageNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TrivyPackageToImage(),
            TrivyPackageToFinding(),
        ],
    )
