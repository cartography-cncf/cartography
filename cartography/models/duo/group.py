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
class DuoGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("group_id", description="Duo group ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    desc: PropertyRef = PropertyRef("desc", description="Group description.")
    group_id: PropertyRef = PropertyRef(
        "group_id", extra_index=True, description="Duo group ID."
    )
    mobile_otp_enabled: PropertyRef = PropertyRef(
        "mobile_otp_enabled",
        description="Legacy mobile OTP setting, which is always false.",
    )
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Group name.")
    push_enabled: PropertyRef = PropertyRef(
        "push_enabled",
        description="Legacy push setting, which is always false.",
    )
    sms_enabled: PropertyRef = PropertyRef(
        "sms_enabled",
        description="Legacy SMS setting, which is always false.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="Group authentication status."
    )
    voice_enabled: PropertyRef = PropertyRef(
        "voice_enabled",
        description="Legacy voice setting, which is always false.",
    )


@dataclass(frozen=True)
class DuoGroupToDuoApiHostRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoGroupToDuoApiHostRel(CartographyRelSchema):
    """The Duo API host contains the group."""

    target_node_label: str = "DuoApiHost"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("DUO_API_HOSTNAME", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DuoGroupToDuoApiHostRelProperties = DuoGroupToDuoApiHostRelProperties()


@dataclass(frozen=True)
class DuoGroupSchema(CartographyNodeSchema):
    """A user group in Duo."""

    label: str = "DuoGroup"
    properties: DuoGroupNodeProperties = DuoGroupNodeProperties()
    sub_resource_relationship: DuoGroupToDuoApiHostRel = DuoGroupToDuoApiHostRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserGroup"])
