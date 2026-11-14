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
class LangSmithAgentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Synthetic identifier of the form <organization_id>|<agent_id>. Agent IDs are "
            "chosen by users, so two organizations can pick the same one; namespacing "
            "keeps their agents, deployments and credential paths from merging."
        ),
    )
    agent_id: PropertyRef = PropertyRef(
        "agent_id",
        extra_index=True,
        description="The user-assigned LangSmith agent ID, as used by the agent-auth API.",
    )
    name: PropertyRef = PropertyRef("name", description="Agent name.")
    agent_type: PropertyRef = PropertyRef(
        "agent_type", description="Agent type, for example CUSTOM or CODING."
    )
    source_type: PropertyRef = PropertyRef(
        "source_type",
        description=(
            "Where the agent runs: LSD (LangSmith Deployment), MDA (managed deep agent), "
            "FLEET, or EXTERNAL."
        ),
    )
    environments: PropertyRef = PropertyRef(
        "environments",
        description="Environments the agent has, for example production and staging.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the agent was created."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithAgentToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithWorkspace)-[:RESOURCE]->(:LangSmithAgent)
class LangSmithAgentToWorkspaceRel(CartographyRelSchema):
    """Links an agent to the workspace it belongs to."""

    target_node_label: str = "LangSmithWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithAgentToWorkspaceRelProperties = (
        LangSmithAgentToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAgentToDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithDeployment)-[:RUNS]->(:LangSmithAgent)
class LangSmithAgentToDeploymentRel(CartographyRelSchema):
    """
    Links an agent to the deployment serving it.

    Set from the deployment's agent block, which LangSmith fills only for deployments
    created with an explicit agent binding.

    One-to-many: an agent has one deployment per environment.
    """

    target_node_label: str = "LangSmithDeployment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("deployment_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RUNS"
    properties: LangSmithAgentToDeploymentRelProperties = (
        LangSmithAgentToDeploymentRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAgentToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithAgent)-[:OWNED_BY]->(:LangSmithUser)
class LangSmithAgentToUserRel(CartographyRelSchema):
    """An agent is owned by the user that registered it."""

    target_node_label: str = "LangSmithUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("owner_ls_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNED_BY"
    properties: LangSmithAgentToUserRelProperties = LangSmithAgentToUserRelProperties()


@dataclass(frozen=True)
class LangSmithAgentSchema(CartographyNodeSchema):
    """
    An agent registered in LangSmith that can hold OAuth credentials.

    Cartography reads agents from the control plane's agent registry. Deployments that
    declare an agent block, and credential records that name an agent, top up the
    inventory.
    """

    label: str = "LangSmithAgent"
    properties: LangSmithAgentNodeProperties = LangSmithAgentNodeProperties()
    sub_resource_relationship: LangSmithAgentToWorkspaceRel = (
        LangSmithAgentToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithAgentToDeploymentRel(),
            LangSmithAgentToUserRel(),
        ],
    )
