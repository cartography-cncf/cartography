from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class PermissionRelationshipRelProperties(CartographyRelProperties):
    """
    Properties for permission relationships between principals and resources.
    """

    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class DynamicPermissionMatchLink(CartographyRelSchema):
    """
    MatchLink schema for permission relationships between principals and resources.
    Creates relationships like: (AWSPrincipal)-[:HAS_PERMISSION]->(Resource)
    """

    source_node_label: str = "AWSPrincipal"
    target_node_label: str = "Resource"
    rel_label: str = "HAS_PERMISSION"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {
            "arn": PropertyRef("principal_arn"),
        }
    )
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("resource_arn"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    properties: PermissionRelationshipRelProperties = (
        PermissionRelationshipRelProperties()
    )

    def __init__(self, target_node_label: str, relationship_name: str):
        object.__setattr__(self, "target_node_label", target_node_label)
        object.__setattr__(self, "rel_label", relationship_name)
