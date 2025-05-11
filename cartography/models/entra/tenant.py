from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class EntraTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    created_date_time: PropertyRef = PropertyRef("created_date_time")
    default_usage_location: PropertyRef = PropertyRef("default_usage_location")
    deleted_date_time: PropertyRef = PropertyRef("deleted_date_time")
    display_name: PropertyRef = PropertyRef("display_name")
    marketing_notification_emails: PropertyRef = PropertyRef(
        "marketing_notification_emails"
    )
    mobile_device_management_authority: PropertyRef = PropertyRef(
        "mobile_device_management_authority"
    )
    on_premises_last_sync_date_time: PropertyRef = PropertyRef(
        "on_premises_last_sync_date_time"
    )
    on_premises_sync_enabled: PropertyRef = PropertyRef("on_premises_sync_enabled")
    partner_tenant_type: PropertyRef = PropertyRef("partner_tenant_type")
    postal_code: PropertyRef = PropertyRef("postal_code")
    preferred_language: PropertyRef = PropertyRef("preferred_language")
    state: PropertyRef = PropertyRef("state")
    street: PropertyRef = PropertyRef("street")
    tenant_type: PropertyRef = PropertyRef("tenant_type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraTenantSchema(CartographyNodeSchema):
    label: str = "AzureTenant"
    properties: EntraTenantNodeProperties = EntraTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["EntraTenant"])
