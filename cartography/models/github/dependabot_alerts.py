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
    id: PropertyRef = PropertyRef(
        "id", description="Dependabot alert web URL used as the stable identifier."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    number: PropertyRef = PropertyRef(
        "number",
        extra_index=True,
        description="Repository-local Dependabot alert number.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        extra_index=True,
        description="Alert state: `open`, `fixed`, `dismissed`, or `auto_dismissed`.",
    )
    url: PropertyRef = PropertyRef(
        "url", description="GitHub REST API URL for the alert."
    )
    html_url: PropertyRef = PropertyRef(
        "html_url", description="GitHub web URL for the alert."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the alert was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the alert was last updated."
    )
    dismissed_at: PropertyRef = PropertyRef(
        "dismissed_at", description="Timestamp when the alert was dismissed."
    )
    dismissed_reason: PropertyRef = PropertyRef(
        "dismissed_reason", description="GitHub dismissal reason, when applicable."
    )
    dismissed_comment: PropertyRef = PropertyRef(
        "dismissed_comment", description="GitHub dismissal comment, when applicable."
    )
    fixed_at: PropertyRef = PropertyRef(
        "fixed_at", description="Timestamp when the alert was fixed."
    )
    dependency_package_ecosystem: PropertyRef = PropertyRef(
        "dependency_package_ecosystem",
        extra_index=True,
        description="Package ecosystem of the vulnerable dependency.",
    )
    dependency_package_name: PropertyRef = PropertyRef(
        "dependency_package_name",
        extra_index=True,
        description="Name of the vulnerable package.",
    )
    dependency_manifest_path: PropertyRef = PropertyRef(
        "dependency_manifest_path",
        extra_index=True,
        description="Manifest path where GitHub found the dependency.",
    )
    dependency_scope: PropertyRef = PropertyRef(
        "dependency_scope", description="Dependency scope reported by GitHub."
    )
    vulnerable_version_range: PropertyRef = PropertyRef(
        "vulnerable_version_range",
        description="Affected package version range.",
    )
    first_patched_version: PropertyRef = PropertyRef(
        "first_patched_version",
        description="First patched package version, when known.",
    )
    severity: PropertyRef = PropertyRef(
        "severity", extra_index=True, description="Advisory severity."
    )
    advisory_ghsa_id: PropertyRef = PropertyRef(
        "advisory_ghsa_id",
        extra_index=True,
        description="GitHub Security Advisory identifier.",
    )
    advisory_cve_id: PropertyRef = PropertyRef(
        "advisory_cve_id",
        extra_index=True,
        description="CVE identifier associated with the advisory, when available.",
    )
    cve_id: PropertyRef = PropertyRef(
        "advisory_cve_id",
        extra_index=True,
        description="Standard CVE identifier mirrored from `advisory_cve_id`.",
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve", description="Whether the advisory includes a CVE identifier."
    )
    advisory_summary: PropertyRef = PropertyRef(
        "advisory_summary", description="GitHub Security Advisory summary."
    )
    advisory_description: PropertyRef = PropertyRef(
        "advisory_description", description="GitHub Security Advisory description."
    )
    advisory_published_at: PropertyRef = PropertyRef(
        "advisory_published_at",
        description="Timestamp when the advisory was published.",
    )
    advisory_updated_at: PropertyRef = PropertyRef(
        "advisory_updated_at",
        description="Timestamp when the advisory was last updated.",
    )
    advisory_withdrawn_at: PropertyRef = PropertyRef(
        "advisory_withdrawn_at",
        description="Timestamp when the advisory was withdrawn, when applicable.",
    )
    cvss_score: PropertyRef = PropertyRef(
        "cvss_score", description="Primary CVSS score reported for the advisory."
    )
    cvss_vector_string: PropertyRef = PropertyRef(
        "cvss_vector_string",
        description="Primary CVSS vector reported for the advisory.",
    )
    cvss_v3_score: PropertyRef = PropertyRef(
        "cvss_v3_score", description="CVSS v3 score, when available."
    )
    cvss_v3_vector_string: PropertyRef = PropertyRef(
        "cvss_v3_vector_string", description="CVSS v3 vector, when available."
    )
    cvss_v4_score: PropertyRef = PropertyRef(
        "cvss_v4_score", description="CVSS v4 score, when available."
    )
    cvss_v4_vector_string: PropertyRef = PropertyRef(
        "cvss_v4_vector_string", description="CVSS v4 vector, when available."
    )
    epss_percentage: PropertyRef = PropertyRef(
        "epss_percentage", description="EPSS probability reported by GitHub."
    )
    epss_percentile: PropertyRef = PropertyRef(
        "epss_percentile", description="EPSS percentile reported by GitHub."
    )
    cwe_ids: PropertyRef = PropertyRef(
        "cwe_ids", description="CWE identifiers associated with the advisory."
    )
    identifiers: PropertyRef = PropertyRef(
        "identifiers",
        description="Advisory identifiers, including GHSA and CVE values.",
    )
    references: PropertyRef = PropertyRef(
        "references", description="Reference URLs associated with the advisory."
    )
    repository_url: PropertyRef = PropertyRef(
        "repository_url",
        extra_index=True,
        description="URL of the affected repository.",
    )
    repository_name: PropertyRef = PropertyRef(
        "repository_name", description="Name of the affected repository."
    )
    repository_full_name: PropertyRef = PropertyRef(
        "repository_full_name",
        description="Affected repository name in `owner/name` form.",
    )


@dataclass(frozen=True)
class GitHubDependabotAlertRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubDependabotAlertToOrgRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

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
    """Links a Dependabot alert to its GitHub repository."""

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
    """Links a Dependabot alert to the GitHub user who dismissed it."""

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
    """Links a Dependabot alert to an assigned GitHub user."""

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
    """A GitHub Dependabot vulnerability alert for a repository dependency."""

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
    id: PropertyRef = PropertyRef("html_url", description="GitHub user profile URL.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    username: PropertyRef = PropertyRef(
        "login", extra_index=True, description="GitHub user login."
    )
    is_site_admin: PropertyRef = PropertyRef(
        "site_admin",
        description="Whether the user is a GitHub site administrator.",
    )
    type: PropertyRef = PropertyRef("type", description="GitHub account type.")


@dataclass(frozen=True)
class GitHubDependabotAlertUserSchema(CartographyNodeSchema):
    """A user account in GitHub."""

    label: str = "GitHubUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: GitHubDependabotAlertUserNodeProperties = (
        GitHubDependabotAlertUserNodeProperties()
    )
    sub_resource_relationship: None = None
    other_relationships: None = None
