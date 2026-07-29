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
class DopplerWebhookNodeProperties(CartographyNodeProperties):
    # The webhook `secret` field is intentionally never ingested.
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    url: PropertyRef = PropertyRef("url")
    enabled: PropertyRef = PropertyRef("enabled")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DopplerWebhookToWorkplaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerWorkplace)-[:RESOURCE]->(:DopplerWebhook)
class DopplerWebhookToWorkplaceRel(CartographyRelSchema):
    target_node_label: str = "DopplerWorkplace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKPLACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DopplerWebhookToWorkplaceRelProperties = (
        DopplerWebhookToWorkplaceRelProperties()
    )


@dataclass(frozen=True)
class DopplerWebhookToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DopplerProject)-[:HAS_WEBHOOK]->(:DopplerWebhook)
class DopplerWebhookToProjectRel(CartographyRelSchema):
    target_node_label: str = "DopplerProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"slug": PropertyRef("project")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_WEBHOOK"
    properties: DopplerWebhookToProjectRelProperties = (
        DopplerWebhookToProjectRelProperties()
    )


@dataclass(frozen=True)
class DopplerWebhookSchema(CartographyNodeSchema):
    label: str = "DopplerWebhook"
    properties: DopplerWebhookNodeProperties = DopplerWebhookNodeProperties()
    sub_resource_relationship: DopplerWebhookToWorkplaceRel = (
        DopplerWebhookToWorkplaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [DopplerWebhookToProjectRel()],
    )
