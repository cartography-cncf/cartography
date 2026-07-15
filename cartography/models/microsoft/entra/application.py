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
class EntraApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Entra application object ID.")
    app_id: PropertyRef = PropertyRef("app_id", description="Application client ID.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the application."
    )
    publisher_domain: PropertyRef = PropertyRef(
        "publisher_domain", description="Verified publisher domain of the application."
    )
    sign_in_audience: PropertyRef = PropertyRef(
        "sign_in_audience",
        description="Accounts allowed to sign in to the application.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraApplicationToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraApplicationToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its Entra applications."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraApplicationToTenantRelProperties = (
        EntraApplicationToTenantRelProperties()
    )


@dataclass(frozen=True)
class EntraApplicationSchema(CartographyNodeSchema):
    """An application registration in Microsoft Entra ID."""

    label: str = "EntraApplication"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ThirdPartyApp"])
    properties: EntraApplicationNodeProperties = EntraApplicationNodeProperties()
    sub_resource_relationship: EntraApplicationToTenantRel = (
        EntraApplicationToTenantRel()
    )
