from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class EntraUserToServicePrincipalAuthorizedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    scopes: PropertyRef = PropertyRef(
        "scopes",
        description=(
            "Delegated permissions the user consented to, across every API the app "
            "asked for. Microsoft Graph permissions are qualified the way they are "
            "requested (https://graph.microsoft.com/Mail.Read); others by the API's "
            "app id (<appId>/<permission>)."
        ),
    )
    # The ontology job that derives AUTHORIZED from app role assignments marks its
    # edges with match_method and cleans up only those. A consent grant can land on an
    # edge that job created; clearing the marker hands the edge to this sync.
    match_method: PropertyRef = PropertyRef("match_method")


@dataclass(frozen=True)
class EntraUserToServicePrincipalAuthorizedMatchLink(CartographyRelSchema):
    """A user consented to an app's delegated permissions (an OAuth2 permission grant)."""

    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("client_id")},
    )
    source_node_label: str = "EntraUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AUTHORIZED"
    properties: EntraUserToServicePrincipalAuthorizedRelProperties = (
        EntraUserToServicePrincipalAuthorizedRelProperties()
    )


@dataclass(frozen=True)
class EntraTenantToServicePrincipalAdminConsentedRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    scopes: PropertyRef = PropertyRef(
        "scopes",
        description=(
            "Delegated permissions an administrator consented to on behalf of every "
            "user, qualified like AUTHORIZED.scopes."
        ),
    )


@dataclass(frozen=True)
class EntraTenantToServicePrincipalAdminConsentedMatchLink(CartographyRelSchema):
    """
    An administrator consented to an app's delegated permissions for every user.

    Kept on the tenant rather than fanned out to an AUTHORIZED edge per user: the
    grant covers users who join later, and the fan-out would be users x apps.
    """

    target_node_label: str = "EntraServicePrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("client_id")},
    )
    source_node_label: str = "AzureTenant"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("tenant_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_CONSENTED"
    properties: EntraTenantToServicePrincipalAdminConsentedRelProperties = (
        EntraTenantToServicePrincipalAdminConsentedRelProperties()
    )
