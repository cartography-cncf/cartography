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
class DatabricksGitCredentialNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Workspace-scoped identifier for the Git credential."
    )
    credential_id: PropertyRef = PropertyRef(
        "credential_id",
        extra_index=True,
        description="Databricks Git credential identifier.",
    )
    git_provider: PropertyRef = PropertyRef(
        "git_provider", description="Git provider associated with the credential."
    )
    git_username: PropertyRef = PropertyRef(
        "git_username",
        extra_index=True,
        description="Git user name associated with the credential.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DatabricksGitCredentialToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:DatabricksWorkspace)-[:RESOURCE]->(:DatabricksGitCredential)
class DatabricksGitCredentialToWorkspaceRel(CartographyRelSchema):
    """A Databricks workspace contains the Git credential as a resource."""

    target_node_label: str = "DatabricksWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: DatabricksGitCredentialToWorkspaceRelProperties = (
        DatabricksGitCredentialToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class DatabricksGitCredentialSchema(CartographyNodeSchema):
    """A credential used to authenticate to a Git provider from Databricks."""

    label: str = "DatabricksGitCredential"
    properties: DatabricksGitCredentialNodeProperties = (
        DatabricksGitCredentialNodeProperties()
    )
    sub_resource_relationship: DatabricksGitCredentialToWorkspaceRel = (
        DatabricksGitCredentialToWorkspaceRel()
    )
