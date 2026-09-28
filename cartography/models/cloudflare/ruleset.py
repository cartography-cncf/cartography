from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import NETWORK_ACCESS_CONTROL


@dataclass(frozen=True)
class CloudflareRulesetNodeProperties(CartographyNodeProperties):
    # A Cloudflare-provided ruleset keeps the same API ID everywhere it is
    # deployed, so the raw ID cannot identify the node: it would merge the
    # account-level and zone-level deployments of a managed ruleset, and merge
    # the deployments of separate accounts read with the same token. The node
    # therefore identifies a deployment, qualified by the scope it applies to.
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Ruleset deployment ID, built as `<zone_id>/<ruleset_id>` for a "
            "zone-level ruleset and `<account_id>/<ruleset_id>` for an "
            "account-level one."
        ),
    )
    ruleset_id: PropertyRef = PropertyRef(
        "ruleset_id",
        extra_index=True,
        description=(
            "Ruleset ID as returned by the Cloudflare API. Shared by every "
            "deployment of a Cloudflare-provided ruleset, and the value that "
            "`CloudflareRulesetRule.executed_ruleset_id` points at."
        ),
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Human-readable name of the ruleset.",
    )
    kind: PropertyRef = PropertyRef(
        "kind",
        description=(
            "Kind of the ruleset: `managed` for Cloudflare-provided rulesets, "
            "`custom`, `root` or `zone` for customer-authored ones."
        ),
    )
    phase: PropertyRef = PropertyRef(
        "phase",
        description=(
            "Request-processing phase the ruleset runs in, such as "
            "`http_request_firewall_custom`."
        ),
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Version of the ruleset.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Informative description of the ruleset.",
    )
    last_updated: PropertyRef = PropertyRef(
        "last_updated",
        description="Timestamp when the ruleset was last modified.",
    )
    scope: PropertyRef = PropertyRef(
        "scope",
        description=(
            "Level the ruleset is deployed at: `account` for a ruleset covering "
            "every zone in the account, `zone` for a single-zone ruleset."
        ),
    )
    security_ruleset: PropertyRef = PropertyRef(
        "security_ruleset",
        description=(
            "Whether the ruleset phase performs access control, as opposed to "
            "caching, transforming or redirecting requests. Drives the "
            "NetworkAccessControl ontology label."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudflareRulesetToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareRuleset)<-[:RESOURCE]-(:CloudflareAccount)
class CloudflareRulesetToAccountRel(CartographyRelSchema):
    """The account contains the ruleset."""

    target_node_label: str = "CloudflareAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("account_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudflareRulesetToAccountRelProperties = (
        CloudflareRulesetToAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudflareRulesetToZoneRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CloudflareZone)-[:HAS_RULESET]->(:CloudflareRuleset)
class CloudflareRulesetToZoneRel(CartographyRelSchema):
    """
    The DNS zone applies the ruleset to its incoming requests. Absent on
    account-level rulesets, which are not tied to a single zone.
    """

    target_node_label: str = "CloudflareZone"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("zone_id", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RULESET"
    properties: CloudflareRulesetToZoneRelProperties = (
        CloudflareRulesetToZoneRelProperties()
    )


@dataclass(frozen=True)
class CloudflareRulesetSchema(CartographyNodeSchema):
    """
    A Cloudflare ruleset, as deployed in one scope. Rulesets are the engine behind
    the Cloudflare WAF: the security phases carry the request filtering, rate
    limiting and bot mitigation configuration, while other phases handle caching,
    transforms and redirects.

    Only deployed rulesets are ingested, that is the phase entry point rulesets of
    a scope and whatever an enabled `execute` rule in them turns on. A ruleset that
    merely exists, such as a Cloudflare-provided one nothing executes, has no node.
    """

    label: str = "CloudflareRuleset"
    properties: CloudflareRulesetNodeProperties = CloudflareRulesetNodeProperties()
    # Only the access-control phases are NetworkAccessControl; labelling a cache
    # or transform ruleset as one would pollute cross-provider firewall queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [NETWORK_ACCESS_CONTROL.when(security_ruleset="true")]
    )
    sub_resource_relationship: CloudflareRulesetToAccountRel = (
        CloudflareRulesetToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudflareRulesetToZoneRel(),
        ],
    )
