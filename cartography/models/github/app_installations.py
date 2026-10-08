from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import THIRD_PARTY_APP


@dataclass(frozen=True)
class GitHubAppInstallationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable identifier derived from the organization and installation ID.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    installation_id: PropertyRef = PropertyRef(
        "installation_id", extra_index=True, description="GitHub installation ID."
    )
    app_id: PropertyRef = PropertyRef(
        "app_id", extra_index=True, description="GitHub App ID."
    )
    app_slug: PropertyRef = PropertyRef(
        "app_slug", extra_index=True, description="GitHub App slug."
    )
    client_id: PropertyRef = PropertyRef(
        "client_id", description="GitHub App OAuth client ID."
    )
    target_type: PropertyRef = PropertyRef(
        "target_type",
        description="Account type the App is installed on, such as `Organization`.",
    )
    repository_selection: PropertyRef = PropertyRef(
        "repository_selection",
        description="Repositories the installation can access: `all` or `selected`.",
    )
    permissions: PropertyRef = PropertyRef(
        "permissions",
        description="Granted permissions and access levels encoded as JSON.",
    )
    read_permissions: PropertyRef = PropertyRef(
        "read_permissions", description="Permissions granted with `read` access."
    )
    write_permissions: PropertyRef = PropertyRef(
        "write_permissions",
        description="Permissions granted with `write` or `admin` access.",
    )
    admin_permissions: PropertyRef = PropertyRef(
        "admin_permissions", description="Permissions granted with `admin` access."
    )
    events: PropertyRef = PropertyRef(
        "events", description="Webhook events the App subscribes to."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled", description="Whether the installation is active (not suspended)."
    )
    suspended_at: PropertyRef = PropertyRef(
        "suspended_at", description="Timestamp when the installation was suspended."
    )
    suspended_by: PropertyRef = PropertyRef(
        "suspended_by", description="Login of the user who suspended the installation."
    )
    html_url: PropertyRef = PropertyRef(
        "html_url", description="Installation settings page URL."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the App was installed."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the installation was last updated."
    )


@dataclass(frozen=True)
class GitHubAppInstallationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubAppInstallationToOrgRel(CartographyRelSchema):
    """Scopes a GitHub resource to its organization."""

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubAppInstallationRelProperties = (
        GitHubAppInstallationRelProperties()
    )


@dataclass(frozen=True)
class GitHubAppInstallationSchema(CartographyNodeSchema):
    """
    A GitHub App installed on an organization, with the permissions it was granted.

    > **Ontology Mapping**: This node has the extra label `ThirdPartyApp` to enable
    > cross-platform queries for third-party applications across providers.
    """

    label: str = "GitHubAppInstallation"
    properties: GitHubAppInstallationNodeProperties = (
        GitHubAppInstallationNodeProperties()
    )
    sub_resource_relationship: GitHubAppInstallationToOrgRel = (
        GitHubAppInstallationToOrgRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([THIRD_PARTY_APP])
