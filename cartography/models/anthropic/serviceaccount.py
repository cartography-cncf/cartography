from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import SERVICE_ACCOUNT


@dataclass(frozen=True)
class AnthropicServiceAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic service account ID.")
    name: PropertyRef = PropertyRef("name", description="Service account name.")
    description: PropertyRef = PropertyRef(
        "description",
        description="Free-text description of the service account.",
    )
    organization_role: PropertyRef = PropertyRef(
        "organization_role",
        description=(
            "Organization-level role: admin or developer. Only an admin service "
            "account can back a federation rule carrying the org:admin scope."
        ),
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the service account was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the service account was last updated.",
    )
    archived_at: PropertyRef = PropertyRef(
        "archived_at",
        description=(
            "RFC 3339 timestamp when the service account was archived. Empty while "
            "the service account is live."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicServiceAccountToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicOrganization)-[:RESOURCE]->(:AnthropicServiceAccount)
class AnthropicServiceAccountToOrganizationRel(CartographyRelSchema):
    """The organization contains the service account."""

    target_node_label: str = "AnthropicOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicServiceAccountToOrganizationRelProperties = (
        AnthropicServiceAccountToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class AnthropicServiceAccountToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicServiceAccount)-[:MEMBER_OF]->(:AnthropicWorkspace)
class AnthropicServiceAccountToWorkspaceRel(CartographyRelSchema):
    """A service account is a member of a workspace.

    Membership is what lets a federated token act in a workspace: enabling a
    federation rule for a workspace does not grant it.
    """

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspaces", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: AnthropicServiceAccountToWorkspaceRelProperties = (
        AnthropicServiceAccountToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicServiceAccountToWorkspaceAdminRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicServiceAccount)-[:ADMIN_OF]->(:AnthropicWorkspace)
class AnthropicServiceAccountToWorkspaceAdminRel(CartographyRelSchema):
    """A service account administers a workspace."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workspace_admins", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ADMIN_OF"
    properties: AnthropicServiceAccountToWorkspaceAdminRelProperties = (
        AnthropicServiceAccountToWorkspaceAdminRelProperties()
    )


@dataclass(frozen=True)
class AnthropicServiceAccountSchema(CartographyNodeSchema):
    """A non-human principal in an Anthropic organization.

    Service accounts are the target of Workload Identity Federation: a federated
    token exchange mints a token that acts as one. Only readable with an org:admin
    OAuth token, never with an Admin API key.
    """

    label: str = "AnthropicServiceAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SERVICE_ACCOUNT])
    properties: AnthropicServiceAccountNodeProperties = (
        AnthropicServiceAccountNodeProperties()
    )
    sub_resource_relationship: AnthropicServiceAccountToOrganizationRel = (
        AnthropicServiceAccountToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicServiceAccountToWorkspaceRel(),
            AnthropicServiceAccountToWorkspaceAdminRel(),
        ],
    )
