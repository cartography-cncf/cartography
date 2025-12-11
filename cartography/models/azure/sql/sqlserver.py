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
class AzureSQLServerProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    resourcegroup: PropertyRef = PropertyRef("resourceGroup")
    location: PropertyRef = PropertyRef("location")
    kind: PropertyRef = PropertyRef("kind")
    state: PropertyRef = PropertyRef("state")
    version: PropertyRef = PropertyRef("version")


@dataclass(frozen=True)
class AzureSQLServerToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureSQLServer)
class AzureSQLServerToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureSQLServerToSubscriptionRelProperties = (
        AzureSQLServerToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureSQLServerSchema(CartographyNodeSchema):
    label: str = "AzureSQLServer"
    properties: AzureSQLServerProperties = AzureSQLServerProperties()
    sub_resource_relationship: AzureSQLServerToSubscriptionRel = (
        AzureSQLServerToSubscriptionRel()
    )
