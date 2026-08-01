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


# --- Node Definitions ---
@dataclass(frozen=True)
class NetlifyAgentRunnerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="The Netlify agent runner id.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef(
        "site_id", description="Id of the site the runner works on."
    )
    title: PropertyRef = PropertyRef(
        "title", description="Title Netlify derived from the prompt."
    )
    state: PropertyRef = PropertyRef(
        "state", description="Runner state, e.g. `new`, `running`, `done`."
    )
    current_task: PropertyRef = PropertyRef(
        "current_task", description="What the runner is doing right now."
    )
    # Where the agent's code came from and which deploy it started from.
    code_origin: PropertyRef = PropertyRef(
        "code_origin",
        description="Where the runner's starting code came from, e.g. `zip`, `git`.",
    )
    base_deploy_id: PropertyRef = PropertyRef(
        "base_deploy_id", description="Deploy the runner started from."
    )
    branch: PropertyRef = PropertyRef(
        "branch", description="Branch the runner started from."
    )
    result_branch: PropertyRef = PropertyRef(
        "result_branch", description="Branch the runner pushed its result to."
    )
    # What the agent did to the repository. These are the fields that make an agent runner a
    # non-human principal with write access: it pushes branches, opens pull requests and can
    # create merge commits.
    pr_url: PropertyRef = PropertyRef(
        "pr_url", description="Pull request the runner opened."
    )
    pr_branch: PropertyRef = PropertyRef(
        "pr_branch", description="Branch the pull request is based on."
    )
    pr_state: PropertyRef = PropertyRef("pr_state", description="Pull request state.")
    pr_number: PropertyRef = PropertyRef(
        "pr_number", description="Pull request number."
    )
    pr_error: PropertyRef = PropertyRef(
        "pr_error", description="Why opening the pull request failed."
    )
    sha: PropertyRef = PropertyRef("sha", description="Commit the runner produced.")
    merge_commit_sha: PropertyRef = PropertyRef(
        "merge_commit_sha", description="Merge commit the runner created."
    )
    merge_commit_error: PropertyRef = PropertyRef(
        "merge_commit_error", description="Why creating the merge commit failed."
    )
    merge_target_available: PropertyRef = PropertyRef(
        "merge_target_available", description="Whether the runner can merge its result."
    )
    needs_git_sync: PropertyRef = PropertyRef(
        "needs_git_sync", description="Whether the runner's branch is behind its base."
    )
    # Set when this runner was forked from another one.
    parent_agent_runner_id: PropertyRef = PropertyRef(
        "parent_agent_runner_id", description="Runner this one was forked from."
    )
    latest_session_state: PropertyRef = PropertyRef(
        "latest_session_state", description="State of the runner's most recent session."
    )
    latest_session_mode: PropertyRef = PropertyRef(
        "latest_session_mode", description="Mode of the most recent session."
    )
    latest_session_is_published: PropertyRef = PropertyRef(
        "latest_session_is_published",
        description="Whether the most recent session's result was published.",
    )
    has_result_diff: PropertyRef = PropertyRef(
        "has_result_diff", description="Whether the runner produced a diff."
    )
    # Flattened from the nested `user` object by transform().
    user_id: PropertyRef = PropertyRef(
        "user_id", description="User who started the runner."
    )
    active_session_created_at: PropertyRef = PropertyRef(
        "active_session_created_at",
        description="When the currently active session started.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the runner was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="When the runner was last modified."
    )
    done_at: PropertyRef = PropertyRef(
        "done_at", description="When the runner finished."
    )


# --- Relationship Definitions ---
@dataclass(frozen=True)
class NetlifyAgentRunnerToNetlifyAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAccount)-[:RESOURCE]->(:NetlifyAgentRunner)
class NetlifyAgentRunnerToNetlifyAccountRel(CartographyRelSchema):
    target_node_label: str = "NetlifyAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("NETLIFY_ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: NetlifyAgentRunnerToNetlifyAccountRelProperties = (
        NetlifyAgentRunnerToNetlifyAccountRelProperties()
    )


@dataclass(frozen=True)
class NetlifyAgentRunnerToSiteRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifySite)-[:HAS_AGENT_RUNNER]->(:NetlifyAgentRunner)
class NetlifyAgentRunnerToSiteRel(CartographyRelSchema):
    target_node_label: str = "NetlifySite"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("site_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_AGENT_RUNNER"
    properties: NetlifyAgentRunnerToSiteRelProperties = (
        NetlifyAgentRunnerToSiteRelProperties()
    )


@dataclass(frozen=True)
class NetlifyAgentRunnerToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAgentRunner)-[:CREATED_BY]->(:NetlifyUser)
class NetlifyAgentRunnerToUserRel(CartographyRelSchema):
    """The team member who started this agent runner."""

    target_node_label: str = "NetlifyUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CREATED_BY"
    properties: NetlifyAgentRunnerToUserRelProperties = (
        NetlifyAgentRunnerToUserRelProperties()
    )


@dataclass(frozen=True)
class NetlifyAgentRunnerToParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:NetlifyAgentRunner)-[:FORKED_FROM]->(:NetlifyAgentRunner)
class NetlifyAgentRunnerToParentRel(CartographyRelSchema):
    """The runner this one was forked from, when it started as a fork of another."""

    target_node_label: str = "NetlifyAgentRunner"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_agent_runner_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FORKED_FROM"
    properties: NetlifyAgentRunnerToParentRelProperties = (
        NetlifyAgentRunnerToParentRelProperties()
    )


# --- Main Schema ---
@dataclass(frozen=True)
class NetlifyAgentRunnerSchema(CartographyNodeSchema):
    """
    A Netlify AI agent runner: a non-human principal that edits a site's code and can push
    branches and open pull requests on its behalf.

    Only the runner is ingested, not its sessions: a session is a live execution record
    (prompt, step list, result diff) rather than inventory.
    """

    label: str = "NetlifyAgentRunner"
    properties: NetlifyAgentRunnerNodeProperties = NetlifyAgentRunnerNodeProperties()
    sub_resource_relationship: NetlifyAgentRunnerToNetlifyAccountRel = (
        NetlifyAgentRunnerToNetlifyAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            NetlifyAgentRunnerToSiteRel(),
            NetlifyAgentRunnerToUserRel(),
            NetlifyAgentRunnerToParentRel(),
        ],
    )
