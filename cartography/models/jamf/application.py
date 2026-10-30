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
class JamfApplicationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Tenant URI, then bundle ID and version: '<tenant>#<bundle id>@<version>'. "
            "Uses the application name when Jamf reports no bundle ID."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    bundle_id: PropertyRef = PropertyRef(
        "bundle_id",
        extra_index=True,
        description="macOS bundle identifier, e.g. com.google.Chrome.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Application name, e.g. Google Chrome.app.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Application version reported by Jamf inventory.",
    )
    mac_app_store: PropertyRef = PropertyRef(
        "mac_app_store",
        description="Whether the application was installed from the Mac App Store.",
    )
    external_version_id: PropertyRef = PropertyRef(
        "external_version_id",
        description="Mac App Store external version identifier, when present.",
    )


@dataclass(frozen=True)
class JamfApplicationToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfApplicationToTenantRel(CartographyRelSchema):
    """Links a Jamf tenant to an application seen in its inventory."""

    target_node_label: str = "JamfTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JamfApplicationToTenantRelProperties = (
        JamfApplicationToTenantRelProperties()
    )


@dataclass(frozen=True)
class JamfComputerHasAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfComputerHasAppRel(CartographyRelSchema):
    """Links a Jamf computer to an application installed on it."""

    target_node_label: str = "JamfComputer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("computer_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_APP"
    properties: JamfComputerHasAppRelProperties = JamfComputerHasAppRelProperties()


@dataclass(frozen=True)
class JamfApplicationSchema(CartographyNodeSchema):
    """An application version installed on one or more Jamf-managed computers."""

    label: str = "JamfApplication"
    properties: JamfApplicationNodeProperties = JamfApplicationNodeProperties()
    sub_resource_relationship: JamfApplicationToTenantRel = JamfApplicationToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [JamfComputerHasAppRel()]
    )
