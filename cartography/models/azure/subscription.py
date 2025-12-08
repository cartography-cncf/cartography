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
class AzureSubscriptionProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("subscriptionId")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    path: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("displayName")
    state: PropertyRef = PropertyRef("state")


@dataclass(frozen=True)
class AzureSubscriptionToTenantProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureTenant)-[:RESOURCE]->(:AzureSubscription)
class AzureSubscriptionToTenantRel(CartographyRelSchema):
    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSubscriptionToTenantProperties = (
        AzureSubscriptionToTenantProperties()
    )


@dataclass(frozen=True)
class AzureSubscriptionSchema(CartographyNodeSchema):
    label: str = "AzureSubscription"
    properties: AzureSubscriptionProperties = AzureSubscriptionProperties()
    sub_resource_relationship: AzureSubscriptionToTenantRel = (
        AzureSubscriptionToTenantRel()
    )
