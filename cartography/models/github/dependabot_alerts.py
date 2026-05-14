from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitHubDependabotAlertNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    number: PropertyRef = PropertyRef("number", extra_index=True)
    state: PropertyRef = PropertyRef("state", extra_index=True)
    url: PropertyRef = PropertyRef("url")
    html_url: PropertyRef = PropertyRef("html_url")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    dismissed_at: PropertyRef = PropertyRef("dismissed_at")
    dismissed_reason: PropertyRef = PropertyRef("dismissed_reason")
    dismissed_comment: PropertyRef = PropertyRef("dismissed_comment")
    fixed_at: PropertyRef = PropertyRef("fixed_at")
    dependency_package_ecosystem: PropertyRef = PropertyRef(
        "dependency_package_ecosystem",
        extra_index=True,
    )
    dependency_package_name: PropertyRef = PropertyRef(
        "dependency_package_name",
        extra_index=True,
    )
    dependency_manifest_path: PropertyRef = PropertyRef(
        "dependency_manifest_path",
        extra_index=True,
    )
    dependency_scope: PropertyRef = PropertyRef("dependency_scope")
    vulnerable_version_range: PropertyRef = PropertyRef("vulnerable_version_range")
    first_patched_version: PropertyRef = PropertyRef("first_patched_version")
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    advisory_ghsa_id: PropertyRef = PropertyRef("advisory_ghsa_id", extra_index=True)
    advisory_cve_id: PropertyRef = PropertyRef("advisory_cve_id", extra_index=True)
    cve_id: PropertyRef = PropertyRef("advisory_cve_id", extra_index=True)
    has_cve: PropertyRef = PropertyRef("has_cve")
    advisory_summary: PropertyRef = PropertyRef("advisory_summary")
    advisory_description: PropertyRef = PropertyRef("advisory_description")
    advisory_published_at: PropertyRef = PropertyRef("advisory_published_at")
    advisory_updated_at: PropertyRef = PropertyRef("advisory_updated_at")
    advisory_withdrawn_at: PropertyRef = PropertyRef("advisory_withdrawn_at")
    cvss_score: PropertyRef = PropertyRef("cvss_score")
    cvss_vector_string: PropertyRef = PropertyRef("cvss_vector_string")
    cvss_v3_score: PropertyRef = PropertyRef("cvss_v3_score")
    cvss_v3_vector_string: PropertyRef = PropertyRef("cvss_v3_vector_string")
    cvss_v4_score: PropertyRef = PropertyRef("cvss_v4_score")
    cvss_v4_vector_string: PropertyRef = PropertyRef("cvss_v4_vector_string")
    epss_percentage: PropertyRef = PropertyRef("epss_percentage")
    epss_percentile: PropertyRef = PropertyRef("epss_percentile")
    cwe_ids: PropertyRef = PropertyRef("cwe_ids")
    identifiers: PropertyRef = PropertyRef("identifiers")
    references: PropertyRef = PropertyRef("references")
    repository_url: PropertyRef = PropertyRef("repository_url", extra_index=True)
    repository_name: PropertyRef = PropertyRef("repository_name")
    repository_full_name: PropertyRef = PropertyRef("repository_full_name")


@dataclass(frozen=True)
class GitHubDependabotAlertRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubDependabotAlertToOrgRel(CartographyRelSchema):
    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubDependabotAlertRelProperties = (
        GitHubDependabotAlertRelProperties()
    )


@dataclass(frozen=True)
class GitHubDependabotAlertToRepoRel(CartographyRelSchema):
    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: GitHubDependabotAlertRelProperties = (
        GitHubDependabotAlertRelProperties()
    )


@dataclass(frozen=True)
class GitHubDependabotAlertDismissedByUserRel(CartographyRelSchema):
    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("dismissed_by_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DISMISSED_BY"
    properties: GitHubDependabotAlertRelProperties = (
        GitHubDependabotAlertRelProperties()
    )


@dataclass(frozen=True)
class GitHubDependabotAlertAssignedToUserRel(CartographyRelSchema):
    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("assignee_user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSIGNED_TO"
    properties: GitHubDependabotAlertRelProperties = (
        GitHubDependabotAlertRelProperties()
    )


@dataclass(frozen=True)
class GitHubDependabotAlertSchema(CartographyNodeSchema):
    label: str = "GitHubDependabotAlert"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "Risk",
            "SecurityIssue",
            ConditionalNodeLabel(label="CVE", conditions={"has_cve": "true"}),
        ]
    )
    properties: GitHubDependabotAlertNodeProperties = (
        GitHubDependabotAlertNodeProperties()
    )
    sub_resource_relationship: GitHubDependabotAlertToOrgRel = (
        GitHubDependabotAlertToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubDependabotAlertToRepoRel(),
            GitHubDependabotAlertDismissedByUserRel(),
            GitHubDependabotAlertAssignedToUserRel(),
        ]
    )


@dataclass(frozen=True)
class GitHubDependabotAlertUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("html_url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef("login", extra_index=True)
    is_site_admin: PropertyRef = PropertyRef("site_admin")
    type: PropertyRef = PropertyRef("type")


@dataclass(frozen=True)
class GitHubDependabotAlertUserSchema(CartographyNodeSchema):
    label: str = "GitHubUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: GitHubDependabotAlertUserNodeProperties = (
        GitHubDependabotAlertUserNodeProperties()
    )
    sub_resource_relationship: None = None
    other_relationships: None = None
