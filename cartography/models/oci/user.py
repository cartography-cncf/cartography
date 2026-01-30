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
class OCIUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    ocid: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    compartmentid: PropertyRef = PropertyRef("compartment_id")
    createdate: PropertyRef = PropertyRef("time_created")
    lifecycle_state: PropertyRef = PropertyRef("lifecycle_state")
    is_mfa_activated: PropertyRef = PropertyRef("is_mfa_activated")
    can_use_api_keys: PropertyRef = PropertyRef("can_use_api_keys")
    can_use_auth_tokens: PropertyRef = PropertyRef("can_use_auth_tokens")
    can_use_console_password: PropertyRef = PropertyRef("can_use_console_password")
    can_use_customer_secret_keys: PropertyRef = PropertyRef(
        "can_use_customer_secret_keys"
    )
    can_use_smtp_credentials: PropertyRef = PropertyRef("can_use_smtp_credentials")


@dataclass(frozen=True)
class OCIUserToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIUserToOCITenancyRel(CartographyRelSchema):
    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OCIUserToOCITenancyRelProperties = OCIUserToOCITenancyRelProperties()


@dataclass(frozen=True)
class OCIUserSchema(CartographyNodeSchema):
    label: str = "OCIUser"
    properties: OCIUserNodeProperties = OCIUserNodeProperties()
    sub_resource_relationship: OCIUserToOCITenancyRel = OCIUserToOCITenancyRel()
