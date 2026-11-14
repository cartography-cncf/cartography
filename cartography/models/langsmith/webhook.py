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
class LangSmithWebhookNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "The prompt webhook UUID, or <rule_id>|<index> for a webhook on an "
            "automation rule."
        ),
    )
    source: PropertyRef = PropertyRef(
        "source",
        description="What sends to the webhook: run_rule (an automation) or prompt.",
    )
    scheme: PropertyRef = PropertyRef(
        "scheme", description="URL scheme, for example https."
    )
    host: PropertyRef = PropertyRef(
        "host",
        extra_index=True,
        description=(
            "Host the webhook delivers to. The path, query, and headers are never "
            "ingested, because webhook URLs often embed a secret."
        ),
    )
    rule_name: PropertyRef = PropertyRef(
        "rule_name", description="Name of the automation rule that sends runs."
    )
    project_name: PropertyRef = PropertyRef(
        "project_name", description="Tracing project whose runs the rule sends."
    )
    dataset_name: PropertyRef = PropertyRef(
        "dataset_name", description="Dataset whose runs the rule sends."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the webhook currently sends."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the webhook was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithWebhookToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:RESOURCE]->(:LangSmithWebhook)
class LangSmithWebhookToWorkspaceRel(CartographyRelSchema):
    """Links a webhook to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithWebhookToWorkspaceRelProperties = (
        LangSmithWebhookToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithWebhookSchema(CartographyNodeSchema):
    """An endpoint outside LangSmith that receives runs or prompt changes."""

    label: str = "LangSmithWebhook"
    properties: LangSmithWebhookNodeProperties = LangSmithWebhookNodeProperties()
    sub_resource_relationship: LangSmithWebhookToWorkspaceRel = (
        LangSmithWebhookToWorkspaceRel()
    )
