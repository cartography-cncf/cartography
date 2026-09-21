from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import MatchLinkSubResource
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class OktaGroupToAWSRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this relationship.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
        description="Label of the Okta organization that owns this relationship.",
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
        description="Identifier of the Okta organization that owns this relationship.",
    )


@dataclass(frozen=True)
class OktaGroupToAWSRoleHasRoleMatchLink(CartographyRelSchema):
    """Links an Okta group to the AWS IAM role granted by its SAML mapping."""

    source_node_label: str = "OktaGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("okta_group_id")},
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="OktaOrganization",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: OktaGroupToAWSRoleRelProperties = OktaGroupToAWSRoleRelProperties()


@dataclass(frozen=True)
# DEPRECATED: replaced by the canonical (:UserGroup)-[:HAS_ROLE]->(:PermissionRole)
# edge (OktaGroupToAWSRoleHasRoleMatchLink). Kept for backward compatibility and
# will be removed in v1.0.0.
class OktaGroupToAWSRoleAllowedByMatchLink(CartographyRelSchema):
    """Compatibility edge for an AWS role granted to Okta group members."""

    source_node_label: str = "OktaGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("okta_group_id")},
    )
    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="OktaOrganization",
        target_node_matcher=make_target_node_matcher(
            {"id": PropertyRef("_sub_resource_id", set_in_kwargs=True)},
        ),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_BY"
    properties: OktaGroupToAWSRoleRelProperties = OktaGroupToAWSRoleRelProperties()
