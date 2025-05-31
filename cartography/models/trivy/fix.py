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
class TrivyFixNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    version: PropertyRef = PropertyRef("FixedVersion")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFixToPackageRelProperties(CartographyRelProperties):
    version: PropertyRef = PropertyRef("FixedVersion")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFixToPackage(CartographyRelSchema):
    target_node_label: str = "Package"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PackageId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SHOULD_UPDATE_TO"
    properties: TrivyFixToPackageRelProperties = TrivyFixToPackageRelProperties()


@dataclass(frozen=True)
class TrivyFixToFindingRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TrivyFixToFinding(CartographyRelSchema):
    target_node_label: str = "TrivyImageFinding"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FindingId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: TrivyFixToFindingRelProperties = TrivyFixToFindingRelProperties()


@dataclass(frozen=True)
class TrivyFixSchema(CartographyNodeSchema):
    label: str = "TrivyFix"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Fix"])
    properties: TrivyFixNodeProperties = TrivyFixNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            TrivyFixToPackage(),
            TrivyFixToFinding(),
        ],
    )
