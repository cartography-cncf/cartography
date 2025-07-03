from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AssumedRoleRelProperties(CartographyRelProperties):
    """
    Properties for the ASSUMED_ROLE relationship representing role assumption events.
    Matches the cloudtrail_management_events spec and adds enhanced temporal precision.
    """

    lastused: PropertyRef = PropertyRef("lastused")
    times_used: PropertyRef = PropertyRef("times_used")
    first_seen: PropertyRef = PropertyRef("first_seen")
    last_seen: PropertyRef = PropertyRef("last_seen")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AssumedRoleRel(CartographyRelSchema):
    """
    Unified relationship schema for role assumptions from any AWS Principal to AWSRole.
    Handles User->Role, Role->Role, and Principal->Role relationships in one class.
    Creates relationships like: (AWSUser|AWSRole|AWSPrincipal)-[:ASSUMED_ROLE]->(AWSRole)

    This schema is used for:
    1. Index creation (performance optimization)
    2. Documentation of the relationship structure
    3. Validation of target node matching

    Note: The actual loading uses custom Cypher queries due to complex aggregation requirements.
    """

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("destination_principal_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMED_ROLE"
    properties: AssumedRoleRelProperties = AssumedRoleRelProperties()
