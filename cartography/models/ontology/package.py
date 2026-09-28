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
from cartography.models.ontology.labels import ONTOLOGY


@dataclass(frozen=True)
class PackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Version-independent normalized identifier in `{type}|{namespace/}{name}` format.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        description="Normalized package name, including its namespace prefix when present.",
    )
    namespace: PropertyRef = PropertyRef(
        "namespace",
        description="Package URL namespace when present.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Package ecosystem or type.",
    )


@dataclass(frozen=True)
class PackageToPackageVersionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PackageToPackageVersionRel(CartographyRelSchema):
    """A canonical package groups an observed package version."""

    target_node_label: str = "PackageVersion"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("version_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_VERSION"
    properties: PackageToPackageVersionRelProperties = (
        PackageToPackageVersionRelProperties()
    )


@dataclass(frozen=True)
class PackageSchema(CartographyNodeSchema):
    """A canonical, version-independent software package aggregated across inventory sources."""

    label: str = "Package"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([ONTOLOGY])
    properties: PackageNodeProperties = PackageNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            PackageToPackageVersionRel(),
        ],
    )
