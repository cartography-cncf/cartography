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
from cartography.models.ontology.labels import CVE
from cartography.models.ontology.labels import SECURITY_ISSUE


@dataclass(frozen=True)
class SnykIssueNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Snyk issue.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    title: PropertyRef = PropertyRef(
        "title", extra_index=True, description="Short issue title."
    )
    cve_id: PropertyRef = PropertyRef(
        "cve_id", extra_index=True, description="Primary CVE identifier, if present."
    )
    has_cve: PropertyRef = PropertyRef(
        "has_cve", description="Whether this issue is backed by a CVE identifier."
    )
    severity: PropertyRef = PropertyRef("severity", description="Snyk severity.")
    status: PropertyRef = PropertyRef(
        "status", description="Current Snyk issue status."
    )
    ignored: PropertyRef = PropertyRef(
        "ignored", description="Whether this issue is currently ignored in Snyk."
    )
    cvss_score: PropertyRef = PropertyRef("cvss_score", description="CVSS score.")
    exploit_maturity: PropertyRef = PropertyRef(
        "exploit_maturity", description="Snyk exploit maturity value."
    )
    package_name: PropertyRef = PropertyRef(
        "package_name", extra_index=True, description="Affected package name."
    )
    package_version: PropertyRef = PropertyRef(
        "package_version", description="Affected package version."
    )
    is_upgradable: PropertyRef = PropertyRef(
        "is_upgradable", description="Whether Snyk reports an upgrade path."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Issue creation time."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Issue update time."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Issue description."
    )
    identifiers: PropertyRef = PropertyRef(
        "identifiers", description="Provider identifiers associated with the issue."
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        extra_index=True,
        description="Snyk project where this issue appears.",
    )
    org_id: PropertyRef = PropertyRef(
        "org_id", description="ID of the owning Snyk org."
    )


@dataclass(frozen=True)
class SnykIssueToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnykIssueToOrgRel(CartographyRelSchema):
    """Connects a Snyk organization to one of its issues."""

    target_node_label: str = "SnykOrg"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnykIssueToOrgRelProperties = SnykIssueToOrgRelProperties()


@dataclass(frozen=True)
class SnykIssueToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnykIssueToProjectRel(CartographyRelSchema):
    """Links a Snyk issue to the Snyk project where it was observed."""

    target_node_label: str = "SnykProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SnykIssueToProjectRelProperties = SnykIssueToProjectRelProperties()


@dataclass(frozen=True)
class SnykIssueToCVERelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SnykIssueToCVERel(CartographyRelSchema):
    """Links a CVE to the Snyk issue that reported it."""

    target_node_label: str = "CVE"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cve_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "LINKED_TO"
    properties: SnykIssueToCVERelProperties = SnykIssueToCVERelProperties()


@dataclass(frozen=True)
class SnykIssueSchema(CartographyNodeSchema):
    """A vulnerability or advisory issue reported by Snyk."""

    label: str = "SnykIssue"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            SECURITY_ISSUE.when(has_cve="false"),
            CVE.when(has_cve="true"),
        ],
    )
    properties: SnykIssueNodeProperties = SnykIssueNodeProperties()
    sub_resource_relationship: SnykIssueToOrgRel = SnykIssueToOrgRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnykIssueToProjectRel(),
            SnykIssueToCVERel(),
        ],
    )
