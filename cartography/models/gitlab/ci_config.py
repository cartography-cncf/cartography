"""
GitLab CI/CD config schema.

Represents a project's `.gitlab-ci.yml`. The config also carries a
``REFERENCES_VARIABLE`` relationship to every project-level CI variable
whose ``key`` is referenced by the parsed pipeline. Modelled as a standard
relationship with a ``one_to_many=True`` matcher (not a MatchLink) — the
endpoints share the same sub-resource (the project), so the framework's
default cleanup tied to the config node is sufficient.
"""

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
# Config -> Project (sub-resource only — there is exactly one CIConfig per
# project, so the standard `RESOURCE` edge already encodes ownership and a
# separate `HAS_CI_CONFIG` semantic edge would be redundant.)
# =============================================================================


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


# =============================================================================
# CIConfig -> CI Variable (one_to_many, applied at config load time)
# =============================================================================


@dataclass(frozen=True)
class GitLabCIConfigToCIVariableRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabCIConfigToCIVariableRel(CartographyRelSchema):
    """
    `(:GitLabCIConfig)-[:REFERENCES_VARIABLE]->(:GitLabCIVariable)`

    Each config record carries a ``referenced_variable_ids`` list — the IDs
    of project variables whose ``key`` appears in the parsed pipeline. The
    matcher is ``one_to_many=True`` so a single config record creates one
    rel per referenced variable. Loaded as part of GitLabCIConfigSchema's
    other_relationships, so the rel's lifecycle follows the config node.
    """

    target_node_label: str = "GitLabCIVariable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("referenced_variable_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES_VARIABLE"
    properties: GitLabCIConfigToCIVariableRelProperties = (
        GitLabCIConfigToCIVariableRelProperties()
    )


@dataclass(frozen=True)
class GitLabCIConfigSchema(CartographyNodeSchema):
    label: str = "GitLabCIConfig"
    properties: GitLabCIConfigNodeProperties = GitLabCIConfigNodeProperties()
    sub_resource_relationship: GitLabCIConfigToProjectRel = GitLabCIConfigToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GitLabCIConfigToCIVariableRel()],
    )
