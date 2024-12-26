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
class GitHubTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('url')
    url: PropertyRef = PropertyRef('url')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    name: PropertyRef = PropertyRef('name', extra_index=True)
    description: PropertyRef = PropertyRef('description')


@dataclass(frozen=True)
class GitHubTeamToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubTeamAdminRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('ADMIN')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN"
    properties: GitHubTeamToRepoRelProperties = GitHubTeamToRepoRelProperties()


@dataclass(frozen=True)
class GitHubTeamMaintainRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('MAINTAIN')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MAINTAIN"
    properties: GitHubTeamToRepoRelProperties = GitHubTeamToRepoRelProperties()


@dataclass(frozen=True)
class GitHubTeamReadRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('READ')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "READ"
    properties: GitHubTeamToRepoRelProperties = GitHubTeamToRepoRelProperties()


@dataclass(frozen=True)
class GitHubTeamTriageRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('TRIAGE')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TRIAGE"
    properties: GitHubTeamToRepoRelProperties = GitHubTeamToRepoRelProperties()


@dataclass(frozen=True)
class GitHubTeamWriteRepoRel(CartographyRelSchema):
    target_node_label: str = 'GitHubRepository'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('WRITE')},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WRITE"
    properties: GitHubTeamToRepoRelProperties = GitHubTeamToRepoRelProperties()


@dataclass(frozen=True)
class GitHubTeamToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubTeamMaintainerUserRel(CartographyRelSchema):
    target_node_label: str = 'GitHubUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('MAINTAINER')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MAINTAINER"
    properties: GitHubTeamToUserRelProperties = GitHubTeamToUserRelProperties()


@dataclass(frozen=True)
class GitHubTeamMemberUserRel(CartographyRelSchema):
    target_node_label: str = 'GitHubUser'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('MEMBER')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER"
    properties: GitHubTeamToUserRelProperties = GitHubTeamToUserRelProperties()


@dataclass(frozen=True)
class GitHubTeamToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubTeamToOrganizationRel(CartographyRelSchema):
    target_node_label: str = 'GitHubOrganization'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('org_url', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubTeamToOrganizationRelProperties = GitHubTeamToOrganizationRelProperties()


@dataclass(frozen=True)
class GitHubTeamToChildTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubTeamChildTeamRel(CartographyRelSchema):
    target_node_label: str = 'GitHubTeam'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('MEMBER_OF_TEAM')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_TEAM"
    properties: GitHubTeamToChildTeamRelProperties = GitHubTeamToChildTeamRelProperties()


@dataclass(frozen=True)
class GitHubTeamSchema(CartographyNodeSchema):
    label: str = 'GitHubTeam'
    properties: GitHubTeamNodeProperties = GitHubTeamNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubTeamAdminRepoRel(),
            GitHubTeamMaintainRepoRel(),
            GitHubTeamReadRepoRel(),
            GitHubTeamTriageRepoRel(),
            GitHubTeamWriteRepoRel(),
            GitHubTeamMaintainerUserRel(),
            GitHubTeamMemberUserRel(),
            GitHubTeamChildTeamRel(),
        ],
    )
    sub_resource_relationship: GitHubTeamToOrganizationRel = GitHubTeamToOrganizationRel()
