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
class GlueConnectionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Name")
    arn: PropertyRef = PropertyRef("Name", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    description: PropertyRef = PropertyRef("Description")
    connection_type: PropertyRef = PropertyRef("ConnectionType")
    status: PropertyRef = PropertyRef("Status")
    status_reason: PropertyRef = PropertyRef("StatusReason")
    authentication_type: PropertyRef = PropertyRef("AuthenticationType")
    secret_arn: PropertyRef = PropertyRef("SecretArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueConnectionToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueConnectionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GlueConnectionToAwsAccountRelProperties = (
        GlueConnectionToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class GlueConnectionSchema(CartographyNodeSchema):
    label: str = "GlueConnection"
    properties: GlueConnectionNodeProperties = GlueConnectionNodeProperties()
    sub_resource_relationship: GlueConnectionToAWSAccountRel = (
        GlueConnectionToAWSAccountRel()
    )
