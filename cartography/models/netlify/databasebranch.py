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
from cartography.models.ontology.labels import DATABASE


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyDatabaseBranchNodeProperties(CartographyNodeProperties):
    # Composite `<site_id>|<branch_id>`, built in transform(). Netlify's `branch_id` is only
    # unique within a site (the primary branch is literally called "production" on every site).
    id: PropertyRef = PropertyRef(
        "id",
        description="Composite `<site_id>|<branch_id>`. Netlify's `branch_id` is only unique within a site: the primary branch is called `production` on every Netlify DB.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the database is attached to."
    )
    branch_id: PropertyRef = PropertyRef(
        "branch_id", description="Netlify's branch identifier."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Branch name."
    )
    state: PropertyRef = PropertyRef("state", description="Branch state, e.g. `ready`.")
    logical_size_bytes: PropertyRef = PropertyRef(
        "logical_size_bytes", description="Logical size of the branch's data."
    )
    # Netlify DB runs on Neon, so the branch has an autoscaling compute endpoint that suspends
    # when idle. Flattened from the nested `compute` object by transform().
    compute_state: PropertyRef = PropertyRef(
        "compute_state",
        description="State of the branch's compute endpoint, e.g. `active`, `idle`.",
    )
    compute_min_cu: PropertyRef = PropertyRef(
        "compute_min_cu", description="Minimum autoscaling compute units."
    )
    compute_max_cu: PropertyRef = PropertyRef(
        "compute_max_cu", description="Maximum autoscaling compute units."
    )
    compute_suspend_timeout_seconds: PropertyRef = PropertyRef(
        "compute_suspend_timeout_seconds",
        description="Idle seconds before the compute endpoint suspends.",
    )
    compute_last_active: PropertyRef = PropertyRef(
        "compute_last_active",
        description="When the compute endpoint last served a query.",
    )
    # The roles Netlify issued a connection string for. The connection strings themselves hold
    # a plaintext password and are never ingested.
    connection_roles: PropertyRef = PropertyRef(
        "connection_roles",
        description="Database roles Netlify issued a connection string for.",
    )
    last_active_at: PropertyRef = PropertyRef(
        "last_active_at", description="When the branch was last active."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the branch was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the branch was last modified."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyDatabaseBranchToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyDatabaseBranch)
class NetlifyDatabaseBranchToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyDatabaseBranchToNetlifyAccountRelProperties = (
        NetlifyDatabaseBranchToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyDatabaseBranchToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_DATABASE_BRANCH]->(:NetlifyDatabaseBranch)
class NetlifyDatabaseBranchToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DATABASE_BRANCH"
    properties: NetlifyDatabaseBranchToSiteRelProperties = (
        NetlifyDatabaseBranchToSiteRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyDatabaseBranchSchema(CartographyNodeSchema):
    """
    A branch of a Netlify DB (Neon) Postgres database attached to a site.
    """

    label: str = "NetlifyDatabaseBranch"
    properties: NetlifyDatabaseBranchNodeProperties = (
        NetlifyDatabaseBranchNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([DATABASE])
    sub_resource_relationship: NetlifyDatabaseBranchToNetlifyAccountRel = (
        NetlifyDatabaseBranchToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [NetlifyDatabaseBranchToSiteRel()],
    )
