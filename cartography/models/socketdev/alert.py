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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef("key")
    type: PropertyRef = PropertyRef("type", extra_index=True)
    category: PropertyRef = PropertyRef("category", extra_index=True)
    severity: PropertyRef = PropertyRef("severity", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    title: PropertyRef = PropertyRef("title")
    description: PropertyRef = PropertyRef("description")
    dashboard_url: PropertyRef = PropertyRef("dashboardUrl")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")
    cleared_at: PropertyRef = PropertyRef("clearedAt")
    # Vulnerability fields (populated when category == "vulnerability")
    cve_id: PropertyRef = PropertyRef("cve_id")
    ghsa_id: PropertyRef = PropertyRef("ghsa_id", extra_index=True)
    cvss_score: PropertyRef = PropertyRef("cvss_score")
    epss_score: PropertyRef = PropertyRef("epss_score")
    epss_percentile: PropertyRef = PropertyRef("epss_percentile")
    is_kev: PropertyRef = PropertyRef("is_kev")
    first_patched_version: PropertyRef = PropertyRef("first_patched_version")
    # Location fields (from first location entry)
    action: PropertyRef = PropertyRef("action")
    repo_slug: PropertyRef = PropertyRef("repo_slug")
    repo_fullname: PropertyRef = PropertyRef("repo_fullname")
    branch: PropertyRef = PropertyRef("branch")
    artifact_name: PropertyRef = PropertyRef("artifact_name")
    artifact_version: PropertyRef = PropertyRef("artifact_version")
    artifact_type: PropertyRef = PropertyRef("artifact_type")


@dataclass(frozen=True)
class SocketDevOrgToAlertRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SocketDevOrganization)-[:RESOURCE]->(:SocketDevAlert)
class SocketDevOrgToAlertRel(CartographyRelSchema):
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
    target_node_label: str = "SocketDevRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"fullname": PropertyRef("repo_fullname")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FOUND_IN"
    properties: SocketDevAlertToRepoRelProperties = SocketDevAlertToRepoRelProperties()


@dataclass(frozen=True)
class SocketDevAlertSchema(CartographyNodeSchema):
    label: str = "SocketDevAlert"
    properties: SocketDevAlertNodeProperties = SocketDevAlertNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Risk"])
    sub_resource_relationship: SocketDevOrgToAlertRel = SocketDevOrgToAlertRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            SocketDevAlertToRepoRel(),
        ],
    )
