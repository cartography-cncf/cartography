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
class ScalewaySearchDeploymentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the deployment.")
    name: PropertyRef = PropertyRef("name", description="Name of the deployment.")
    status: PropertyRef = PropertyRef("status", description="Status of the deployment.")
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags attached to the deployment."
    )
    node_amount: PropertyRef = PropertyRef(
        "node_amount", description="Number of nodes."
    )
    node_type: PropertyRef = PropertyRef("node_type", description="Node type.")
    version: PropertyRef = PropertyRef("version", description="Engine version.")
    # Derived from the endpoints list: true if any endpoint is public-facing.
    is_public: PropertyRef = PropertyRef(
        "is_public", description="True if any endpoint is public-facing."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the deployment lives in."
    )
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
class ScalewaySearchDeploymentToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewaySearchDeployment)
class ScalewaySearchDeploymentToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewaySearchDeployment` through `RESOURCE`."""

    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewaySearchDeploymentToProjectRelProperties = (
        ScalewaySearchDeploymentToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewaySearchDeploymentSchema(CartographyNodeSchema):
    """Represents a managed OpenSearch deployment (SearchDB) in Scaleway."""

    label: str = "ScalewaySearchDeployment"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: ScalewaySearchDeploymentProperties = (
        ScalewaySearchDeploymentProperties()
    )
    sub_resource_relationship: ScalewaySearchDeploymentToProjectRel = (
        ScalewaySearchDeploymentToProjectRel()
    )
