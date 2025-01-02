"""
This schema does not handle the org's relationships.  Those are handled by other schemas, for example:
* GitHubTeamSchema defines (GitHubOrganization)-[RESOURCE]->(GitHubTeam)
* GitHubUserSchema defines (GitHubUser)-[MEMBER_OF|ADMIN_OF|UNAFFILIATED]->(GitHubOrganization)
(There may be others, these are just two examples.)
"""
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GitHubOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('url')
    username: PropertyRef = PropertyRef('login', extra_index=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubOrganizationSchema(CartographyNodeSchema):
    label: str = 'GitHubOrganization'
    properties: GitHubOrganizationNodeProperties = GitHubOrganizationNodeProperties()
    other_relationships = None
    sub_resource_relationship = None
