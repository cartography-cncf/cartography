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
class CloudflareRulesetRuleNodeProperties(CartographyNodeProperties):
    # A rule only exists as part of a ruleset deployment, and its API ID is only
    # unique within one, so the node is qualified with its deployment the same
    # way CloudflareRuleset is qualified with its scope.
    id: PropertyRef = PropertyRef(
        "id",
        description="Rule ID, built as `<ruleset deployment id>/<rule_id>`.",
    )
    rule_id: PropertyRef = PropertyRef(
        "rule_id",
        extra_index=True,
        description="Rule ID as returned by the Cloudflare API.",
    )
    action: PropertyRef = PropertyRef(
        "action",
        description=(
            "Action performed when the rule matches, such as `block`, "
            "`managed_challenge` or `execute`."
        ),
    )
    expression: PropertyRef = PropertyRef(
        "expression",
        description="Expression defining which traffic matches the rule.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Informative description of the rule.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the rule is executed.",
    )
    ref: PropertyRef = PropertyRef(
        "ref",
        description="Reference of the rule, defaulting to the rule ID.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Version of the rule.",
    )
    last_updated: PropertyRef = PropertyRef(
        "last_updated",
        description="Timestamp when the rule was last modified.",
    )
    categories: PropertyRef = PropertyRef(
        "categories",
        description="Categories of the rule.",
    )
    logging_enabled: PropertyRef = PropertyRef(
        "logging.enabled",
        description="Whether the rule logs its matches.",
    )
    ratelimit_period: PropertyRef = PropertyRef(
        "ratelimit.period",
        description="Period in seconds over which the rate limit counter increments.",
    )
    ratelimit_requests_per_period: PropertyRef = PropertyRef(
        "ratelimit.requests_per_period",
        description="Request threshold per period before the action is executed.",
    )
    executed_ruleset_id: PropertyRef = PropertyRef(
        "action_parameters.id",
        description=(
            "Cloudflare API ID of the ruleset this rule executes, shared by every "
            "deployment of that ruleset. Set only on `execute` rules, which is how "
            "a zone or an account turns on a Cloudflare managed ruleset. Follow "
            "the EXECUTES relationship to reach the single deployment this rule "
            "actually turns on."
        ),
    )
    executed_deployment_id: PropertyRef = PropertyRef(
        "executed_deployment_id",
        description=(
            "Deployment ID of the ruleset this rule executes, resolved in the "
            "scope the rule itself was read from."
        ),
    )
    ruleset_id: PropertyRef = PropertyRef(
        "ruleset_id",
        set_in_kwargs=True,
        description=(
            "Deployment ID of the ruleset the rule belongs to, matching "
            "`CloudflareRuleset.id`."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareRulesetRuleToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareRulesetRule)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareRulesetRuleToAccountRel(CartographyRelSchema):
    """The account contains the ruleset rule."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareRulesetRuleToAccountRelProperties = (
        CloudflareRulesetRuleToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareRulesetRuleToRulesetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareRuleset)-[:HAS_RULE]->(:CloudflareRulesetRule)
class CloudflareRulesetRuleToRulesetRel(CartographyRelSchema):
    """The ruleset contains the rule."""

    target_node_label: str = "CloudflareRuleset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ruleset_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULE"
    properties: CloudflareRulesetRuleToRulesetRelProperties = (
        CloudflareRulesetRuleToRulesetRelProperties()
    )


@dataclass(frozen=True)
class CloudflareRulesetRuleToExecutedRulesetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareRulesetRule)-[:EXECUTES]->(:CloudflareRuleset)
class CloudflareRulesetRuleToExecutedRulesetRel(CartographyRelSchema):
    """
    The rule turns on another ruleset, typically a Cloudflare managed one. The
    target is the deployment in the scope the rule was read from, not every
    deployment sharing the executed ruleset's API ID.
    """

    target_node_label: str = "CloudflareRuleset"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("executed_deployment_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "EXECUTES"
    properties: CloudflareRulesetRuleToExecutedRulesetRelProperties = (
        CloudflareRulesetRuleToExecutedRulesetRelProperties()
    )


@dataclass(frozen=True)
class CloudflareRulesetRuleSchema(CartographyNodeSchema):
    """A rule inside a Cloudflare ruleset."""

    label: str = "CloudflareRulesetRule"
    properties: CloudflareRulesetRuleNodeProperties = (
        CloudflareRulesetRuleNodeProperties()
    )
    sub_resource_relationship: CloudflareRulesetRuleToAccountRel = (
        CloudflareRulesetRuleToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudflareRulesetRuleToRulesetRel(),
            CloudflareRulesetRuleToExecutedRulesetRel(),
        ],
    )
