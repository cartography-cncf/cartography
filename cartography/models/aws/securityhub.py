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
class SecurityHubNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("HubArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    subscribed_at: PropertyRef = PropertyRef("SubscribedAt")
    auto_enable_controls: PropertyRef = PropertyRef("AutoEnableControls")


@dataclass(frozen=True)
class SecurityHubToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:SecurityHub)
class SecurityHubToAWSAccountRel(CartographyRelSchema):
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
    label: str = "SecurityHub"
    properties: SecurityHubNodeProperties = SecurityHubNodeProperties()
    sub_resource_relationship: SecurityHubToAWSAccountRel = SecurityHubToAWSAccountRel()
