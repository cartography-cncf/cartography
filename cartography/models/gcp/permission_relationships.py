"""
GCP permission relationship MatchLink schemas.
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
class GCPPermissionRelProperties(CartographyRelProperties):
    """
    Properties for GCP permission relationships.
    """

    # Required fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPPermissionMatchLink(CartographyRelSchema):
    """
    MatchLink schema for GCP permission relationships.
    Creates relationships like: (GCPPrincipal)-[:CAN_READ]->(GCPResource)

    This MatchLink handles permission relationships between GCP principals and resources
    based on IAM policy bindings and permission evaluations.

    GCPPrincipal can be:
    - GCPUser (from GSuite)
    - GCPServiceAccount
    - GCPGroup (from GSuite)
    """

    source_node_label: str = "GCPPrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"email": PropertyRef("principal_email")},
    )

    target_node_label: str = (
        "GCPResource"  # Will be dynamically set based on target_label
    )
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = (
        "HAS_PERMISSION"  # Will be dynamically set based on relationship_name
    )
    properties: GCPPermissionRelProperties = GCPPermissionRelProperties()
