"""
Azure permission relationship MatchLink schemas.
"""

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
class AzurePermissionRelProperties(CartographyRelProperties):
    """
    Properties for Azure permission relationships.
    """

    # Required fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class AzurePermissionMatchLink(CartographyRelSchema):
    """
    MatchLink schema for Azure permission relationships.
    Creates relationships like: (EntraUser|EntraGroup|EntraServicePrincipal)-[:CAN_READ]->(AzureResource)

    This MatchLink handles permission relationships between Azure principals and resources
    based on RBAC assignments and permission evaluations.
    """

    # MatchLink-specific fields
    source_node_label: str = (
        "EntraPrincipal"  # Covers EntraUser, EntraGroup, EntraServicePrincipal
    )
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )

    # Standard CartographyRelSchema fields
    target_node_label: str = (
        "AzureResource"  # Will be dynamically set based on target_label
    )
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = (
        "HAS_PERMISSION"  # Will be dynamically set based on relationship_name
    )
    properties: AzurePermissionRelProperties = AzurePermissionRelProperties()
