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
from cartography.models.ontology.labels import SNAPSHOT


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyDatabaseSnapshotNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify snapshot id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the snapshotted database belongs to."
    )
    # Composite `<site_id>|<source_branch_id>`, matching NetlifyDatabaseBranch.id.
    source_branch_node_id: PropertyRef = PropertyRef(
        "source_branch_node_id",
        description="`NetlifyDatabaseBranch.id` of the snapshotted branch.",
    )
    source_branch_id: PropertyRef = PropertyRef(
        "source_branch_id",
        description="Netlify's branch identifier of the snapshotted branch.",
    )
    # Netlify has no name for a snapshot, so transform() derives one from the source branch and
    # the point-in-time timestamp to satisfy the Snapshot ontology mapping.
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Derived `<source_branch_id>@<timestamp>`. Netlify gives a snapshot no name of its own.",
    )
    # False for the automatic snapshots Netlify takes on a schedule.
    manual: PropertyRef = PropertyRef(
        "manual",
        description="Whether the snapshot was taken by hand rather than on Netlify's schedule.",
    )
    timestamp: PropertyRef = PropertyRef(
        "timestamp", description="Point in time the snapshot captures."
    )
    expires_at: PropertyRef = PropertyRef(
        "expires_at", description="When the snapshot is deleted."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the snapshot was taken."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyDatabaseSnapshotToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyDatabaseSnapshot)
class NetlifyDatabaseSnapshotToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyDatabaseSnapshotToNetlifyAccountRelProperties = (
        NetlifyDatabaseSnapshotToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyDatabaseSnapshotToBranchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyDatabaseBranch)-[:HAS_SNAPSHOT]->(:NetlifyDatabaseSnapshot)
class NetlifyDatabaseSnapshotToBranchRel(CartographyRelSchema):
    target_node_label: str = "NetlifyDatabaseBranch"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_branch_node_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SNAPSHOT"
    properties: NetlifyDatabaseSnapshotToBranchRelProperties = (
        NetlifyDatabaseSnapshotToBranchRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyDatabaseSnapshotSchema(CartographyNodeSchema):
    """
    A point-in-time snapshot of a Netlify DB branch.
    """

    label: str = "NetlifyDatabaseSnapshot"
    properties: NetlifyDatabaseSnapshotNodeProperties = (
        NetlifyDatabaseSnapshotNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNAPSHOT])
    sub_resource_relationship: NetlifyDatabaseSnapshotToNetlifyAccountRel = (
        NetlifyDatabaseSnapshotToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyDatabaseSnapshotToBranchRel()],
    )
