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
class AzureCosmosDBCorsPolicyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("cors_policy_unique_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    allowedorigins: PropertyRef = PropertyRef("allowed_origins")
    allowedmethods: PropertyRef = PropertyRef("allowed_methods")
    allowedheaders: PropertyRef = PropertyRef("allowed_headers")
    exposedheaders: PropertyRef = PropertyRef("exposed_headers")
    maxageinseconds: PropertyRef = PropertyRef("max_age_in_seconds")


@dataclass(frozen=True)
class AzureCosmosDBCorsPolicyToCosmosDBAccountProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONTAINS]->(:AzureCosmosDBCorsPolicy)
class AzureCosmosDBCorsPolicyToCosmosDBAccountRel(CartographyRelSchema):
    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DatabaseAccountId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBCorsPolicyToCosmosDBAccountProperties = (
        AzureCosmosDBCorsPolicyToCosmosDBAccountProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBCorsPolicyToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBCorsPolicy)
class AzureCosmosDBCorsPolicyToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureCosmosDBCorsPolicyToSubscriptionRelProperties = (
        AzureCosmosDBCorsPolicyToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBCorsPolicySchema(CartographyNodeSchema):
    label: str = "AzureCosmosDBCorsPolicy"
    properties: AzureCosmosDBCorsPolicyProperties = AzureCosmosDBCorsPolicyProperties()
    sub_resource_relationship: AzureCosmosDBCorsPolicyToSubscriptionRel = (
        AzureCosmosDBCorsPolicyToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureCosmosDBCorsPolicyToCosmosDBAccountRel(),
        ]
    )
