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
        "id", description="Agent ID, also referred to as the assistant ID."
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Agent name, taken from the deployment that serves it when one exists.",
    )
    environment: PropertyRef = PropertyRef(
        "environment",
        description="Environment the agent is deployed to, for example production.",
    )
    graph_id: PropertyRef = PropertyRef(
        "graph_id", description="Identifier of the LangGraph graph this agent runs."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Human-readable description of the agent."
    )
    version: PropertyRef = PropertyRef(
        "version", description="Assistant version number."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Timestamp when the assistant was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Timestamp when the assistant was last updated."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class LangSmithAgentToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithOrganization)-[:RESOURCE]->(:LangSmithAgent)
class LangSmithAgentToOrganizationRel(CartographyRelSchema):
    """Links an organization to an agent running within it."""

    target_node_label: str = "LangSmithOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: LangSmithAgentToOrganizationRelProperties = (
        LangSmithAgentToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class LangSmithAgentToDeploymentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:LangSmithDeployment)-[:RUNS]->(:LangSmithAgent)
class LangSmithAgentToDeploymentRel(CartographyRelSchema):
    """
    Links an agent to the deployment serving it.

    Set when the agent was discovered by listing the deployment's assistants, which is the
    usual case; a deployment's own agent block is populated only for deployments created
    with an explicit agent binding.

    One-to-many: LangGraph derives an assistant id from its graph, so the same agent can be
    served by several deployments.
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
class LangSmithAgentSchema(CartographyNodeSchema):
    """
    An agent (assistant) that can hold OAuth credentials.

    Agents are discovered by listing each deployment's assistants on its own data plane,
    since a LangGraph Platform agent id is an assistant id and the control plane does not
    expose it. Deployments that declare an agent block, and credential records that name an
    agent, top up the inventory.
    """

    label: str = "LangSmithAgent"
    properties: LangSmithAgentNodeProperties = LangSmithAgentNodeProperties()
    sub_resource_relationship: LangSmithAgentToOrganizationRel = (
        LangSmithAgentToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            LangSmithAgentToDeploymentRel(),
        ],
    )
