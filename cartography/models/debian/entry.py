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
class DebianSecurityTrackerEntryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "`<release>|<source package>|<CVE ID>`, for example "
            "`bookworm|tar|CVE-2005-2541`."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    cve_id: PropertyRef = PropertyRef(
        "cve_id",
        extra_index=True,
        description="CVE identifier.",
    )
    source_package: PropertyRef = PropertyRef(
        "source_package",
        extra_index=True,
        description=(
            "Debian source package the entry is for. Every binary package built from "
            "it shares the entry."
        ),
    )
    release: PropertyRef = PropertyRef(
        "release",
        description="Release codename, for example `bookworm`, `trixie` or `sid`.",
    )
    release_version: PropertyRef = PropertyRef(
        "release_version",
        extra_index=True,
        description=(
            "Major version of the release, for example `12` for bookworm, from a "
            "mapping kept in Cartography. Unset for sid, which never gets a version, "
            "and for a codename the mapping does not know."
        ),
    )
    status: PropertyRef = PropertyRef(
        "status",
        description=(
            "Tracker status in the release: `open` (affected and not fixed), "
            "`resolved` (fixed in `fixed_version`, or never affected when it is `0`) "
            "or `undetermined` (not yet analyzed)."
        ),
    )
    urgency: PropertyRef = PropertyRef(
        "urgency",
        description=(
            "Urgency the Debian security team assigned in the release, as published: "
            "`unimportant`, `low`, `medium`, `high`, `not yet assigned`, or "
            "`end-of-life` when the package has no security support in the release."
        ),
    )
    fixed_version: PropertyRef = PropertyRef(
        "fixed_version",
        description=(
            "Version that fixed the vulnerability in the release, as published. `0` "
            "means the release was never affected. Unset while the entry is open or "
            "undetermined."
        ),
    )
    not_affected: PropertyRef = PropertyRef(
        "not_affected",
        description="Whether the release was never affected (`fixed_version` is `0`).",
    )
    nodsa: PropertyRef = PropertyRef(
        "nodsa",
        description=(
            "Note the security team recorded when it decided not to issue a Debian "
            "Security Advisory for the release, for example `Minor issue`. Unset "
            "when there is no such decision."
        ),
    )
    nodsa_reason: PropertyRef = PropertyRef(
        "nodsa_reason",
        description=(
            "Kind of that decision: `postponed`, `ignored`, or an empty string for a "
            "plain no-DSA. Unset when `nodsa` is."
        ),
    )
    next_point_update: PropertyRef = PropertyRef(
        "next_point_update",
        description="Whether the fix is scheduled for the release's next point release.",
    )
    debianbug: PropertyRef = PropertyRef(
        "debianbug",
        description="Debian bug number filed for the vulnerability, when there is one.",
    )


@dataclass(frozen=True)
class DebianSecurityTrackerEntryToFeedRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DebianSecurityTrackerEntryToFeedRel(CartographyRelSchema):
    """Links the Debian security tracker feed to an entry read from it."""

    target_node_label: str = "DebianSecurityTrackerFeed"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("FEED_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DebianSecurityTrackerEntryToFeedRelProperties = (
        DebianSecurityTrackerEntryToFeedRelProperties()
    )


@dataclass(frozen=True)
class DebianSecurityTrackerEntrySchema(CartographyNodeSchema):
    """
    The Debian security tracker's state of one CVE in one source package and one
    Debian release. Entries are kept only for CVEs already in the graph, and carry
    no `CVE` label: whether one applies to an image depends on the image's release.
    """

    label: str = "DebianSecurityTrackerEntry"
    properties: DebianSecurityTrackerEntryNodeProperties = (
        DebianSecurityTrackerEntryNodeProperties()
    )
    sub_resource_relationship: DebianSecurityTrackerEntryToFeedRel = (
        DebianSecurityTrackerEntryToFeedRel()
    )
