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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class FlyAppNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Fly.io app ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Fly.io app name."
    )
    internal_numeric_id: PropertyRef = PropertyRef(
        "internal_numeric_id", description="Fly.io internal numeric app ID."
    )
    network: PropertyRef = PropertyRef("network", description="Fly.io network name.")
    status: PropertyRef = PropertyRef("status", description="App status.")
    machine_count: PropertyRef = PropertyRef(
        "machine_count", description="Number of Machines reported by the app summary."
    )
    volume_count: PropertyRef = PropertyRef(
        "volume_count", description="Number of Volumes reported by the app summary."
    )
    cname_target: PropertyRef = PropertyRef(
        "cname_target", description="App CNAME target."
    )
    app_role: PropertyRef = PropertyRef(
        "app_role", description="App role returned by Fly.io."
    )
    organization_slug: PropertyRef = PropertyRef(
        "organization_slug",
        extra_index=True,
        description="Organization slug returned by Fly.io.",
    )
    organization_id: PropertyRef = PropertyRef("ORGANIZATION_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class FlyAppToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyOrganization)-[:RESOURCE]->(:FlyApp)
class FlyAppToOrganizationRel(CartographyRelSchema):
    """Connects `FlyOrganization` to `FlyApp` through `RESOURCE`."""

    target_node_label: str = "FlyOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORGANIZATION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyAppToOrganizationRelProperties = FlyAppToOrganizationRelProperties()


@dataclass(frozen=True)
class FlyAppSchema(CartographyNodeSchema):
    """Represents a Fly.io app."""

    label: str = "FlyApp"
    properties: FlyAppNodeProperties = FlyAppNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    sub_resource_relationship: FlyAppToOrganizationRel = FlyAppToOrganizationRel()
