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
class ScalewayServerlessFunctionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Function UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Function name."
    )
    status: PropertyRef = PropertyRef("status", description="Function status.")
    runtime: PropertyRef = PropertyRef(
        "runtime", description="Runtime (e.g. `python311`, `node20`)."
    )
    handler: PropertyRef = PropertyRef(
        "handler", description="Function entrypoint handler."
    )
    # Exposure signal: `public` lets anyone invoke the function without auth.
    privacy: PropertyRef = PropertyRef(
        "privacy",
        description="Invocation privacy (`public` allows unauthenticated invokes, `private` requires a token).",
    )
    domain_name: PropertyRef = PropertyRef(
        "domain_name", extra_index=True, description="Auto-assigned invocation domain."
    )
    # `enabled` allows plain HTTP; `redirected` forces HTTPS.
    http_option: PropertyRef = PropertyRef(
        "http_option",
        description="`enabled` allows plain HTTP; `redirected` forces HTTPS.",
    )
    sandbox: PropertyRef = PropertyRef(
        "sandbox", description="Sandbox generation (`v1`, `v2`)."
    )
    min_scale: PropertyRef = PropertyRef(
        "min_scale", description="Minimum number of instances."
    )
    max_scale: PropertyRef = PropertyRef(
        "max_scale", description="Maximum number of instances."
    )
    memory_limit: PropertyRef = PropertyRef(
        "memory_limit", description="Memory limit in MB."
    )
    cpu_limit: PropertyRef = PropertyRef("cpu_limit", description="CPU limit in mvCPU.")
    timeout: PropertyRef = PropertyRef(
        "timeout", description="Invocation timeout (e.g. `300s`)."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the function lives in."
    )
    tags: PropertyRef = PropertyRef("tags", description="Function tags.")
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessFunction)
class ScalewayServerlessFunctionToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayServerlessFunction` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayServerlessFunctionToProjectRelProperties = (
        ScalewayServerlessFunctionToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayServerlessFunctionNamespace)-[:HAS]->(:ScalewayServerlessFunction)
class ScalewayServerlessFunctionToNamespaceRel(CartographyRelSchema):
    """Connects `ScalewayServerlessFunctionNamespace` to `ScalewayServerlessFunction`
    through `HAS`.
    """

    target_node_label: str = "ScalewayServerlessFunctionNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayServerlessFunctionToNamespaceRelProperties = (
        ScalewayServerlessFunctionToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionToPrivateNetworkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayServerlessFunction)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
class ScalewayServerlessFunctionToPrivateNetworkRel(CartographyRelSchema):
    """Connects `ScalewayServerlessFunction` to `ScalewayPrivateNetwork` through
    `ATTACHED_TO`.
    """

    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayServerlessFunctionToPrivateNetworkRelProperties = (
        ScalewayServerlessFunctionToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionSchema(CartographyNodeSchema):
    """Represents a Scaleway Serverless Function."""

    label: str = "ScalewayServerlessFunction"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Function"])
    properties: ScalewayServerlessFunctionProperties = (
        ScalewayServerlessFunctionProperties()
    )
    sub_resource_relationship: ScalewayServerlessFunctionToProjectRel = (
        ScalewayServerlessFunctionToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayServerlessFunctionToNamespaceRel(),
            ScalewayServerlessFunctionToPrivateNetworkRel(),
        ]
    )
