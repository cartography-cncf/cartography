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
class AWSGlueDatabaseNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ARN")
    name: PropertyRef = PropertyRef("Name")
    description: PropertyRef = PropertyRef("Description")
    arn: PropertyRef = PropertyRef("ARN")
    catalog_id: PropertyRef = PropertyRef("CatalogId")
    create_time: PropertyRef = PropertyRef("CreateTime")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSGlueDatabaseToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSGlueDatabaseToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSGlueDatabaseToAWSAccountRelProperties = (
        AWSGlueDatabaseToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSGlueDatabaseSchema(CartographyNodeSchema):
    label: str = "AWSGlueDatabase"
    properties: AWSGlueDatabaseNodeProperties = AWSGlueDatabaseNodeProperties()
    sub_resource_relationship: AWSGlueDatabaseToAWSAccountRel = (
        AWSGlueDatabaseToAWSAccountRel()
    )
