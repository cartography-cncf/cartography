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
    """
    Version-independent identity of a software package.

    The id format is `{type}|{namespace/}{normalized_name}`, i.e. the version-bearing
    `PackageVersion.id` minus its version segment. Both are produced by the helpers in
    cartography.intel.trivy.util so the two keys always agree on normalization.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Normalized name (PEP 503 for Python, lowercase elsewhere) so the same package
    # reported by different scanners resolves to a single node. This is the id segment
    # after the type, so it deliberately keeps the PURL namespace prefix when there is
    # one: `pkg:npm/%40types/node` gives name `@types/node`, not `node`. That is the
    # name the package is published under, and it keeps `name` aligned with `id`.
    # `namespace` below exposes the bare PURL namespace component (`@types`) for callers
    # that need the two apart.
    name: PropertyRef = PropertyRef("name")
    namespace: PropertyRef = PropertyRef("namespace")
    type: PropertyRef = PropertyRef("type")


@dataclass(frozen=True)
class PackageToPackageVersionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:Package)-[:HAS_VERSION]->(:PackageVersion)
@dataclass(frozen=True)
class PackageToPackageVersionRel(CartographyRelSchema):
    """
    Each Package carries a version_ids list of the PackageVersion ids it groups.
    """

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
    """
    Canonical, version-independent software package.

    Package is a pure aggregation node: every derived edge (DETECTED_AS, DEPLOYED,
    AFFECTS, SHOULD_UPDATE_TO, DEPENDS_ON) hangs off the PackageVersion nodes it
    groups via HAS_VERSION.
    """

    label: str = "Package"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([ONTOLOGY])
    properties: PackageNodeProperties = PackageNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            PackageToPackageVersionRel(),
        ],
    )
