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
from cartography.models.extra_labels import RISK
from cartography.models.ontology.labels import CVE
from cartography.models.ontology.labels import SECURITY_ISSUE
from cartography.models.ontology.labels import USER_ACCOUNT


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
        "severity",
        extra_index=True,
        description=(
            "Severity of the vulnerable version range that the alert matched, or "
            "the advisory's severity when GitHub omits it."
        ),
    )
    cve_id: PropertyRef = PropertyRef(
        "advisory_cve_id",
        extra_index=True,
        description="CVE identifier of the alert's advisory, when available.",
    )
    # DEPRECATED: copies of advisory-level fields, which GitHubSecurityAdvisory now
    # holds once per advisory. The alert keeps writing them so existing queries
    # work; they will be removed in v1.0.0.
    advisory_ghsa_id: PropertyRef = PropertyRef(
        "advisory_ghsa_id",
        extra_index=True,
        description=(
            "Deprecated. Read `advisory_ghsa_id` on the alert's "
            "`GitHubSecurityAdvisory`. Will be removed in v1.0.0."
        ),
    )
    advisory_cve_id: PropertyRef = PropertyRef(
        "advisory_cve_id",
        extra_index=True,
        description=(
            "Deprecated duplicate of `cve_id`. Read `cve_id` on the alert or on its "
            "`GitHubSecurityAdvisory`. Will be removed in v1.0.0."
        ),
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve",
        description=(
            "Deprecated. Read `has_cve` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    advisory_summary: PropertyRef = PropertyRef(
        "advisory_summary",
        description=(
            "Deprecated. Read `advisory_summary` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    advisory_description: PropertyRef = PropertyRef(
        "advisory_description",
        description=(
            "Deprecated. Read `advisory_description` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    advisory_published_at: PropertyRef = PropertyRef(
        "advisory_published_at",
        description=(
            "Deprecated. Read `advisory_published_at` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    advisory_updated_at: PropertyRef = PropertyRef(
        "advisory_updated_at",
        description=(
            "Deprecated. Read `advisory_updated_at` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    advisory_withdrawn_at: PropertyRef = PropertyRef(
        "advisory_withdrawn_at",
        description=(
            "Deprecated. Read `advisory_withdrawn_at` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    cvss_score: PropertyRef = PropertyRef(
        "cvss_score",
        description=(
            "Deprecated. Read `cvss_score` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    cvss_vector_string: PropertyRef = PropertyRef(
        "cvss_vector_string",
        description=(
            "Deprecated. Read `cvss_vector_string` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    cvss_v3_score: PropertyRef = PropertyRef(
        "cvss_v3_score",
        description=(
            "Deprecated. Read `cvss_v3_score` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    cvss_v3_vector_string: PropertyRef = PropertyRef(
        "cvss_v3_vector_string",
        description=(
            "Deprecated. Read `cvss_v3_vector_string` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    cvss_v4_score: PropertyRef = PropertyRef(
        "cvss_v4_score",
        description=(
            "Deprecated. Read `cvss_v4_score` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    cvss_v4_vector_string: PropertyRef = PropertyRef(
        "cvss_v4_vector_string",
        description=(
            "Deprecated. Read `cvss_v4_vector_string` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    epss_percentage: PropertyRef = PropertyRef(
        "epss_percentage",
        description=(
            "Deprecated. Read `epss_percentage` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    epss_percentile: PropertyRef = PropertyRef(
        "epss_percentile",
        description=(
            "Deprecated. Read `epss_percentile` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    cwe_ids: PropertyRef = PropertyRef(
        "cwe_ids",
        description=(
            "Deprecated. Read `cwe_ids` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    identifiers: PropertyRef = PropertyRef(
        "identifiers",
        description=(
            "Deprecated. Read `identifiers` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
    )
    references: PropertyRef = PropertyRef(
        "references",
        description=(
            "Deprecated. Read `references` on the alert's `GitHubSecurityAdvisory`. "
            "Will be removed in v1.0.0."
        ),
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
class GitHubDependabotAlertToSecurityAdvisoryRel(CartographyRelSchema):
    """Links a Dependabot alert to the security advisory it reports."""

    target_node_label: str = "GitHubSecurityAdvisory"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("advisory_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_VULNERABILITY"
    properties: GitHubDependabotAlertRelProperties = (
        GitHubDependabotAlertRelProperties()
    )


@dataclass(frozen=True)
class GitHubDependabotAlertSchema(CartographyNodeSchema):
    """A GitHub Dependabot vulnerability alert for a repository dependency.

    An alert is not labeled [`CVE`](#ontology-cve). The `GitHubSecurityAdvisory` it
    links to through `HAS_VULNERABILITY` carries that label, so each CVE is one node
    in each organization rather than one node per alert. The alert still writes its
    advisory-level fields, which are deprecated and will be removed in v1.0.0.
    """

    label: str = "GitHubDependabotAlert"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            RISK,
            SECURITY_ISSUE,
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
            GitHubDependabotAlertToSecurityAdvisoryRel(),
        ]
    )


@dataclass(frozen=True)
class GitHubSecurityAdvisoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "`GHSA|<organization URL>|<GHSA identifier>`: the advisory as reported "
            "to one organization."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    advisory_ghsa_id: PropertyRef = PropertyRef(
        "advisory_ghsa_id",
        extra_index=True,
        description="GitHub Security Advisory (GHSA) identifier.",
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier of the advisory. Unset when the advisory has no CVE.",
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve",
        description="`true` when the advisory has a CVE identifier, so the node is labeled `:CVE`.",
    )
    advisory_summary: PropertyRef = PropertyRef(
        "advisory_summary", description="Short summary of the advisory."
    )
    advisory_description: PropertyRef = PropertyRef(
        "advisory_description", description="Full description of the advisory."
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
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Severity of the advisory: `low`, `medium`, `high`, or `critical`.",
    )
    cvss_score: PropertyRef = PropertyRef(
        "cvss_score", description="Primary CVSS score of the advisory."
    )
    cvss_vector_string: PropertyRef = PropertyRef(
        "cvss_vector_string", description="Primary CVSS vector of the advisory."
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
        "epss_percentage",
        description="Exploit Prediction Scoring System (EPSS) probability reported by GitHub.",
    )
    epss_percentile: PropertyRef = PropertyRef(
        "epss_percentile", description="EPSS percentile reported by GitHub."
    )
    cwe_ids: PropertyRef = PropertyRef(
        "cwe_ids", description="CWE identifiers of the advisory."
    )
    identifiers: PropertyRef = PropertyRef(
        "identifiers",
        description="Identifiers of the advisory, including its GHSA and CVE values.",
    )
    references: PropertyRef = PropertyRef(
        "references", description="Reference URLs of the advisory."
    )


@dataclass(frozen=True)
class GitHubSecurityAdvisoryToOrgRel(CartographyRelSchema):
    """Scopes a security advisory to the organization whose alerts report it."""

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
class GitHubSecurityAdvisorySchema(CartographyNodeSchema):
    """A [GitHub security advisory](https://docs.github.com/en/rest/dependabot/alerts) that Dependabot alerts report.

    Holds the advisory data that is the same for every alert of the advisory, so each
    `GitHubDependabotAlert` adds only what is specific to one repository dependency.
    There is one node per GHSA identifier in each organization, so an organization's
    cleanup never deletes an advisory that another organization's alerts link to.
    Labeled [`CVE`](#ontology-cve) when the advisory has a CVE identifier, so
    `CVEMetadata` enriches one node per CVE in each organization rather than one per
    alert.
    """

    label: str = "GitHubSecurityAdvisory"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([CVE.when(has_cve="true")])
    properties: GitHubSecurityAdvisoryNodeProperties = (
        GitHubSecurityAdvisoryNodeProperties()
    )
    sub_resource_relationship: GitHubSecurityAdvisoryToOrgRel = (
        GitHubSecurityAdvisoryToOrgRel()
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
    properties: GitHubDependabotAlertUserNodeProperties = (
        GitHubDependabotAlertUserNodeProperties()
    )
    sub_resource_relationship: None = None
    other_relationships: None = None
