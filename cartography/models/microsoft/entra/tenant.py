from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class EntraTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Microsoft tenant ID.")
    created_date_time: PropertyRef = PropertyRef(
        "created_date_time", description="Timestamp when the tenant was created."
    )
    default_usage_location: PropertyRef = PropertyRef(
        "default_usage_location", description="Default tenant usage location."
    )
    deleted_date_time: PropertyRef = PropertyRef(
        "deleted_date_time", description="Timestamp when the tenant was deleted."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the tenant."
    )
    marketing_notification_emails: PropertyRef = PropertyRef(
        "marketing_notification_emails",
        description="Email addresses that receive marketing notifications.",
    )
    mobile_device_management_authority: PropertyRef = PropertyRef(
        "mobile_device_management_authority",
        description="Mobile device management authority for the tenant.",
    )
    on_premises_last_sync_date_time: PropertyRef = PropertyRef(
        "on_premises_last_sync_date_time",
        description="Timestamp of the latest on-premises directory synchronization.",
    )
    on_premises_sync_enabled: PropertyRef = PropertyRef(
        "on_premises_sync_enabled",
        description="Whether on-premises directory synchronization is enabled.",
    )
    partner_tenant_type: PropertyRef = PropertyRef(
        "partner_tenant_type", description="Partner relationship type of the tenant."
    )
    postal_code: PropertyRef = PropertyRef(
        "postal_code", description="Postal code of the tenant address."
    )
    preferred_language: PropertyRef = PropertyRef(
        "preferred_language", description="Preferred language of the tenant."
    )
    state: PropertyRef = PropertyRef(
        "state", description="State or province of the tenant address."
    )
    street: PropertyRef = PropertyRef(
        "street", description="Street portion of the tenant address."
    )
    tenant_type: PropertyRef = PropertyRef(
        "tenant_type", description="Microsoft directory tenant type."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraTenantSchema(CartographyNodeSchema):
    """A Microsoft tenant, with EntraTenant retained as a compatibility label."""

    label: str = "AzureTenant"
    properties: EntraTenantNodeProperties = EntraTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EntraTenant", "Tenant"])
