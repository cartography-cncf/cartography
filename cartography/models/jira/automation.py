from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.jira.access import JiraRelProperties
from cartography.models.jira.access import JiraResourceRel


@dataclass(frozen=True)
class JiraAutomationRuleRunsAsRel(CartographyRelSchema):
    """The Jira user account that the automation rule executes as."""

    target_node_label: str = "JiraUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("actor_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RUNS_AS"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraAutomationRuleProjectRel(CartographyRelSchema):
    """A Jira project in the automation rule's configured scope."""

    target_node_label: str = "JiraProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "APPLIES_TO"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraAutomationRuleGitHubRepoRel(CartographyRelSchema):
    """A GitHub repository targeted by an outgoing web request in the automation rule."""

    target_node_label: str = "GitHubRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("github_repository_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SENDS_REQUESTS_TO"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraAutomationRuleSlackTeamRel(CartographyRelSchema):
    """A Slack workspace targeted by an incoming webhook in the automation rule."""

    target_node_label: str = "SlackTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("slack_team_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SENDS_REQUESTS_TO"
    properties: JiraRelProperties = JiraRelProperties()


@dataclass(frozen=True)
class JiraAutomationRuleProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Cloud ID, automation_rule kind, and URL-escaped rule UUID.",
    )
    uuid: PropertyRef = PropertyRef(
        "uuid",
        description="Atlassian Automation rule UUID.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Automation rule name.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="Automation rule state, such as ENABLED or DISABLED.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Automation rule description.",
    )
    write_access_type: PropertyRef = PropertyRef(
        "write_access_type",
        description="Rule writeAccessType setting, such as OWNER_ONLY.",
    )
    created: PropertyRef = PropertyRef(
        "created",
        description="When the rule was created.",
    )
    updated: PropertyRef = PropertyRef(
        "updated",
        description="When the rule was last updated.",
    )
    trigger_type: PropertyRef = PropertyRef(
        "trigger_type",
        description="Type identifier of the rule's trigger component.",
    )
    has_incoming_webhook_trigger: PropertyRef = PropertyRef(
        "has_incoming_webhook_trigger",
        description="True when trigger_type is jira.incoming.webhook.",
    )
    is_global: PropertyRef = PropertyRef(
        "is_global",
        description="True when ruleScopeARIs contains the Jira site ARI (a global rule). Project-type rules are not global.",
    )
    outgoing_request_hosts: PropertyRef = PropertyRef(
        "outgoing_request_hosts",
        description="Sorted unique lowercase hostnames from outgoing web request and Slack webhook components.",
    )
    outgoing_request_count: PropertyRef = PropertyRef(
        "outgoing_request_count",
        description="Total count of outgoing web request and Slack webhook components in the rule.",
    )
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID",
        set_in_kwargs=True,
        description="Jira Cloud ID.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last Cartography sync.",
    )


@dataclass(frozen=True)
class JiraAutomationRuleSchema(CartographyNodeSchema):
    """
    A Jira Cloud Automation rule and its non-secret outgoing request targets.

    Cartography stores rule metadata, the trigger type, scope flags, outgoing
    request hosts and counts, and the GitHub `owner/repo` or Slack team ID that
    an outgoing request targets. Full URLs, other path segments, query strings,
    headers, bodies, Slack channel names, and webhook tokens are never stored or
    logged, because the Automation API returns webhook tokens even when it
    redacts sensitive fields. Confluence Automation rules are out of scope.
    """

    label: str = "JiraAutomationRule"
    properties: JiraAutomationRuleProperties = JiraAutomationRuleProperties()
    sub_resource_relationship: JiraResourceRel = JiraResourceRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            JiraAutomationRuleRunsAsRel(),
            JiraAutomationRuleProjectRel(),
            JiraAutomationRuleGitHubRepoRel(),
            JiraAutomationRuleSlackTeamRel(),
        ]
    )
