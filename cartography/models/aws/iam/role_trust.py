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
class AWSRoleTrustsPrincipalRelProperties(CartographyRelProperties):
    """
    Properties for the TRUSTS_AWS_PRINCIPAL relationship, which represents what a role's
    assume role policy document declares: the principals permitted to assume it.

    The condition fields mirror the ones set on permission relationships by
    cartography.intel.aws.permission_relationships, so the two kinds of edge can be
    filtered the same way. AWS evaluates conditions at request time against a token that
    does not exist at sync time, so a conditional trust is annotated, never dropped.
    """

    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Condition metadata, aggregated across every statement that trusts this principal.
    has_condition: PropertyRef = PropertyRef("has_condition")
    condition_keys: PropertyRef = PropertyRef("condition_keys")
    conditions: PropertyRef = PropertyRef("conditions")


@dataclass(frozen=True)
class AWSRoleTrustsPrincipalMatchLink(CartographyRelSchema):
    """
    MatchLink schema for (:AWSRole)-[:TRUSTS_AWS_PRINCIPAL]->(:AWSPrincipal).

    This is a MatchLink rather than a relationship on AWSRoleSchema because a single role
    can trust several principals under different conditions, and only a per-(role,
    principal) row can carry per-edge properties. A node-schema relationship using a
    one_to_many target matcher compiles to a single `principal.arn IN $list` clause, so
    every edge from a given role would share one set of property values.
    """

    # Source node (the role whose trust policy declares the trust)
    source_node_label: str = "AWSRole"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"arn": PropertyRef("source_role_arn")},
    )

    # Target node (the principal permitted to assume the role)
    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("target_principal_arn")},
    )

    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TRUSTS_AWS_PRINCIPAL"
    properties: AWSRoleTrustsPrincipalRelProperties = (
        AWSRoleTrustsPrincipalRelProperties()
    )
