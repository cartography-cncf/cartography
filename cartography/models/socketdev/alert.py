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
class SocketDevAlertNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique Socket.dev alert identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    key: PropertyRef = PropertyRef(
        "key",
        description="Alert deduplication key.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="Socket.dev alert type.",
    )
    category: PropertyRef = PropertyRef(
        "category",
        extra_index=True,
        description="Alert category.",
    )
    severity: PropertyRef = PropertyRef(
        "severity",
        extra_index=True,
        description="Alert severity.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="Alert status.",
    )
    title: PropertyRef = PropertyRef(
        "title",
        description="Human-readable alert title.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Detailed alert description.",
    )
    dashboard_url: PropertyRef = PropertyRef(
        "dashboardUrl",
        description="URL for the alert in the Socket.dev dashboard.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt",
        description="Alert creation timestamp.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt",
        description="Alert last update timestamp.",
    )
    cleared_at: PropertyRef = PropertyRef(
        "clearedAt",
        description="Timestamp when the alert was cleared.",
    )
    # Vulnerability fields (populated when category == "vulnerability")
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        description="CVE identifier for a vulnerability alert.",
    )
    ghsa_id: PropertyRef = PropertyRef(
        "ghsa_id",
        extra_index=True,
        description="GitHub Security Advisory identifier.",
    )
    cvss_score: PropertyRef = PropertyRef(
        "cvss_score",
        description="CVSS score for a vulnerability alert.",
    )
    epss_score: PropertyRef = PropertyRef(
        "epss_score",
        description="EPSS probability score for a vulnerability alert.",
    )
    epss_percentile: PropertyRef = PropertyRef(
        "epss_percentile",
        description="EPSS percentile for a vulnerability alert.",
    )
    is_kev: PropertyRef = PropertyRef(
        "is_kev",
        description="Whether the vulnerability is in the CISA KEV catalog.",
    )
    first_patched_version: PropertyRef = PropertyRef(
        "first_patched_version",
        description="First package version that fixes the vulnerability.",
    )
    # Location fields (from first location entry)
    action: PropertyRef = PropertyRef(
        "action",
        description="Action assigned by the security policy.",
    )
    repo_slug: PropertyRef = PropertyRef(
        "repo_slug",
        description="Slug of the repository where the alert was found.",
    )
    repo_fullname: PropertyRef = PropertyRef(
        "repo_fullname",
        description="Full path of the repository where the alert was found.",
    )
    branch: PropertyRef = PropertyRef(
        "branch",
        description="Branch where the alert was found.",
    )
    artifact_name: PropertyRef = PropertyRef(
        "artifact_name",
        description="Affected package name.",
    )
    artifact_version: PropertyRef = PropertyRef(
        "artifact_version",
        description="Affected package version.",
    )
    artifact_type: PropertyRef = PropertyRef(
        "artifact_type",
        description="Affected package ecosystem.",
    )


@dataclass(frozen=True)
class SocketDevOrgToAlertRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevOrganization)-[:RESOURCE]->(:SocketDevAlert)
class SocketDevOrgToAlertRel(CartographyRelSchema):
    """Links a Socket.dev organization to one of its alerts."""

    target_node_label: str = "SocketDevOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SocketDevOrgToAlertRelProperties = SocketDevOrgToAlertRelProperties()


@dataclass(frozen=True)
class SocketDevAlertToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevAlert)-[:FOUND_IN]->(:SocketDevRepository)
class SocketDevAlertToRepoRel(CartographyRelSchema):
    """Links an alert to the Socket.dev repository where it was found."""

    target_node_label: str = "SocketDevRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("repo_fullname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SocketDevAlertToRepoRelProperties = SocketDevAlertToRepoRelProperties()


@dataclass(frozen=True)
class SocketDevAlertSchema(CartographyNodeSchema):
    """A security or supply chain alert reported by Socket.dev."""

    label: str = "SocketDevAlert"
    properties: SocketDevAlertNodeProperties = SocketDevAlertNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk", "SecurityIssue"])
    sub_resource_relationship: SocketDevOrgToAlertRel = SocketDevOrgToAlertRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SocketDevAlertToRepoRel(),
        ],
    )
