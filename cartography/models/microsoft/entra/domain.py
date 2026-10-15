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
class EntraDomainNodeProperties(CartographyNodeProperties):
    # A domain name is not unique across tenants: an unverified domain can be
    # added to several, so the tenant is part of the identity.
    id: PropertyRef = PropertyRef(
        "id", description="Tenant ID and lowercase domain name, joined by a slash."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Lowercase fully qualified domain name."
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID",
        set_in_kwargs=True,
        description="ID of the Entra tenant the domain belongs to.",
    )
    authentication_type: PropertyRef = PropertyRef(
        "authentication_type",
        description="`Managed` when Entra ID authenticates the domain's users, "
        "`Federated` when an external identity provider such as AD FS or Okta does.",
    )
    is_default: PropertyRef = PropertyRef(
        "is_default",
        description="Whether the domain is the tenant's default for new users.",
    )
    is_initial: PropertyRef = PropertyRef(
        "is_initial",
        description="Whether the domain is the `onmicrosoft.com` domain Microsoft "
        "created with the tenant.",
    )
    is_root: PropertyRef = PropertyRef(
        "is_root",
        description="Whether the domain is a verified root domain rather than a "
        "subdomain.",
    )
    is_verified: PropertyRef = PropertyRef(
        "is_verified",
        description="Whether the tenant has proven ownership of the domain.",
    )
    is_admin_managed: PropertyRef = PropertyRef(
        "is_admin_managed",
        description="Whether DNS record management is delegated to Microsoft 365.",
    )
    supported_services: PropertyRef = PropertyRef(
        "supported_services",
        description="Services the domain is configured for, such as `Email` or "
        "`OfficeCommunicationsOnline`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraTenantToDomainRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraDomain)<-[:RESOURCE]-(:AzureTenant)
class EntraDomainToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its domains."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraTenantToDomainRelProperties = EntraTenantToDomainRelProperties()


@dataclass(frozen=True)
class EntraDomainSchema(CartographyNodeSchema):
    """A domain name added to a Microsoft Entra tenant."""

    label: str = "EntraDomain"
    properties: EntraDomainNodeProperties = EntraDomainNodeProperties()
    sub_resource_relationship: EntraDomainToTenantRel = EntraDomainToTenantRel()
