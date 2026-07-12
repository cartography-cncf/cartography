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
class CircleCIWebhookNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    url: PropertyRef = PropertyRef("url")
    verify_tls: PropertyRef = PropertyRef("verify_tls")
    has_signing_secret: PropertyRef = PropertyRef("has_signing_secret")
    events: PropertyRef = PropertyRef("events")


@dataclass(frozen=True)
class CircleCIWebhookToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCIWebhook)
class CircleCIWebhookToProjectRel(CartographyRelSchema):
    target_node_label: str = "CircleCIProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CircleCIWebhookToProjectRelProperties = (
        CircleCIWebhookToProjectRelProperties()
    )


@dataclass(frozen=True)
class CircleCIWebhookSchema(CartographyNodeSchema):
    label: str = "CircleCIWebhook"
    properties: CircleCIWebhookNodeProperties = CircleCIWebhookNodeProperties()
    sub_resource_relationship: CircleCIWebhookToProjectRel = (
        CircleCIWebhookToProjectRel()
    )
