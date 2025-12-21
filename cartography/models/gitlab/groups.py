from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GitLabGroupNodeProperties(CartographyNodeProperties):
    """Properties for a GitLab group (namespace)."""

    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    numeric_id: PropertyRef = PropertyRef("numeric_id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    path: PropertyRef = PropertyRef("path")
    full_path: PropertyRef = PropertyRef("full_path")
    web_url: PropertyRef = PropertyRef("web_url")
    visibility: PropertyRef = PropertyRef("visibility")
    description: PropertyRef = PropertyRef("description")


@dataclass(frozen=True)
class GitLabGroupSchema(CartographyNodeSchema):
    label: str = "GitLabGroup"
    properties: GitLabGroupNodeProperties = GitLabGroupNodeProperties()

    @property
    def scoped_cleanup(self) -> bool:
        return False
