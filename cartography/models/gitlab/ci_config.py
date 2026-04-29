"""
GitLab CI/CD config schema.

Represents a project's `.gitlab-ci.yml`. The config also carries a scoped
MatchLink that connects it to the project-level CI/CD variables it
references at runtime via `$VAR` / `${VAR}` patterns.
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitLabCIConfigNodeProperties(CartographyNodeProperties):
    """Properties for a `.gitlab-ci.yml` config node."""

    id: PropertyRef = PropertyRef("id")  # Composite: f"{project_id}:{file_path}"
    project_id: PropertyRef = PropertyRef("project_id", extra_index=True)
    file_path: PropertyRef = PropertyRef("file_path")
    is_valid: PropertyRef = PropertyRef("is_valid")
    is_merged: PropertyRef = PropertyRef("is_merged")
    job_count: PropertyRef = PropertyRef("job_count")
    stages: PropertyRef = PropertyRef("stages")
    trigger_rules: PropertyRef = PropertyRef("trigger_rules")
    referenced_variable_keys: PropertyRef = PropertyRef("referenced_variable_keys")
    referenced_protected_variables: PropertyRef = PropertyRef(
        "referenced_protected_variables"
    )
    default_image: PropertyRef = PropertyRef("default_image")
    has_includes: PropertyRef = PropertyRef("has_includes")
    include_count: PropertyRef = PropertyRef("include_count")
    gitlab_url: PropertyRef = PropertyRef("gitlab_url", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# =============================================================================
# Config <-> Project (sub-resource and HAS_CI_CONFIG)
# =============================================================================


@dataclass(frozen=True)
class GitLabProjectHasCIConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectHasCIConfigRel(CartographyRelSchema):
    """`(:GitLabProject)-[:HAS_CI_CONFIG]->(:GitLabCIConfig)`."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CI_CONFIG"
    properties: GitLabProjectHasCIConfigRelProperties = (
        GitLabProjectHasCIConfigRelProperties()
    )


@dataclass(frozen=True)
class GitLabCIConfigToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabCIConfigToProjectRel(CartographyRelSchema):
    """Sub-resource relationship — scoped to GitLabProject."""

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabCIConfigToProjectRelProperties = (
        GitLabCIConfigToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabCIConfigSchema(CartographyNodeSchema):
    label: str = "GitLabCIConfig"
    properties: GitLabCIConfigNodeProperties = GitLabCIConfigNodeProperties()
    sub_resource_relationship: GitLabCIConfigToProjectRel = (
        GitLabCIConfigToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitLabProjectHasCIConfigRel()],
    )


# =============================================================================
# CIConfig -> CI Variable MatchLink (project-scoped)
# =============================================================================


@dataclass(frozen=True)
class GitLabCIConfigToCIVariableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id", set_in_kwargs=True
    )


@dataclass(frozen=True)
class GitLabCIConfigToCIVariableMatchLink(CartographyRelSchema):
    """
    `(:GitLabCIConfig)-[:REFERENCES_VARIABLE]->(:GitLabCIVariable)`

    Linked when the config's `referenced_variable_keys` contains the
    variable's `key`. Scoped to the parent GitLabProject.
    """

    source_node_label: str = "GitLabCIConfig"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("config_id")},
    )
    target_node_label: str = "GitLabCIVariable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("variable_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES_VARIABLE"
    properties: GitLabCIConfigToCIVariableRelProperties = (
        GitLabCIConfigToCIVariableRelProperties()
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="GitLabProject",
        target_node_matcher=make_target_node_matcher(
            {
                "id": PropertyRef("_sub_resource_id", set_in_kwargs=True),
                "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
            },
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="GitLabProject",
        target_node_matcher=make_target_node_matcher(
            {
                "id": PropertyRef("_sub_resource_id", set_in_kwargs=True),
                "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
            },
        ),
        direction=LinkDirection.INWARD,
        rel_label="HAS_CI_VARIABLE",
    )
