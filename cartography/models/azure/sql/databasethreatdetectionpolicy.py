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
class AzureDatabaseThreatDetectionPolicyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    location: PropertyRef = PropertyRef("location")
    kind: PropertyRef = PropertyRef("kind")
    emailadmins: PropertyRef = PropertyRef("email_account_admins")
    emailaddresses: PropertyRef = PropertyRef("email_addresses")
    retentiondays: PropertyRef = PropertyRef("retention_days")
    state: PropertyRef = PropertyRef("state")
    storageendpoint: PropertyRef = PropertyRef("storage_endpoint")
    useserverdefault: PropertyRef = PropertyRef("use_server_default")
    disabledalerts: PropertyRef = PropertyRef("disabled_alerts")


@dataclass(frozen=True)
class AzureDatabaseThreatDetectionPolicyToSQLDatabaseProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLDatabase)-[:CONTAINS]->(:AzureDatabaseThreatDetectionPolicy)
class AzureDatabaseThreatDetectionPolicyToSQLDatabaseRel(CartographyRelSchema):
    target_node_label: str = "AzureSQLDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureDatabaseThreatDetectionPolicyToSQLDatabaseProperties = (
        AzureDatabaseThreatDetectionPolicyToSQLDatabaseProperties()
    )


@dataclass(frozen=True)
class AzureDatabaseThreatDetectionPolicyToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureDatabaseThreatDetectionPolicy)
class AzureDatabaseThreatDetectionPolicyToSubscriptionRel(CartographyRelSchema):
    target_node_label: str = "AzureSubscription"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AZURE_SUBSCRIPTION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AzureDatabaseThreatDetectionPolicyToSubscriptionRelProperties = (
        AzureDatabaseThreatDetectionPolicyToSubscriptionRelProperties()
    )


@dataclass(frozen=True)
class AzureDatabaseThreatDetectionPolicySchema(CartographyNodeSchema):
    label: str = "AzureDatabaseThreatDetectionPolicy"
    properties: AzureDatabaseThreatDetectionPolicyProperties = (
        AzureDatabaseThreatDetectionPolicyProperties()
    )
    sub_resource_relationship: AzureDatabaseThreatDetectionPolicyToSubscriptionRel = (
        AzureDatabaseThreatDetectionPolicyToSubscriptionRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AzureDatabaseThreatDetectionPolicyToSQLDatabaseRel(),
        ]
    )
