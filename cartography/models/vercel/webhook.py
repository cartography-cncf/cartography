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
class VercelWebhookNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    url: PropertyRef = PropertyRef("url", extra_index=True)
    events: PropertyRef = PropertyRef("events")
    project_ids: PropertyRef = PropertyRef("projectIds")
    created_at: PropertyRef = PropertyRef("createdAt")
    updated_at: PropertyRef = PropertyRef("updatedAt")


@dataclass(frozen=True)
class VercelWebhookToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelWebhook)
class VercelWebhookToTeamRel(CartographyRelSchema):
    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelWebhookToTeamRelProperties = VercelWebhookToTeamRelProperties()


@dataclass(frozen=True)
class VercelWebhookToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelWebhook)-[:WATCHES]->(:VercelProject)
class VercelWebhookToProjectRel(CartographyRelSchema):
    target_node_label: str = "VercelProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("projectIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WATCHES"
    properties: VercelWebhookToProjectRelProperties = (
        VercelWebhookToProjectRelProperties()
    )


@dataclass(frozen=True)
class VercelWebhookSchema(CartographyNodeSchema):
    label: str = "VercelWebhook"
    properties: VercelWebhookNodeProperties = VercelWebhookNodeProperties()
    sub_resource_relationship: VercelWebhookToTeamRel = VercelWebhookToTeamRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [VercelWebhookToProjectRel()],
    )
