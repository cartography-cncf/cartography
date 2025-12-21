from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GitLabRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    url: PropertyRef = PropertyRef("url")


@dataclass(frozen=True)
class GitLabRepositorySchema(CartographyNodeSchema):
    label: str = "GitLabRepository"
    properties: GitLabRepositoryNodeProperties = GitLabRepositoryNodeProperties()
