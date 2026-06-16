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
    # Constant condition fields (always unconditional on the bulk path). Set so a
    # conditional -> unconditional transition clears stale metadata left by a prior
    # sync that wrote the same edge via the row-by-row conditional schema.
    has_condition: PropertyRef = PropertyRef("has_condition", set_in_kwargs=True)
    condition_title: PropertyRef = PropertyRef("condition_title", set_in_kwargs=True)
    condition_expression: PropertyRef = PropertyRef(
        "condition_expression", set_in_kwargs=True
    )
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


@dataclass(frozen=True)
class GCPConditionalPermissionRelProperties(CartographyRelProperties):
    """
    Properties for GCP permission relationships that carry IAM condition metadata.

    GCP evaluates IAM conditions (CEL expressions) at request time, so cartography
    cannot statically decide whether a conditional binding resolves to allow. These
    per-edge properties annotate the relationship so consumers can filter conditional
    access. See issue #2312.

    Used only on the row-by-row load path; the bulk Cartesian helper requires all
    relationship properties to be kwargs-bound (see build_matchlink_cartesian_product_query),
    so broad unconditional grants keep using GCPPermissionMatchLink.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    has_condition: PropertyRef = PropertyRef("has_condition")
    condition_title: PropertyRef = PropertyRef("condition_title")
    condition_expression: PropertyRef = PropertyRef("condition_expression")
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPConditionalPermissionMatchLink(CartographyRelSchema):
    """
    MatchLink schema for GCP permission relationships that may carry IAM conditions.

    Same edge shape as GCPPermissionMatchLink (same rel_label, source/target matchers),
    but with per-edge condition metadata. Loaded via load_matchlinks() (row-by-row), so
    cleanup by rel_label + sub-resource covers edges written by either schema.
    """

    source_node_label: str = "GCPPrincipal"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"email": PropertyRef("principal_email")},
    )

    target_node_label: str = "GCPResource"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("resource_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_PERMISSION"
    properties: GCPConditionalPermissionRelProperties = (
        GCPConditionalPermissionRelProperties()
    )
