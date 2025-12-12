from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class S1AccountNodeProperties(CartographyNodeProperties):
    """
    Properties for SentinelOne Account nodes
    """

    # Required unique identifier
    id: PropertyRef = PropertyRef("id")

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from SentinelOne API
    name: PropertyRef = PropertyRef("name", extra_index=True)
    account_type: PropertyRef = PropertyRef("account_type")
    active_agents: PropertyRef = PropertyRef("active_agents")
    created_at: PropertyRef = PropertyRef("created_at")
    expiration: PropertyRef = PropertyRef("expiration")
    number_of_sites: PropertyRef = PropertyRef("number_of_sites")
    state: PropertyRef = PropertyRef("state")


@dataclass(frozen=True)
class S1AccountSchema(CartographyNodeSchema):
    """
    Schema for SentinelOne Account nodes
    """

    label: str = "S1Account"
    properties: S1AccountNodeProperties = S1AccountNodeProperties()

    # S1Account is a top-level tenant-like entity, so no sub_resource_relationship
    sub_resource_relationship: None = None
