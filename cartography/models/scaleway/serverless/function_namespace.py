from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayServerlessFunctionNamespaceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Namespace UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Namespace name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Namespace description."
    )
    status: PropertyRef = PropertyRef("status", description="Namespace status.")
    error_message: PropertyRef = PropertyRef(
        "error_message", description="Human-readable error message, if any."
    )
    registry_namespace_id: PropertyRef = PropertyRef(
        "registry_namespace_id",
        description="UUID of the backing container registry namespace.",
    )
    registry_endpoint: PropertyRef = PropertyRef(
        "registry_endpoint",
        extra_index=True,
        description="Endpoint of the backing container registry.",
    )
    # Whether the namespace can reach a VPC private network.
    vpc_integration_activated: PropertyRef = PropertyRef(
        "vpc_integration_activated",
        description="True if the namespace can reach a VPC private network.",
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the namespace lives in."
    )
    tags: PropertyRef = PropertyRef("tags", description="Namespace tags.")
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
class ScalewayServerlessFunctionNamespaceToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayServerlessFunctionNamespace)
class ScalewayServerlessFunctionNamespaceToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayServerlessFunctionNamespace` through
    `RESOURCE`.
    """

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayServerlessFunctionNamespaceToProjectRelProperties = (
        ScalewayServerlessFunctionNamespaceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayServerlessFunctionNamespaceSchema(CartographyNodeSchema):
    """Represents a Scaleway Serverless Functions namespace (project-scoped grouping of
    functions, backed by a hidden container registry namespace).
    """

    label: str = "ScalewayServerlessFunctionNamespace"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ComputeNamespace"])
    properties: ScalewayServerlessFunctionNamespaceProperties = (
        ScalewayServerlessFunctionNamespaceProperties()
    )
    sub_resource_relationship: ScalewayServerlessFunctionNamespaceToProjectRel = (
        ScalewayServerlessFunctionNamespaceToProjectRel()
    )
