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
class GoogleWorkspaceAppsScriptProjectNodeProperties(CartographyNodeProperties):
    """
    Google Workspace Apps Script project node properties
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Unique Google Apps Script project ID (Drive file ID).",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography update.",
    )
    title: PropertyRef = PropertyRef(
        "title",
        description="Title of the Apps Script project.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time",
        description="Time when the Apps Script project was created.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="Time when the Apps Script project was last updated.",
    )
    parent_id: PropertyRef = PropertyRef(
        "parent_id",
        description="Drive ID of the parent folder or container, if any.",
    )
    creator_email: PropertyRef = PropertyRef(
        "creator_email",
        description="Email address of the Apps Script project creator.",
    )
    versioned_deployment_count: PropertyRef = PropertyRef(
        "versioned_deployment_count",
        description="Number of versioned deployments for the Apps Script project.",
    )
    webapp_access: PropertyRef = PropertyRef(
        "webapp_access",
        description="Widest access level among versioned web app entry points.",
    )
    webapp_execute_as: PropertyRef = PropertyRef(
        "webapp_execute_as",
        description="Execution identity of the widest-access versioned web app entry point.",
    )
    is_anonymous_webapp_running_as_deployer: PropertyRef = PropertyRef(
        "is_anonymous_webapp_running_as_deployer",
        description=(
            "Whether the project has a versioned web app that anyone can open "
            "anonymously and that executes as the user who deployed it "
            "(executeAs USER_DEPLOYING). The deployer is usually, but not "
            "necessarily, the owner: any editor can deploy."
        ),
    )
    api_executable_access: PropertyRef = PropertyRef(
        "api_executable_access",
        description="Widest access level among versioned Execution API entry points.",
    )
    customer_id: PropertyRef = PropertyRef(
        "CUSTOMER_ID",
        set_in_kwargs=True,
        description="ID of the Google Workspace tenant that contains the project.",
    )


@dataclass(frozen=True)
class GoogleWorkspaceAppsScriptProjectToTenantRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace Apps Script project to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceAppsScriptProjectToTenantRel(CartographyRelSchema):
    """A Google Workspace tenant contains an Apps Script project."""

    target_node_label: str = "GoogleWorkspaceTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GoogleWorkspaceAppsScriptProjectToTenantRelProperties = (
        GoogleWorkspaceAppsScriptProjectToTenantRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceUserToAppsScriptProjectRelProperties(CartographyRelProperties):
    """
    Properties for Google Workspace user to Apps Script project relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GoogleWorkspaceUserToAppsScriptProjectRel(CartographyRelSchema):
    """A Google Workspace user owns a standalone Apps Script project."""

    target_node_label: str = "GoogleWorkspaceUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("owner_user_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "OWNS"
    properties: GoogleWorkspaceUserToAppsScriptProjectRelProperties = (
        GoogleWorkspaceUserToAppsScriptProjectRelProperties()
    )


@dataclass(frozen=True)
class GoogleWorkspaceAppsScriptProjectSchema(CartographyNodeSchema):
    """
    A standalone Google Apps Script project in Google Workspace.

    Cartography finds projects through each user's Google Drive file list, so
    container-bound scripts attached to a Google Doc, Sheet, or Form are out of
    scope. Deployments are summarized as project properties. Deployment IDs,
    web app URLs, and script source code are not stored, because the URL of an
    anonymous web app is enough to run it.
    """

    label: str = "GoogleWorkspaceAppsScriptProject"
    properties: GoogleWorkspaceAppsScriptProjectNodeProperties = (
        GoogleWorkspaceAppsScriptProjectNodeProperties()
    )
    sub_resource_relationship: GoogleWorkspaceAppsScriptProjectToTenantRel = (
        GoogleWorkspaceAppsScriptProjectToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GoogleWorkspaceUserToAppsScriptProjectRel(),
        ]
    )
