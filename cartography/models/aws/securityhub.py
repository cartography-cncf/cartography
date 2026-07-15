from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class SecurityHubNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("HubArn", description="The arn of the hub resource.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    subscribed_at: PropertyRef = PropertyRef(
        "SubscribedAt",
        description="The date and time when Security Hub was enabled in the account.",
    )
    auto_enable_controls: PropertyRef = PropertyRef(
        "AutoEnableControls",
        description="Whether to automatically enable new controls when they are added to standards that are enabled.",
    )


@dataclass(frozen=True)
class SecurityHubToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSSecurityHub)
class SecurityHubToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSecurityHub`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SecurityHubToAWSAccountRelProperties = (
        SecurityHubToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class SecurityHubSchema(CartographyNodeSchema):
    "Represents an `AWSSecurityHub` node in the AWS graph."

    label: str = "AWSSecurityHub"
    # DEPRECATED: legacy SecurityHub node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SecurityHub"])
    properties: SecurityHubNodeProperties = SecurityHubNodeProperties()
    sub_resource_relationship: SecurityHubToAWSAccountRel = SecurityHubToAWSAccountRel()
