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
class DuoTokenNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("token_id", description="Duo hardware token ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    admins: PropertyRef = PropertyRef(
        "admins", description="Administrators associated with the hardware token."
    )
    serial: PropertyRef = PropertyRef(
        "serial", extra_index=True, description="Hardware token serial number."
    )
    token_id: PropertyRef = PropertyRef(
        "token_id", extra_index=True, description="Duo hardware token ID."
    )
    totp_step: PropertyRef = PropertyRef(
        "totp_step", description="TOTP step value, which is null for supported tokens."
    )
    type: PropertyRef = PropertyRef("type", description="Hardware token type.")


@dataclass(frozen=True)
class DuoTokenToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoTokenToDuoApiHostRel(CartographyRelSchema):
    """The Duo API host contains the hardware token."""

    target_node_label: str = "DuoApiHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DUO_API_HOSTNAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoTokenToDuoApiHostRelProperties = DuoTokenToDuoApiHostRelProperties()


class DuoTokenToDuoUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoTokenToDuoUserRel(CartographyRelSchema):
    """The Duo user has the hardware token."""

    target_node_label: str = "DuoUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"user_id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_DUO_TOKEN"
    properties: DuoTokenToDuoUserRelProperties = DuoTokenToDuoUserRelProperties()


@dataclass(frozen=True)
class DuoTokenSchema(CartographyNodeSchema):
    """A hardware token registered in Duo."""

    label: str = "DuoToken"
    properties: DuoTokenNodeProperties = DuoTokenNodeProperties()
    sub_resource_relationship: DuoTokenToDuoApiHostRel = DuoTokenToDuoApiHostRel()
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            DuoTokenToDuoUserRel(),
        ],
    )
