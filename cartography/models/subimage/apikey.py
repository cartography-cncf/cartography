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
class SubImageAPIKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("app_id", description="Application ID.")
    client_id: PropertyRef = PropertyRef(
        "client_id",
        description="Client ID.",
    )
    role: PropertyRef = PropertyRef(
        "role",
        description="Role associated with the API key.",
    )
    name: PropertyRef = PropertyRef("name", description="API key name.")
    description: PropertyRef = PropertyRef(
        "description",
        description="API key description.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SubImageAPIKeyToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SubImageTenant)-[:RESOURCE]->(:SubImageAPIKey)
class SubImageAPIKeyToTenantRel(CartographyRelSchema):
    """The tenant contains the API key."""

    target_node_label: str = "SubImageTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SubImageAPIKeyToTenantRelProperties = (
        SubImageAPIKeyToTenantRelProperties()
    )


@dataclass(frozen=True)
class SubImageAPIKeySchema(CartographyNodeSchema):
    """An API key configured in SubImage."""

    label: str = "SubImageAPIKey"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["APIKey"])
    properties: SubImageAPIKeyNodeProperties = SubImageAPIKeyNodeProperties()
    sub_resource_relationship: SubImageAPIKeyToTenantRel = SubImageAPIKeyToTenantRel()
