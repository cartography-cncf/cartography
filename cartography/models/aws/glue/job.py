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
class GlueJobNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Name")
    arn: PropertyRef = PropertyRef("Name", extra_index=True)
    profile_name: PropertyRef = PropertyRef("ProfileName")
    job_mode: PropertyRef = PropertyRef("JobMode")
    connections: PropertyRef = PropertyRef("Connections")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    description: PropertyRef = PropertyRef("Description")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueJobToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueJobToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GlueJobToAwsAccountRelProperties = GlueJobToAwsAccountRelProperties()


@dataclass(frozen=True)
class GlueJobToGlueConnectionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GlueJobToGlueConnectionRel(CartographyRelSchema):
    target_node_label: str = "GlueConnection"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("Connections", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES"
    properties: GlueJobToGlueConnectionRelProperties = (
        GlueJobToGlueConnectionRelProperties()
    )


@dataclass(frozen=True)
class GlueJobSchema(CartographyNodeSchema):
    label: str = "GlueJob"
    properties: GlueJobNodeProperties = GlueJobNodeProperties()
    sub_resource_relationship: GlueJobToAWSAccountRel = GlueJobToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GlueJobToGlueConnectionRel(),
        ]
    )
