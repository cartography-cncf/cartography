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
class GithubRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    fullname: PropertyRef = PropertyRef("fullname")
    description: PropertyRef = PropertyRef("description")
    primarylanguage: PropertyRef = PropertyRef("primarylanguage")
    homepage: PropertyRef = PropertyRef("homepage")
    defaultbranch: PropertyRef = PropertyRef("defaultbranch")
    defaultbranchid: PropertyRef = PropertyRef("defaultbranchid")
    private: PropertyRef = PropertyRef("private")
    disabled: PropertyRef = PropertyRef("disabled")
    archived: PropertyRef = PropertyRef("archived")
    locked: PropertyRef = PropertyRef("locked")
    giturl: PropertyRef = PropertyRef("giturl")
    url: PropertyRef = PropertyRef("url")
    sshurl: PropertyRef = PropertyRef("sshurl")
    updatedat: PropertyRef = PropertyRef("updatedat")
    createdat: PropertyRef = PropertyRef("createdat")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GithubRepositoryToGitHubOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GithubRepositoryToGitHubOrganizationRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_id", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNER"
    properties: GithubRepositoryToGitHubOrganizationRelProperties = GithubRepositoryToGitHubOrganizationRelProperties()


@dataclass(frozen=True)
class GithubRepositorySchema(CartographyNodeSchema):
    label: str = "GitHubRepository"
    properties: GithubRepositoryNodeProperties = GithubRepositoryNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships([
        GithubRepositoryToGitHubOrganizationRel(),
    ])
