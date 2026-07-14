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
class SentryReleaseNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Organization-scoped release version ID.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        extra_index=True,
        description="Full release version identifier.",
    )
    short_version: PropertyRef = PropertyRef(
        "shortVersion",
        description="Abbreviated release version.",
    )
    date_created: PropertyRef = PropertyRef(
        "date_created",
        description="ISO 8601 timestamp when the release was created.",
    )
    date_released: PropertyRef = PropertyRef(
        "date_released",
        description="ISO 8601 timestamp when the release was published.",
    )
    commit_count: PropertyRef = PropertyRef(
        "commitCount",
        description="Number of commits in the release.",
    )
    deploy_count: PropertyRef = PropertyRef(
        "deployCount",
        description="Number of deployments for the release.",
    )
    new_groups: PropertyRef = PropertyRef(
        "newGroups",
        description="Number of new issues introduced by the release.",
    )
    ref: PropertyRef = PropertyRef(
        "ref",
        description="Git reference associated with the release.",
    )
    url: PropertyRef = PropertyRef(
        "url",
        description="URL associated with the release.",
    )


@dataclass(frozen=True)
class SentryOrganizationToReleaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryOrganization)-[:RESOURCE]->(:SentryRelease)
@dataclass(frozen=True)
class SentryOrganizationToReleaseRel(CartographyRelSchema):
    """The organization contains the release."""

    target_node_label: str = "SentryOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SentryOrganizationToReleaseRelProperties = (
        SentryOrganizationToReleaseRelProperties()
    )


@dataclass(frozen=True)
class SentryReleaseSchema(CartographyNodeSchema):
    """A release in a Sentry organization."""

    label: str = "SentryRelease"
    properties: SentryReleaseNodeProperties = SentryReleaseNodeProperties()
    sub_resource_relationship: SentryOrganizationToReleaseRel = (
        SentryOrganizationToReleaseRel()
    )
