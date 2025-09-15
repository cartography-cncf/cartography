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
class EntraServicePrincipalNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    app_id: PropertyRef = PropertyRef("app_id")
    display_name: PropertyRef = PropertyRef("display_name")
    reply_urls: PropertyRef = PropertyRef("reply_urls")
    aws_identity_center_instance_id: PropertyRef = PropertyRef(
        "aws_identity_center_instance_id"
    )
    account_enabled: PropertyRef = PropertyRef("account_enabled")
    service_principal_type: PropertyRef = PropertyRef("service_principal_type")
    app_owner_organization_id: PropertyRef = PropertyRef("app_owner_organization_id")
    login_url: PropertyRef = PropertyRef("login_url")
    preferred_single_sign_on_mode: PropertyRef = PropertyRef(
        "preferred_single_sign_on_mode"
    )
    preferred_token_signing_key_thumbprint: PropertyRef = PropertyRef(
        "preferred_token_signing_key_thumbprint"
    )
    sign_in_audience: PropertyRef = PropertyRef("sign_in_audience")
    tags: PropertyRef = PropertyRef("tags")
    token_encryption_key_id: PropertyRef = PropertyRef("token_encryption_key_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraServicePrincipalToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraServicePrincipalToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
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
    label: str = "EntraServicePrincipal"
    properties: EntraServicePrincipalNodeProperties = (
        EntraServicePrincipalNodeProperties()
    )
    sub_resource_relationship: EntraServicePrincipalToTenantRel = (
        EntraServicePrincipalToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ServicePrincipalToApplicationRel(), ServicePrincipalToAWSIdentityCenterRel()]
    )
