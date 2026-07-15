from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EntraServicePrincipalNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Entra service principal ID.")
    app_id: PropertyRef = PropertyRef(
        "app_id", description="Client ID of the associated application."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the service principal."
    )
    reply_urls: PropertyRef = PropertyRef(
        "reply_urls", description="Reply URLs registered for the service principal."
    )
    aws_identity_center_instance_id: PropertyRef = PropertyRef(
        "aws_identity_center_instance_id",
        description="AWS Identity Center instance ID derived from reply URLs.",
    )
    account_enabled: PropertyRef = PropertyRef(
        "account_enabled", description="Whether the service principal is enabled."
    )
    service_principal_type: PropertyRef = PropertyRef(
        "service_principal_type", description="Type of service principal."
    )
    app_owner_organization_id: PropertyRef = PropertyRef(
        "app_owner_organization_id",
        description="Tenant ID of the application's owning organization.",
    )
    login_url: PropertyRef = PropertyRef(
        "login_url", description="Login URL of the service principal."
    )
    preferred_single_sign_on_mode: PropertyRef = PropertyRef(
        "preferred_single_sign_on_mode",
        description="Preferred single sign-on mode.",
    )
    preferred_token_signing_key_thumbprint: PropertyRef = PropertyRef(
        "preferred_token_signing_key_thumbprint",
        description="Thumbprint of the preferred token-signing certificate.",
    )
    sign_in_audience: PropertyRef = PropertyRef(
        "sign_in_audience", description="Accounts allowed to sign in."
    )
    tags: PropertyRef = PropertyRef(
        "tags", description="Tags assigned to the service principal."
    )
    token_encryption_key_id: PropertyRef = PropertyRef(
        "token_encryption_key_id",
        description="Key ID used to encrypt issued tokens.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraServicePrincipalToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraServicePrincipalToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its service principals."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraServicePrincipalToTenantRelProperties = (
        EntraServicePrincipalToTenantRelProperties()
    )


@dataclass(frozen=True)
class ServicePrincipalToApplicationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ServicePrincipalToApplicationRel(CartographyRelSchema):
    """Links an Entra application to its deployed service principal."""

    target_node_label: str = "EntraApplication"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"app_id": PropertyRef("app_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "SERVICE_PRINCIPAL"
    properties: ServicePrincipalToApplicationRelProperties = (
        ServicePrincipalToApplicationRelProperties()
    )


@dataclass(frozen=True)
class ServicePrincipalToAWSIdentityCenterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ServicePrincipalToAWSIdentityCenterRel(CartographyRelSchema):
    """Links an Entra service principal to its federated AWS Identity Center."""

    target_node_label: str = "AWSIdentityCenter"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"identity_store_id": PropertyRef("aws_identity_center_instance_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FEDERATES_TO"
    properties: ServicePrincipalToAWSIdentityCenterRelProperties = (
        ServicePrincipalToAWSIdentityCenterRelProperties()
    )


@dataclass(frozen=True)
class EntraServicePrincipalSchema(CartographyNodeSchema):
    """A service principal in Microsoft Entra ID."""

    label: str = "EntraServicePrincipal"
    properties: EntraServicePrincipalNodeProperties = (
        EntraServicePrincipalNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ServiceAccount"])
    sub_resource_relationship: EntraServicePrincipalToTenantRel = (
        EntraServicePrincipalToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ServicePrincipalToApplicationRel(), ServicePrincipalToAWSIdentityCenterRel()]
    )
