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
class EndorLabsFindingNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uuid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace")
    summary: PropertyRef = PropertyRef("summary")
    level: PropertyRef = PropertyRef("level", extra_index=True)
    finding_categories: PropertyRef = PropertyRef("finding_categories")
    finding_tags: PropertyRef = PropertyRef("finding_tags")
    target_dependency_name: PropertyRef = PropertyRef("target_dependency_name")
    target_dependency_version: PropertyRef = PropertyRef("target_dependency_version")
    target_dependency_package_name: PropertyRef = PropertyRef(
        "target_dependency_package_name",
    )
    proposed_version: PropertyRef = PropertyRef("proposed_version")
    remediation: PropertyRef = PropertyRef("remediation")
    remediation_action: PropertyRef = PropertyRef("remediation_action")
    project_uuid: PropertyRef = PropertyRef("project_uuid")
    cve_id: PropertyRef = PropertyRef("cve_id", extra_index=True)
    create_time: PropertyRef = PropertyRef("create_time")


@dataclass(frozen=True)
class EndorLabsFindingToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsFindingToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "EndorLabsNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NAMESPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EndorLabsFindingToNamespaceRelProperties = (
        EndorLabsFindingToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class EndorLabsFindingToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsFindingToProjectRel(CartographyRelSchema):
    target_node_label: str = "EndorLabsProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_uuid")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: EndorLabsFindingToProjectRelProperties = (
        EndorLabsFindingToProjectRelProperties()
    )


@dataclass(frozen=True)
class EndorLabsFindingToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsFindingToCVERel(CartographyRelSchema):
    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LINKED_TO"
    properties: EndorLabsFindingToCVERelProperties = (
        EndorLabsFindingToCVERelProperties()
    )


@dataclass(frozen=True)
class EndorLabsFindingSchema(CartographyNodeSchema):
    label: str = "EndorLabsFinding"
    properties: EndorLabsFindingNodeProperties = EndorLabsFindingNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk"])
    sub_resource_relationship: EndorLabsFindingToNamespaceRel = (
        EndorLabsFindingToNamespaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            EndorLabsFindingToProjectRel(),
            EndorLabsFindingToCVERel(),
        ],
    )
