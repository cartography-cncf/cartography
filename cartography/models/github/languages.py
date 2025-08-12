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
class ProgrammingLanguageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProgrammingLanguageToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProgrammingLanguageToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repo_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LANGUAGE"
    properties: ProgrammingLanguageToRepositoryRelProperties = ProgrammingLanguageToRepositoryRelProperties()


@dataclass(frozen=True)
class ProgrammingLanguageSchema(CartographyNodeSchema):
    label: str = "ProgrammingLanguage"
    properties: ProgrammingLanguageNodeProperties = ProgrammingLanguageNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships([
        ProgrammingLanguageToRepositoryRel(),
    ]) 