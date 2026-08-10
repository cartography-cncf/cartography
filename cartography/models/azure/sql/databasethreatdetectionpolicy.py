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
    id: PropertyRef = PropertyRef(
        "id", description="Azure resource ID for the database security alert policy."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Azure resource name.")
    emailadmins: PropertyRef = PropertyRef(
        "email_account_admins",
        description="Whether alerts are sent to account administrators.",
    )
    emailaddresses: PropertyRef = PropertyRef(
        "email_addresses",
        description="Additional email addresses that receive alerts.",
    )
    retentiondays: PropertyRef = PropertyRef(
        "retention_days",
        description="Number of days threat detection audit logs are retained.",
    )
    state: PropertyRef = PropertyRef(
        "state", description="Current state of the security alert policy."
    )
    storageendpoint: PropertyRef = PropertyRef(
        "storage_endpoint",
        description="Blob storage endpoint for threat detection audit logs.",
    )
    disabledalerts: PropertyRef = PropertyRef(
        "disabled_alerts", description="Alert types disabled by the policy."
    )
    creationtime: PropertyRef = PropertyRef(
        "creation_time", description="Timestamp when the policy was created."
    )


@dataclass(frozen=True)
class AzureDatabaseThreatDetectionPolicyToSQLDatabaseRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSQLDatabase)-[:CONTAINS]->(:AzureDatabaseThreatDetectionPolicy)
class AzureDatabaseThreatDetectionPolicyToSQLDatabaseRel(CartographyRelSchema):
    """An Azure SQL database contains this security alert policy."""

    target_node_label: str = "AzureSQLDatabase"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("database_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureDatabaseThreatDetectionPolicyToSQLDatabaseRelProperties = (
        AzureDatabaseThreatDetectionPolicyToSQLDatabaseRelProperties()
    )


@dataclass(frozen=True)
class AzureDatabaseThreatDetectionPolicyToSubscriptionRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AzureSubscription)-[:RESOURCE]->(:AzureDatabaseThreatDetectionPolicy)
class AzureDatabaseThreatDetectionPolicyToSubscriptionRel(CartographyRelSchema):
    """An Azure subscription contains this database security policy resource."""

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
    """A security alert policy for an Azure SQL database."""

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
