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
class CircleCIOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="CircleCI organization ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Organization display name.")
    slug: PropertyRef = PropertyRef(
        "slug", extra_index=True, description="CircleCI organization slug."
    )
    vcs_type: PropertyRef = PropertyRef(
        "vcs_type", description="Version control system type."
    )
    avatar_url: PropertyRef = PropertyRef(
        "avatar_url", description="URL of the organization avatar."
    )
    # VCS org login derived from the slug (e.g. "gh/acme" -> "acme"); only set
    # for GitHub-backed orgs, used to match the GitHubOrganization node.
    vcs_login: PropertyRef = PropertyRef(
        "vcs_login",
        description="GitHub organization login derived from the CircleCI slug.",
    )


@dataclass(frozen=True)
class CircleCIOrgToGitHubOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIOrganization)-[:ASSOCIATED_WITH]->(:GitHubOrganization), joined on login.
# Best-effort: only created if the GitHub org was ingested (OPTIONAL MATCH).
class CircleCIOrgToGitHubOrgRel(CartographyRelSchema):
    """The CircleCI organization is associated with a matching GitHub organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"username": PropertyRef("vcs_login")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: CircleCIOrgToGitHubOrgRelProperties = (
        CircleCIOrgToGitHubOrgRelProperties()
    )


@dataclass(frozen=True)
class CircleCIOrganizationSchema(CartographyNodeSchema):
    """A CircleCI organization with the canonical Tenant label."""

    label: str = "CircleCIOrganization"
    properties: CircleCIOrganizationNodeProperties = (
        CircleCIOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
    other_relationships: OtherRelationships = OtherRelationships(
        [CircleCIOrgToGitHubOrgRel()],
    )
