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
class GitHubWebhookNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="GitHub REST API URL of the webhook."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    hook_id: PropertyRef = PropertyRef("hook_id", description="GitHub webhook ID.")
    scope: PropertyRef = PropertyRef(
        "scope",
        extra_index=True,
        description="Where the webhook is configured: `organization` or `repository`.",
    )
    name: PropertyRef = PropertyRef(
        "name", description="Webhook type name. Always `web` for HTTP webhooks."
    )
    active: PropertyRef = PropertyRef(
        "active", description="Whether GitHub delivers events to the webhook."
    )
    events: PropertyRef = PropertyRef(
        "events", description="Events that trigger the webhook. `*` means all events."
    )
    content_type: PropertyRef = PropertyRef(
        "content_type", description="Payload format: `json` or `form`."
    )
    target_scheme: PropertyRef = PropertyRef(
        "target_scheme",
        description="URL scheme of the delivery target, such as `https`.",
    )
    target_host: PropertyRef = PropertyRef(
        "target_host",
        extra_index=True,
        description="Host of the delivery target. The path and query are not stored because they often contain credentials.",
    )
    uses_https: PropertyRef = PropertyRef(
        "uses_https", description="Whether payloads are delivered over HTTPS."
    )
    insecure_ssl: PropertyRef = PropertyRef(
        "insecure_ssl",
        description="Whether TLS certificate verification is disabled for deliveries.",
    )
    has_secret: PropertyRef = PropertyRef(
        "has_secret",
        description="Whether a secret is configured to sign payloads. GitHub never returns the secret value.",
    )
    last_response_code: PropertyRef = PropertyRef(
        "last_response_code",
        description="HTTP status of the latest delivery. Repository webhooks only.",
    )
    last_response_status: PropertyRef = PropertyRef(
        "last_response_status",
        description="Status of the latest delivery, such as `active`. Repository webhooks only.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the webhook was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the webhook was last updated."
    )


@dataclass(frozen=True)
class GitHubWebhookRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubWebhookToOrgRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubWebhookRelProperties = GitHubWebhookRelProperties()


@dataclass(frozen=True)
class GitHubOrganizationToWebhookRel(CartographyRelSchema):
    """Links an organization to a webhook configured at the organization level."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_WEBHOOK"
    properties: GitHubWebhookRelProperties = GitHubWebhookRelProperties()


@dataclass(frozen=True)
class GitHubRepositoryToWebhookRel(CartographyRelSchema):
    """Links a repository to a webhook configured on it."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_WEBHOOK"
    properties: GitHubWebhookRelProperties = GitHubWebhookRelProperties()


@dataclass(frozen=True)
class GitHubWebhookSchema(CartographyNodeSchema):
    """An HTTP webhook configured on a GitHub organization or repository."""

    label: str = "GitHubWebhook"
    properties: GitHubWebhookNodeProperties = GitHubWebhookNodeProperties()
    sub_resource_relationship: GitHubWebhookToOrgRel = GitHubWebhookToOrgRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubOrganizationToWebhookRel(), GitHubRepositoryToWebhookRel()],
    )
