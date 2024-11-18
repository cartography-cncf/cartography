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
class FakeEmp2ToGitHubUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class FakeEmp2ToGitHubUser(CartographyRelSchema):
    target_node_label: str = 'GitHubUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'username': PropertyRef('github_username', fuzzy_and_ignore_case=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IDENTITY_GITHUB"
    properties: FakeEmp2ToGitHubUserRelProperties = FakeEmp2ToGitHubUserRelProperties()


@dataclass(frozen=True)
class FakeEmp2NodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    email: PropertyRef = PropertyRef('email')
    github_username: PropertyRef = PropertyRef('github_username')


@dataclass(frozen=True)
class FakeEmp2Schema(CartographyNodeSchema):
    label: str = 'FakeEmployee2'
    properties: FakeEmp2NodeProperties = FakeEmp2NodeProperties()
    other_relationships: OtherRelationships = OtherRelationships([
        FakeEmp2ToGitHubUser(),
    ])
