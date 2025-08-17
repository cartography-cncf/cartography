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
class SESConfigurationSetNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ConfigurationSetArn")
    arn: PropertyRef = PropertyRef("ConfigurationSetArn", extra_index=True)
    name: PropertyRef = PropertyRef("Name", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SESConfigurationSetToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SESConfigurationSetToAWSAccount(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SESConfigurationSetToAwsAccountRelProperties = SESConfigurationSetToAwsAccountRelProperties()


@dataclass(frozen=True)
class SESConfigurationSetSchema(CartographyNodeSchema):
    label: str = "SESConfigurationSet"
    properties: SESConfigurationSetNodeProperties = SESConfigurationSetNodeProperties()
    sub_resource_relationship: SESConfigurationSetToAWSAccount = SESConfigurationSetToAWSAccount()
