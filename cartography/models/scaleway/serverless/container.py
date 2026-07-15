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
class ScalewayServerlessContainerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Container UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Container name."
    )
    status: PropertyRef = PropertyRef("status", description="Container status.")
    registry_image: PropertyRef = PropertyRef(
        "registry_image", extra_index=True, description="Container image pull URI."
    )
    # Digest the `registry_image` pull URI resolves to, populated at ingest from
    # the container-registry sync so HAS_IMAGE can match the Image node.
    image_digest: PropertyRef = PropertyRef(
        "image_digest",
        extra_index=True,
        description="Digest the `registry_image` resolves to, populated at ingest from the container-registry sync.",
    )
    # Exposure signal: `public` lets anyone invoke the container without auth.
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
    protocol: PropertyRef = PropertyRef(
        "protocol", description="Serving protocol (`http1`, `h2c`)."
    )
    port: PropertyRef = PropertyRef("port", description="Container listening port.")
    sandbox: PropertyRef = PropertyRef(
        "sandbox", description="Sandbox generation (`v1`, `v2`)."
    )
    min_scale: PropertyRef = PropertyRef(
        "min_scale", description="Minimum number of instances."
    )
    max_scale: PropertyRef = PropertyRef(
        "max_scale", description="Maximum number of instances."
    )
    max_concurrency: PropertyRef = PropertyRef(
        "max_concurrency", description="Max concurrent requests per instance."
    )
    memory_limit: PropertyRef = PropertyRef(
        "memory_limit", description="Memory limit in MB."
    )
    cpu_limit: PropertyRef = PropertyRef("cpu_limit", description="CPU limit in mvCPU.")
    timeout: PropertyRef = PropertyRef(
        "timeout", description="Invocation timeout (e.g. `300s`)."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the container lives in."
    )
    tags: PropertyRef = PropertyRef("tags", description="Container tags.")
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
class ScalewayServerlessContainerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessContainer)
class ScalewayServerlessContainerToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayServerlessContainer` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayServerlessContainerToProjectRelProperties = (
        ScalewayServerlessContainerToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessContainerToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayServerlessContainerNamespace)-[:HAS]->(:ScalewayServerlessContainer)
class ScalewayServerlessContainerToNamespaceRel(CartographyRelSchema):
    """Connects `ScalewayServerlessContainerNamespace` to `ScalewayServerlessContainer`
    through `HAS`.
    """

    target_node_label: str = "ScalewayServerlessContainerNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayServerlessContainerToNamespaceRelProperties = (
        ScalewayServerlessContainerToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessContainerToPrivateNetworkRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayServerlessContainer)-[:ATTACHED_TO]->(:ScalewayPrivateNetwork)
class ScalewayServerlessContainerToPrivateNetworkRel(CartographyRelSchema):
    """Connects `ScalewayServerlessContainer` to `ScalewayPrivateNetwork` through
    `ATTACHED_TO`.
    """

    target_node_label: str = "ScalewayPrivateNetwork"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("private_network_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTACHED_TO"
    properties: ScalewayServerlessContainerToPrivateNetworkRelProperties = (
        ScalewayServerlessContainerToPrivateNetworkRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessContainerToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayServerlessContainer)-[:HAS_IMAGE]->(:ScalewayContainerRegistryImage)
# The container's `registry_image` pull URI is resolved to a digest at ingest;
# this ties the running container to the digest-addressed Image so the shared
# RESOLVED_IMAGE analysis can reach it.
class ScalewayServerlessContainerToImageRel(CartographyRelSchema):
    """Connects `ScalewayServerlessContainer` to `ScalewayContainerRegistryImage` through
    `HAS_IMAGE`.
    """

    target_node_label: str = "ScalewayContainerRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: ScalewayServerlessContainerToImageRelProperties = (
        ScalewayServerlessContainerToImageRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessContainerSchema(CartographyNodeSchema):
    """Represents a Scaleway Serverless Container (a managed, autoscaled container service
    that runs a single container).
    """

    label: str = "ScalewayServerlessContainer"
    # A Scaleway Serverless Container is a managed, autoscaled container service
    # (the Cloud Run Service / AWS App Runner analog) that runs a single
    # container. It is both the service (`ComputeService`) and the running
    # container (`Container`); the `Container` label lets the shared
    # RESOLVED_IMAGE analysis reach it via HAS_IMAGE.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["ComputeService", "Container"]
    )
    properties: ScalewayServerlessContainerProperties = (
        ScalewayServerlessContainerProperties()
    )
    sub_resource_relationship: ScalewayServerlessContainerToProjectRel = (
        ScalewayServerlessContainerToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayServerlessContainerToNamespaceRel(),
            ScalewayServerlessContainerToPrivateNetworkRel(),
            ScalewayServerlessContainerToImageRel(),
        ]
    )
