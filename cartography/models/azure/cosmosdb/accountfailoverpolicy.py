from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AzureCosmosDBAccountFailoverPolicyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    locationname: PropertyRef = PropertyRef("locationname")
    failoverpriority: PropertyRef = PropertyRef("failoverpriority")


@dataclass(frozen=True)
class AzureCosmosDBAccountFailoverPolicyToCosmosDBAccountRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccountFailoverPolicy)<-[:CONTAINS]-(:AzureCosmosDBAccount)
class AzureCosmosDBAccountFailoverPolicyToCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DatabaseAccountId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBAccountFailoverPolicyToCosmosDBAccountRelProperties = (
        AzureCosmosDBAccountFailoverPolicyToCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBAccountFailoverPolicyToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBAccountFailoverPolicy)
class AzureCosmosDBAccountFailoverPolicyToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBAccountFailoverPolicyToSubscriptionRelProperties = (
        AzureCosmosDBAccountFailoverPolicyToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBAccountFailoverPolicySchema(CartographyNodeSchema):
    label: str = "AzureCosmosDBAccountFailoverPolicy"
    properties: AzureCosmosDBAccountFailoverPolicyProperties = (
        AzureCosmosDBAccountFailoverPolicyProperties()
    )
    sub_resource_relationship: AzureCosmosDBAccountFailoverPolicyToSubscriptionRel = (
        AzureCosmosDBAccountFailoverPolicyToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBAccountFailoverPolicyToCosmosDBAccountRel(),
        ]
    )
