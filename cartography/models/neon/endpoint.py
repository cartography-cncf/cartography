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
class NeonEndpointNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="The compute endpoint id (`ep-...`), unique across Neon"
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", description="Optional display name of the compute endpoint"
    )
    host: PropertyRef = PropertyRef(
        "host",
        extra_index=True,
        description="The hostname Postgres clients connect to",
    )
    pooled_host: PropertyRef = PropertyRef(
        "pooled_host",
        extra_index=True,
        description="The hostname of the connection pooler in front of this compute",
    )
    branch_id: PropertyRef = PropertyRef(
        "branch_id", description="Id of the branch this compute serves"
    )
    region_id: PropertyRef = PropertyRef(
        "region_id", description="The region hosting the compute"
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="`read_write` for the branch's primary compute, `read_only` for a read replica",
    )
    current_state: PropertyRef = PropertyRef(
        "current_state", description="Lifecycle state (`init`, `active`, `idle`)"
    )
    disabled: PropertyRef = PropertyRef(
        "disabled",
        description="Whether connections to the compute are refused",
    )
    passwordless_access: PropertyRef = PropertyRef(
        "passwordless_access",
        description="Whether the compute accepts passwordless (Console-brokered) authentication",
    )
    pooler_enabled: PropertyRef = PropertyRef(
        "pooler_enabled",
        description="Whether the deprecated per-endpoint pooler flag is set. The pooled hostname works either way",
    )
    pooler_mode: PropertyRef = PropertyRef(
        "pooler_mode", description="The connection pooler mode"
    )
    autoscaling_limit_min_cu: PropertyRef = PropertyRef(
        "autoscaling_limit_min_cu",
        description="Minimum compute size, in compute units",
    )
    autoscaling_limit_max_cu: PropertyRef = PropertyRef(
        "autoscaling_limit_max_cu",
        description="Maximum compute size, in compute units",
    )
    suspend_timeout_seconds: PropertyRef = PropertyRef(
        "suspend_timeout_seconds",
        description="Seconds of inactivity before the compute scales to zero. `0` uses the default, `-1` never suspends",
    )
    compute_release_version: PropertyRef = PropertyRef(
        "compute_release_version", description="The compute image release"
    )
    creation_source: PropertyRef = PropertyRef(
        "creation_source",
        description="How the compute was created (`console`, `neonctl`, ...)",
    )
    last_active: PropertyRef = PropertyRef(
        "last_active", description="When the compute was last active"
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the compute was created"
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the compute was last changed"
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        extra_index=True,
        description="`True` when any internet address may open a connection: public connections are not blocked, the compute is not disabled, and no IP allowlist applies to its branch (or the allowlist contains `0.0.0.0/0` or `::/0`)",
    )
    exposed_internet_type: PropertyRef = PropertyRef(
        "exposed_internet_type",
        extra_index=True,
        description="How it is exposed. Always `direct`, since the hostname resolves to the compute's own proxy",
    )


@dataclass(frozen=True)
class NeonEndpointToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonProject)-[:RESOURCE]->(:NeonEndpoint)
class NeonEndpointToProjectRel(CartographyRelSchema):
    target_node_label: str = "NeonProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NeonEndpointToProjectRelProperties = (
        NeonEndpointToProjectRelProperties()
    )


@dataclass(frozen=True)
class NeonEndpointToBranchRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NeonEndpoint)-[:ATTACHED_TO]->(:NeonBranch)
class NeonEndpointToBranchRel(CartographyRelSchema):
    target_node_label: str = "NeonBranch"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("branch_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: NeonEndpointToBranchRelProperties = NeonEndpointToBranchRelProperties()


@dataclass(frozen=True)
class NeonEndpointSchema(CartographyNodeSchema):
    """Represents a Neon compute endpoint: the Postgres server that serves one branch and the hostname clients connect to."""

    label: str = "NeonEndpoint"
    properties: NeonEndpointNodeProperties = NeonEndpointNodeProperties()
    sub_resource_relationship: NeonEndpointToProjectRel = NeonEndpointToProjectRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NeonEndpointToBranchRel(),
        ],
    )
