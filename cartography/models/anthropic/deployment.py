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
class AnthropicDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Anthropic deployment ID.")
    status: PropertyRef = PropertyRef(
        "status",
        description="Whether the deployment is active or paused.",
    )
    paused_reason: PropertyRef = PropertyRef(
        "paused_reason", description="Why the deployment was paused."
    )
    schedule_type: PropertyRef = PropertyRef(
        "schedule.type", description="Trigger type, currently always cron."
    )
    schedule_expression: PropertyRef = PropertyRef(
        "schedule.expression",
        description="Cron expression the agent is run on.",
    )
    schedule_timezone: PropertyRef = PropertyRef(
        "schedule.timezone", description="Timezone the cron expression is read in."
    )
    schedule_last_run_at: PropertyRef = PropertyRef(
        "schedule.last_run_at",
        description="RFC 3339 timestamp of the most recent scheduled run.",
    )
    agent_id: PropertyRef = PropertyRef(
        "agent.id", description="Agent this deployment runs."
    )
    agent_version: PropertyRef = PropertyRef(
        "agent.version", description="Pinned version of the agent definition."
    )
    environment_id: PropertyRef = PropertyRef(
        "environment_id", description="Environment the deployment runs in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="RFC 3339 timestamp when the deployment was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the deployment was last updated.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AnthropicDeploymentToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicWorkspace)-[:RESOURCE]->(:AnthropicDeployment)
class AnthropicDeploymentToWorkspaceRel(CartographyRelSchema):
    """The workspace the deployment belongs to."""

    target_node_label: str = "AnthropicWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AnthropicDeploymentToWorkspaceRelProperties = (
        AnthropicDeploymentToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class AnthropicDeploymentToAgentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicDeployment)-[:RUNS]->(:AnthropicAgent)
class AnthropicDeploymentToAgentRel(CartographyRelSchema):
    """The agent this deployment runs on a schedule."""

    target_node_label: str = "AnthropicAgent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("agent.id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS"
    properties: AnthropicDeploymentToAgentRelProperties = (
        AnthropicDeploymentToAgentRelProperties()
    )


@dataclass(frozen=True)
class AnthropicDeploymentToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicDeployment)-[:RUNS_IN]->(:AnthropicEnvironment)
class AnthropicDeploymentToEnvironmentRel(CartographyRelSchema):
    """The sandbox the deployment executes in, and so the egress policy it inherits."""

    target_node_label: str = "AnthropicEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environment_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_IN"
    properties: AnthropicDeploymentToEnvironmentRelProperties = (
        AnthropicDeploymentToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class AnthropicDeploymentToVaultRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AnthropicDeployment)-[:USES_VAULT]->(:AnthropicVault)
class AnthropicDeploymentToVaultRel(CartographyRelSchema):
    """A vault the deployment can draw credentials from."""

    target_node_label: str = "AnthropicVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vault_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_VAULT"
    properties: AnthropicDeploymentToVaultRelProperties = (
        AnthropicDeploymentToVaultRelProperties()
    )


@dataclass(frozen=True)
class AnthropicDeploymentSchema(CartographyNodeSchema):
    """A scheduled, unattended run of an agent.

    An active deployment is standing execution: the agent runs on its cron
    expression with the credentials of its vaults and the egress of its environment,
    with nobody watching.
    """

    label: str = "AnthropicDeployment"
    properties: AnthropicDeploymentNodeProperties = AnthropicDeploymentNodeProperties()
    sub_resource_relationship: AnthropicDeploymentToWorkspaceRel = (
        AnthropicDeploymentToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AnthropicDeploymentToAgentRel(),
            AnthropicDeploymentToEnvironmentRel(),
            AnthropicDeploymentToVaultRel(),
        ],
    )
