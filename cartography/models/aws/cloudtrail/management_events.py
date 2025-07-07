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
class AssumedRoleRelProperties(CartographyRelProperties):
    """
    Properties for the ASSUMED_ROLE relationship representing role assumption events.
    Matches the cloudtrail_management_events spec and adds enhanced temporal precision.
    """

    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # CloudTrail-specific relationship properties
    lastused: PropertyRef = PropertyRef("lastused")
    times_used: PropertyRef = PropertyRef("times_used")
    first_seen: PropertyRef = PropertyRef("first_seen")
    last_seen: PropertyRef = PropertyRef("last_seen")


@dataclass(frozen=True)
class AssumedRoleMatchLink(CartographyRelSchema):
    """
    MatchLink schema for ASSUMED_ROLE relationships from CloudTrail events.
    Creates relationships like: (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE]->(AWSRole)

    This MatchLink handles role assumption relationships discovered via CloudTrail management events.
    It supports multiple source node types and aggregated relationship properties.
    """

    # MatchLink-specific fields
    source_node_label: str = (
        "AWSPrincipal"  # Base type that covers AWSUser, AWSRole, AWSPrincipal
    )
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"arn": PropertyRef("source_principal_arn")},
    )

    # Standard CartographyRelSchema fields
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("destination_principal_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMED_ROLE"
    properties: AssumedRoleRelProperties = AssumedRoleRelProperties()


# Legacy schema for backward compatibility and index creation (Potential for removal if MatchLink is working)
@dataclass(frozen=True)
class AssumedRoleRel(CartographyRelSchema):
    """
    Legacy relationship schema for role assumptions from any AWS Principal to AWSRole.

    This schema is maintained for backward compatibility and index creation.
    The actual loading now uses AssumedRoleMatchLink with load_matchlinks().
    """

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("destination_principal_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMED_ROLE"
    properties: AssumedRoleRelProperties = AssumedRoleRelProperties()
