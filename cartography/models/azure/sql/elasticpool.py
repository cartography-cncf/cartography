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
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the SQL elastic pool."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    location: PropertyRef = PropertyRef(
        "location", description="Azure region of the resource."
    )
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    kind: PropertyRef = PropertyRef(
        "kind", description="Resource kind reported by Azure."
    )
    creation_date: PropertyRef = PropertyRef(
        "creation_date", description="Timestamp when the elastic pool was created."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current state of the elastic pool."
    )
    maxsizebytes: PropertyRef = PropertyRef(
        "max_size_bytes", description="Storage limit for the elastic pool in bytes."
    )
    licensetype: PropertyRef = PropertyRef(
        "license_type", description="License model for the elastic pool."
    )
    zoneredundant: PropertyRef = PropertyRef(
        "zone_redundant",
        description="Whether the elastic pool uses availability zone redundancy.",
    )


@dataclass(frozen=True)
class AzureElasticPoolToSQLServerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLServer)-[:CONTAINS]->(:AzureElasticPool)
class AzureElasticPoolToSQLServerRel(CartographyRelSchema):
    """An Azure SQL logical server contains this elastic pool."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureElasticPoolToSQLServerRelProperties = (
        AzureElasticPoolToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureElasticPoolToSubscriptionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureElasticPool)
class AzureElasticPoolToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this SQL elastic pool resource."""

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
# (:AzureSQLServer)-[:RESOURCE]->(:AzureElasticPool) - Backwards compatibility
class AzureElasticPoolToSQLServerDeprecatedRel(CartographyRelSchema):
    """An Azure SQL logical server contains this elastic pool resource."""

    target_node_label: str = "AzureSQLServer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("server_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureElasticPoolToSQLServerRelProperties = (
        AzureElasticPoolToSQLServerRelProperties()
    )


@dataclass(frozen=True)
class AzureElasticPoolSchema(CartographyNodeSchema):
    """An Azure SQL elastic pool that shares resources across databases."""

    label: str = "AzureElasticPool"
    properties: AzureElasticPoolProperties = AzureElasticPoolProperties()
    sub_resource_relationship: AzureElasticPoolToSubscriptionRel = (
        AzureElasticPoolToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureElasticPoolToSQLServerRel(),
            # DEPRECATED: for backward compatibility, will be removed in v1.0.0
            AzureElasticPoolToSQLServerDeprecatedRel(),
        ]
    )
