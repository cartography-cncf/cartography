from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OCIUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="OCI user OCID.")
    ocid: PropertyRef = PropertyRef(
        "id", extra_index=True, description="OCI user OCID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="User name.")
    description: PropertyRef = PropertyRef(
        "description", description="User description."
    )
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    compartmentid: PropertyRef = PropertyRef(
        "compartment_id", description="OCID of the user's compartment."
    )
    createdate: PropertyRef = PropertyRef(
        "time_created", description="Date and time when the user was created."
    )
    lifecycle_state: PropertyRef = PropertyRef(
        "lifecycle_state", description="Current lifecycle state of the user."
    )
    is_mfa_activated: PropertyRef = PropertyRef(
        "is_mfa_activated", description="Whether MFA is activated for the user."
    )
    can_use_api_keys: PropertyRef = PropertyRef(
        "can_use_api_keys", description="Whether the user can use API keys."
    )
    can_use_auth_tokens: PropertyRef = PropertyRef(
        "can_use_auth_tokens", description="Whether the user can use auth tokens."
    )
    can_use_console_password: PropertyRef = PropertyRef(
        "can_use_console_password",
        description="Whether the user can sign in with a console password.",
    )
    can_use_customer_secret_keys: PropertyRef = PropertyRef(
        "can_use_customer_secret_keys",
        description="Whether the user can use customer secret keys.",
    )
    can_use_smtp_credentials: PropertyRef = PropertyRef(
        "can_use_smtp_credentials",
        description="Whether the user can use SMTP credentials.",
    )


@dataclass(frozen=True)
class OCIUserToOCITenancyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OCIUserToOCITenancyRel(CartographyRelSchema):
    """An OCI tenancy contains a user as a managed resource."""

    target_node_label: str = "OCITenancy"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"ocid": PropertyRef("OCI_TENANCY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OCIUserToOCITenancyRelProperties = OCIUserToOCITenancyRelProperties()


@dataclass(frozen=True)
class OCIUserSchema(CartographyNodeSchema):
    """An OCI user account with the UserAccount label."""

    label: str = "OCIUser"
    properties: OCIUserNodeProperties = OCIUserNodeProperties()
    sub_resource_relationship: OCIUserToOCITenancyRel = OCIUserToOCITenancyRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
