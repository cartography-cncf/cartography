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
class PackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("normalized_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    version: PropertyRef = PropertyRef("version")
    type: PropertyRef = PropertyRef("type")
    purl: PropertyRef = PropertyRef("purl")


@dataclass(frozen=True)
class PackageToNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:Package)-[:DETECTED_AS]->(:TrivyPackage)
@dataclass(frozen=True)
class PackageToTrivyPackageRel(CartographyRelSchema):
    target_node_label: str = "TrivyPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageToNodeRelProperties = PackageToNodeRelProperties()


# (:Package)-[:DETECTED_AS]->(:SyftPackage)
@dataclass(frozen=True)
class PackageToSyftPackageRel(CartographyRelSchema):
    target_node_label: str = "SyftPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageToNodeRelProperties = PackageToNodeRelProperties()


# (:Package)-[:DETECTED_AS]->(:Dependency)
@dataclass(frozen=True)
class PackageToDependencyRel(CartographyRelSchema):
    target_node_label: str = "Dependency"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"normalized_id": PropertyRef("normalized_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_AS"
    properties: PackageToNodeRelProperties = PackageToNodeRelProperties()


@dataclass(frozen=True)
class PackageSchema(CartographyNodeSchema):
    label: str = "Package"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: PackageNodeProperties = PackageNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            PackageToTrivyPackageRel(),
            PackageToSyftPackageRel(),
            PackageToDependencyRel(),
        ],
    )
