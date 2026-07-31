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
    id: PropertyRef = PropertyRef(
        "cors_policy_unique_id",
        description="Unique identifier assigned to the CORS policy.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    allowedorigins: PropertyRef = PropertyRef(
        "allowed_origins",
        description="Origins permitted to make cross-origin requests.",
    )
    allowedmethods: PropertyRef = PropertyRef(
        "allowed_methods",
        description="HTTP methods permitted for cross-origin requests.",
    )
    allowedheaders: PropertyRef = PropertyRef(
        "allowed_headers",
        description="Request headers permitted for cross-origin requests.",
    )
    exposedheaders: PropertyRef = PropertyRef(
        "exposed_headers",
        description="Response headers exposed to cross-origin clients.",
    )
    maxageinseconds: PropertyRef = PropertyRef(
        "max_age_in_seconds",
        description="Maximum time in seconds that a preflight response may be cached.",
    )


@dataclass(frozen=True)
class AzureCosmosDBCorsPolicyToCosmosDBAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureCosmosDBAccount)-[:CONTAINS]->(:AzureCosmosDBCorsPolicy)
class AzureCosmosDBCorsPolicyToCosmosDBAccountRel(CartographyRelSchema):
    """A Cosmos DB account contains the CORS policy."""

    target_node_label: str = "AzureCosmosDBAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DatabaseAccountId", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureCosmosDBCorsPolicyToCosmosDBAccountRelProperties = (
        AzureCosmosDBCorsPolicyToCosmosDBAccountRelProperties()
    )


@dataclass(frozen=True)
class AzureCosmosDBCorsPolicyToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureCosmosDBCorsPolicy)
class AzureCosmosDBCorsPolicyToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains the CORS policy as a resource."""

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
    """A cross-origin resource sharing policy for an Azure Cosmos DB account."""

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
