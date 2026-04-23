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
class EndorLabsPackageVersionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uuid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace")
    ecosystem: PropertyRef = PropertyRef("ecosystem")
    package_name: PropertyRef = PropertyRef("package_name")
    version: PropertyRef = PropertyRef("version")
    purl: PropertyRef = PropertyRef("purl")
    normalized_id: PropertyRef = PropertyRef("normalized_id", extra_index=True)
    release_timestamp: PropertyRef = PropertyRef("release_timestamp")
    call_graph_available: PropertyRef = PropertyRef("call_graph_available")
    project_uuid: PropertyRef = PropertyRef("project_uuid")


@dataclass(frozen=True)
class EndorLabsPackageVersionToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsPackageVersionToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "EndorLabsNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NAMESPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EndorLabsPackageVersionToNamespaceRelProperties = (
        EndorLabsPackageVersionToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class EndorLabsPackageVersionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsPackageVersionToProjectRel(CartographyRelSchema):
    target_node_label: str = "EndorLabsProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_uuid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: EndorLabsPackageVersionToProjectRelProperties = (
        EndorLabsPackageVersionToProjectRelProperties()
    )


@dataclass(frozen=True)
class EndorLabsPackageVersionSchema(CartographyNodeSchema):
    label: str = "EndorLabsPackageVersion"
    properties: EndorLabsPackageVersionNodeProperties = (
        EndorLabsPackageVersionNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Dependency"])
    sub_resource_relationship: EndorLabsPackageVersionToNamespaceRel = (
        EndorLabsPackageVersionToNamespaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            EndorLabsPackageVersionToProjectRel(),
        ],
    )
