from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class CloudflareAccountNodeProperties(CartographyNodeProperties):
    created_on: PropertyRef = PropertyRef("created_on")
    name: PropertyRef = PropertyRef("name")
    abuse_contact_email: PropertyRef = PropertyRef("settings.abuse_contact_email")
    default_nameservers: PropertyRef = PropertyRef("settings.default_nameservers")
    enforce_twofactor: PropertyRef = PropertyRef("settings.enforce_twofactor")
    use_account_custom_ns_by_default: PropertyRef = PropertyRef(
        "settings.use_account_custom_ns_by_default"
    )
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareAccountSchema(CartographyNodeSchema):
    label: str = "CloudflareAccount"
    properties: CloudflareAccountNodeProperties = CloudflareAccountNodeProperties()
