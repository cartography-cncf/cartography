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
class PythonLibraryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    version: PropertyRef = PropertyRef("version")
    specifier: PropertyRef = PropertyRef("specifier")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PythonLibraryToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PythonLibraryToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_url")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REQUIRES"
    properties: PythonLibraryToRepositoryRelProperties = PythonLibraryToRepositoryRelProperties()


@dataclass(frozen=True)
class PythonLibrarySchema(CartographyNodeSchema):
    label: str = "PythonLibrary"
    properties: PythonLibraryNodeProperties = PythonLibraryNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships([
        PythonLibraryToRepositoryRel(),
    ]) 