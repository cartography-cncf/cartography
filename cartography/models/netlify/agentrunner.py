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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    site_id: PropertyRef = PropertyRef("site_id")
    title: PropertyRef = PropertyRef("title")
    state: PropertyRef = PropertyRef("state")
    current_task: PropertyRef = PropertyRef("current_task")
    # Where the agent's code came from and which deploy it started from.
    code_origin: PropertyRef = PropertyRef("code_origin")
    base_deploy_id: PropertyRef = PropertyRef("base_deploy_id")
    branch: PropertyRef = PropertyRef("branch")
    result_branch: PropertyRef = PropertyRef("result_branch")
    # What the agent did to the repository. These are the fields that make an agent runner a
    # non-human principal with write access: it pushes branches, opens pull requests and can
    # create merge commits.
    pr_url: PropertyRef = PropertyRef("pr_url")
    pr_branch: PropertyRef = PropertyRef("pr_branch")
    pr_state: PropertyRef = PropertyRef("pr_state")
    pr_number: PropertyRef = PropertyRef("pr_number")
    pr_error: PropertyRef = PropertyRef("pr_error")
    sha: PropertyRef = PropertyRef("sha")
    merge_commit_sha: PropertyRef = PropertyRef("merge_commit_sha")
    merge_commit_error: PropertyRef = PropertyRef("merge_commit_error")
    merge_target_available: PropertyRef = PropertyRef("merge_target_available")
    needs_git_sync: PropertyRef = PropertyRef("needs_git_sync")
    # Set when this runner was forked from another one.
    parent_agent_runner_id: PropertyRef = PropertyRef("parent_agent_runner_id")
    latest_session_state: PropertyRef = PropertyRef("latest_session_state")
    latest_session_mode: PropertyRef = PropertyRef("latest_session_mode")
    latest_session_is_published: PropertyRef = PropertyRef(
        "latest_session_is_published",
    )
    has_result_diff: PropertyRef = PropertyRef("has_result_diff")
    # Flattened from the nested `user` object by transform().
    user_id: PropertyRef = PropertyRef("user_id")
    active_session_created_at: PropertyRef = PropertyRef("active_session_created_at")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    done_at: PropertyRef = PropertyRef("done_at")


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
