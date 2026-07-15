from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class CloudflareAccountNodeProperties(CartographyNodeProperties):
    created_on: PropertyRef = PropertyRef(
        "created_on",
        description="Timestamp when the account was created.",
    )
    name: PropertyRef = PropertyRef("name", description="Account name.")
    abuse_contact_email: PropertyRef = PropertyRef(
        "settings.abuse_contact_email",
        description="Contact email for abuse reports.",
    )
    default_nameservers: PropertyRef = PropertyRef(
        "settings.default_nameservers",
        description="Deprecated default nameserver setting for new zones.",
    )
    enforce_twofactor: PropertyRef = PropertyRef(
        "settings.enforce_twofactor",
        description="Whether account membership requires two-factor authentication.",
    )
    use_account_custom_ns_by_default: PropertyRef = PropertyRef(
        "settings.use_account_custom_ns_by_default",
        description="Deprecated setting for using account custom nameservers by default.",
    )
    id: PropertyRef = PropertyRef("id", description="Cloudflare account ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class CloudflareAccountSchema(CartographyNodeSchema):
    """A Cloudflare account that contains managed resources."""

    label: str = "CloudflareAccount"
    properties: CloudflareAccountNodeProperties = CloudflareAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
