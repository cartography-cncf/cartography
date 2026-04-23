from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EndorLabsProjectNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uuid")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    platform_source: PropertyRef = PropertyRef("platform_source")
    git_http_clone_url: PropertyRef = PropertyRef("git_http_clone_url")
    scan_state: PropertyRef = PropertyRef("scan_state")


@dataclass(frozen=True)
class EndorLabsProjectToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EndorLabsProjectToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "EndorLabsNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NAMESPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EndorLabsProjectToNamespaceRelProperties = (
        EndorLabsProjectToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class EndorLabsProjectSchema(CartographyNodeSchema):
    label: str = "EndorLabsProject"
    properties: EndorLabsProjectNodeProperties = EndorLabsProjectNodeProperties()
    sub_resource_relationship: EndorLabsProjectToNamespaceRel = (
        EndorLabsProjectToNamespaceRel()
    )
