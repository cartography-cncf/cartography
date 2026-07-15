from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class S1AccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="SentinelOne account ID.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="SentinelOne account name.",
    )
    account_type: PropertyRef = PropertyRef(
        "account_type",
        description="SentinelOne account type.",
    )
    active_agents: PropertyRef = PropertyRef(
        "active_agents",
        description="Number of active agents in the account.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Account creation timestamp.",
    )
    expiration: PropertyRef = PropertyRef(
        "expiration",
        description="Account expiration timestamp.",
    )
    number_of_sites: PropertyRef = PropertyRef(
        "number_of_sites",
        description="Number of sites in the account.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Current account state.",
    )


@dataclass(frozen=True)
class S1AccountSchema(CartographyNodeSchema):
    """A top-level SentinelOne account."""

    label: str = "S1Account"
    properties: S1AccountNodeProperties = S1AccountNodeProperties()
    sub_resource_relationship: None = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
