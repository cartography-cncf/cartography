from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class CloudflareAccountNodeProperties(CartographyNodeProperties):
    created_on: PropertyRef = PropertyRef('created_on')
    name: PropertyRef = PropertyRef('name')
    settings_abuse_contact_email: PropertyRef = PropertyRef('settings.abuse_contact_email')
    settings_default_nameservers: PropertyRef = PropertyRef('settings.default_nameservers')
    settings_enforce_twofactor: PropertyRef = PropertyRef('settings.enforce_twofactor')
    settings_use_account_custom_ns_by_default: PropertyRef = PropertyRef('settings.use_account_custom_ns_by_default')
    id: PropertyRef = PropertyRef('id')
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)






@dataclass(frozen=True)
class CloudflareAccountSchema(CartographyNodeSchema):
    label: str = 'CloudflareAccount'
    properties: CloudflareAccountNodeProperties = CloudflareAccountNodeProperties()
