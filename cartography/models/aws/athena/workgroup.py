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
class AWSAthenaWorkGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "Name"
    )  # WorkGroup Name is unique per region-account? Yes. ARN is better?
    # Athena WorkGroups don't seem to return an ARN in 'list_work_groups', but usually available.
    # We will construct ARN or use Name. Let's start with Name as ID for now if ARN unavailable in simple list.
    name: PropertyRef = PropertyRef("Name")
    description: PropertyRef = PropertyRef("Description")
    state: PropertyRef = PropertyRef("State")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSAthenaWorkGroupToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSAthenaWorkGroupToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSAthenaWorkGroupToAWSAccountRelProperties = (
        AWSAthenaWorkGroupToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSAthenaWorkGroupSchema(CartographyNodeSchema):
    label: str = "AWSAthenaWorkGroup"
    properties: AWSAthenaWorkGroupNodeProperties = AWSAthenaWorkGroupNodeProperties()
    sub_resource_relationship: AWSAthenaWorkGroupToAWSAccountRel = (
        AWSAthenaWorkGroupToAWSAccountRel()
    )
