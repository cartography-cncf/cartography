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
    id: PropertyRef = PropertyRef("id", description="CircleCI webhook ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Webhook name."
    )
    url: PropertyRef = PropertyRef("url", description="Webhook destination URL.")
    verify_tls: PropertyRef = PropertyRef(
        "verify_tls", description="Whether the webhook verifies TLS certificates."
    )
    has_signing_secret: PropertyRef = PropertyRef(
        "has_signing_secret",
        description="Whether the webhook has a signing secret configured.",
    )
    events: PropertyRef = PropertyRef(
        "events", description="Webhook event subscriptions."
    )


@dataclass(frozen=True)
class CircleCIWebhookToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CircleCIProject)-[:RESOURCE]->(:CircleCIWebhook)
class CircleCIWebhookToProjectRel(CartographyRelSchema):
    """The CircleCI project contains the outbound webhook."""

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
    """An outbound webhook configured for a CircleCI project."""

    label: str = "CircleCIWebhook"
    properties: CircleCIWebhookNodeProperties = CircleCIWebhookNodeProperties()
    sub_resource_relationship: CircleCIWebhookToProjectRel = (
        CircleCIWebhookToProjectRel()
    )
