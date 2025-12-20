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
class AzureElasticPoolProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    location: PropertyRef = PropertyRef("location")
    name: PropertyRef = PropertyRef("name")
    kind: PropertyRef = PropertyRef("kind")
    creation_date: PropertyRef = PropertyRef("creation_date")
    state: PropertyRef = PropertyRef("state")
    maxsizebytes: PropertyRef = PropertyRef("max_size_bytes")
    licensetype: PropertyRef = PropertyRef("license_type")
    zoneredundant: PropertyRef = PropertyRef("zone_redundant")


@dataclass(frozen=True)
class AzureElasticPoolToSQLServerProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:RESOURCE]->(:AzureElasticPool)
class AzureElasticPoolToSQLServerRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureElasticPoolToSQLServerProperties = (
        AzureElasticPoolToSQLServerProperties()
    )


@dataclass(frozen=True)
class AzureElasticPoolToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureElasticPool)
class AzureElasticPoolToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureElasticPoolToSubscriptionRelProperties = (
        AzureElasticPoolToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureElasticPoolSchema(CartographyNodeSchema):
    label: str = "AzureElasticPool"
    properties: AzureElasticPoolProperties = AzureElasticPoolProperties()
    sub_resource_relationship: AzureElasticPoolToSubscriptionRel = (
        AzureElasticPoolToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureElasticPoolToSQLServerRel(),
        ]
    )
