from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CircleCIRepoPackagedFromMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the fallback PACKAGED_FROM relationship between Image and a code
    repository, produced by the CircleCI supply-chain matcher.

    Every edge carries match_method + confidence so consumers can filter at their own
    threshold; these are low-confidence fallback rungs that run below the SLSA provenance
    and Dockerfile-analysis ladder.
    """

    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Match method: "circleci_tag_revision" or "circleci_config_binding"
    match_method: PropertyRef = PropertyRef("match_method")
    confidence: PropertyRef = PropertyRef("confidence")


@dataclass(frozen=True)
class CircleCIGitHubRepoPackagedFromMatchLink(CartographyRelSchema):
    """
    MatchLink for CircleCI fallback matching: (Image)-[:PACKAGED_FROM]->(GitHubRepository).

    Matches Image.digest to the specific image identified by the matcher, and
    GitHubRepository.id to the (normalized) repo URL from the CircleCI run's vcs block.
    Keyed on GitHubRepository.id (the canonical HTTPS URL) to stay consistent with the
    existing GitHub provenance matcher.
    """

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("repo_url"),
        }
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "digest": PropertyRef("image_digest"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_FROM"
    properties: CircleCIRepoPackagedFromMatchLinkProperties = (
        CircleCIRepoPackagedFromMatchLinkProperties()
    )


@dataclass(frozen=True)
class CircleCIGitLabProjectPackagedFromMatchLink(CartographyRelSchema):
    """
    MatchLink for CircleCI fallback matching: (Image)-[:PACKAGED_FROM]->(GitLabProject).

    Matches Image.digest to the specific image identified by the matcher, and
    GitLabProject.web_url to the (normalized) repo URL from the CircleCI run's vcs block
    (GitLabProject.id is numeric, so web_url is the URL-bearing key, consistent with the
    existing GitLab provenance matcher).
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "web_url": PropertyRef("repo_url"),
        }
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "digest": PropertyRef("image_digest"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_FROM"
    properties: CircleCIRepoPackagedFromMatchLinkProperties = (
        CircleCIRepoPackagedFromMatchLinkProperties()
    )


@dataclass(frozen=True)
class ImagePackagedByCircleCIProjectMatchLinkProperties(CartographyRelProperties):
    """
    Properties for the PACKAGED_BY relationship between Image and CircleCIProject.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    match_method: PropertyRef = PropertyRef("match_method")


@dataclass(frozen=True)
class ImagePackagedByCircleCIProjectMatchLink(CartographyRelSchema):
    """
    MatchLink for the building project: (Image)-[:PACKAGED_BY]->(CircleCIProject).

    Emitted where a rung identifies the building CircleCI project (the /pipeline feed run
    reliably carries project_slug). Analogous to the GitHub ImagePackagedByWorkflowMatchLink;
    the PACKAGED_FROM edge to the repo follows either the matcher's own repo edge or the
    project's existing CircleCIProject-[:BUILDS]->repo hop.
    """

    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "slug": PropertyRef("project_slug"),
        }
    )
    source_node_label: str = "Image"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "digest": PropertyRef("image_digest"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PACKAGED_BY"
    properties: ImagePackagedByCircleCIProjectMatchLinkProperties = (
        ImagePackagedByCircleCIProjectMatchLinkProperties()
    )
