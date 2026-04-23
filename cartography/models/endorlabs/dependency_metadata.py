from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EndorLabsDependencyMetadataNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uuid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace")
    direct: PropertyRef = PropertyRef("direct")
    reachable: PropertyRef = PropertyRef("reachable")
    scope: PropertyRef = PropertyRef("scope")
    project_uuid: PropertyRef = PropertyRef("project_uuid")
    importer_uuid: PropertyRef = PropertyRef("importer_uuid")
    dependency_name: PropertyRef = PropertyRef("dependency_name")


@dataclass(frozen=True)
class EndorLabsDependencyMetadataToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsDependencyMetadataToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "EndorLabsNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NAMESPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EndorLabsDependencyMetadataToNamespaceRelProperties = (
        EndorLabsDependencyMetadataToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class EndorLabsDependencyMetadataToImporterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsDependencyMetadataToImporterRel(CartographyRelSchema):
    target_node_label: str = "EndorLabsPackageVersion"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("importer_uuid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMPORTED_BY"
    properties: EndorLabsDependencyMetadataToImporterRelProperties = (
        EndorLabsDependencyMetadataToImporterRelProperties()
    )


@dataclass(frozen=True)
class EndorLabsDependencyMetadataToDependencyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsDependencyMetadataToDependencyRel(CartographyRelSchema):
    target_node_label: str = "EndorLabsPackageVersion"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dependency_package_version_uuid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPENDS_ON"
    properties: EndorLabsDependencyMetadataToDependencyRelProperties = (
        EndorLabsDependencyMetadataToDependencyRelProperties()
    )


@dataclass(frozen=True)
class EndorLabsDependencyMetadataSchema(CartographyNodeSchema):
    label: str = "EndorLabsDependencyMetadata"
    properties: EndorLabsDependencyMetadataNodeProperties = (
        EndorLabsDependencyMetadataNodeProperties()
    )
    sub_resource_relationship: EndorLabsDependencyMetadataToNamespaceRel = (
        EndorLabsDependencyMetadataToNamespaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            EndorLabsDependencyMetadataToImporterRel(),
            EndorLabsDependencyMetadataToDependencyRel(),
        ],
    )
