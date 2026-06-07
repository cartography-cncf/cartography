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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    version: PropertyRef = PropertyRef("version", extra_index=True)
    short_version: PropertyRef = PropertyRef("shortVersion")
    date_created: PropertyRef = PropertyRef("date_created")
    date_released: PropertyRef = PropertyRef("date_released")
    commit_count: PropertyRef = PropertyRef("commitCount")
    deploy_count: PropertyRef = PropertyRef("deployCount")
    new_groups: PropertyRef = PropertyRef("newGroups")
    ref: PropertyRef = PropertyRef("ref")
    url: PropertyRef = PropertyRef("url")


@dataclass(frozen=True)
class SentryOrganizationToReleaseRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:SentryOrganization)-[:RESOURCE]->(:SentryRelease)
@dataclass(frozen=True)
class SentryOrganizationToReleaseRel(CartographyRelSchema):
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
    label: str = "SentryRelease"
    properties: SentryReleaseNodeProperties = SentryReleaseNodeProperties()
    sub_resource_relationship: SentryOrganizationToReleaseRel = (
        SentryOrganizationToReleaseRel()
    )
