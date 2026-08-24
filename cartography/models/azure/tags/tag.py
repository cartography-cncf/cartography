from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureTagProperties(CartographyNodeProperties):
    # The ID is a string: "{subscription_id}|{key}:{value}"
    id: PropertyRef = PropertyRef(
        "id",
        description="Subscription-scoped identifier formed from the tag key and value.",
    )
    key: PropertyRef = PropertyRef(
        "key", extra_index=True, description="Name of the tag."
    )
    value: PropertyRef = PropertyRef("value", description="Value of the tag.")
    subscription_id: PropertyRef = PropertyRef(
        "subscription_id",
        description="Azure subscription containing the tagged resource.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureTagToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureTagToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription scopes the tag."""

    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureTagToSubscriptionRelProperties = (
        AzureTagToSubscriptionRelProperties()
    )
