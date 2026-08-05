from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class FlyIPNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Fly IP address ID, or synthesized `<app_id>/<address>` key for "
            "shared IPv4 addresses."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    address: PropertyRef = PropertyRef(
        "address", extra_index=True, description="IP address."
    )
    type: PropertyRef = PropertyRef(
        "type",
        description=(
            "Fly.io IP type, such as `v6`, `shared_v4`, `private_v6`, or "
            "`egress_v4`."
        ),
    )
    region: PropertyRef = PropertyRef(
        "region", description="Fly.io region, if applicable."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description=(
            "Creation timestamp, or last ownership-change timestamp for "
            "app-scoped egress IPs."
        ),
    )
    direction: PropertyRef = PropertyRef(
        "direction", description="Whether the IP is used for app ingress or egress."
    )
    ip_version: PropertyRef = PropertyRef(
        "ip_version", description="IP version, either `4` or `6`."
    )
    is_public: PropertyRef = PropertyRef(
        "is_public", description="Whether the address is globally routable."
    )
    service_name: PropertyRef = PropertyRef(
        "service_name", description="Fly service name, if returned by Fly.io."
    )
    network_name: PropertyRef = PropertyRef(
        "network_name", description="Fly network name, if returned by Fly.io."
    )
    network_organization_slug: PropertyRef = PropertyRef(
        "network_organization_slug",
        description="Fly network organization slug, if returned by Fly.io.",
    )
    app_id: PropertyRef = PropertyRef(
        "APP_ID", set_in_kwargs=True, description="Fly app ID."
    )


@dataclass(frozen=True)
class FlyIPToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlyIP)
class FlyIPToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlyIP` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlyIPToAppRelProperties = FlyIPToAppRelProperties()


@dataclass(frozen=True)
class FlyIPSchema(CartographyNodeSchema):
    """Represents an IP address allocated to a Fly app."""

    label: str = "FlyIP"
    properties: FlyIPNodeProperties = FlyIPNodeProperties()
    sub_resource_relationship: FlyIPToAppRel = FlyIPToAppRel()
