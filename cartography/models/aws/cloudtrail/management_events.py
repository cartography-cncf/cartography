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
    last_used: PropertyRef = PropertyRef("last_used")
    times_used: PropertyRef = PropertyRef("times_used")
    first_seen_in_time_window: PropertyRef = PropertyRef("first_seen_in_time_window")


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


@dataclass(frozen=True)
class AssumedRoleWithSAMLRelProperties(CartographyRelProperties):
    """
    Properties for the ASSUMED_ROLE_WITH_SAML relationship representing SAML-based role assumption events.
    Focuses specifically on SAML federated identity role assumptions.
    """

    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # CloudTrail-specific relationship properties
    last_used: PropertyRef = PropertyRef("last_used")
    times_used: PropertyRef = PropertyRef("times_used")
    first_seen_in_time_window: PropertyRef = PropertyRef("first_seen_in_time_window")


@dataclass(frozen=True)
class AssumedRoleWithSAMLMatchLink(CartographyRelSchema):
    """
    MatchLink schema for ASSUMED_ROLE_WITH_SAML relationships from CloudTrail SAML events.
    Creates relationships like: (AWSRole)-[:ASSUMED_ROLE_WITH_SAML]->(AWSRole)

    This MatchLink handles SAML-based role assumption relationships discovered via CloudTrail
    AssumeRoleWithSAML events. It creates separate relationships from regular AssumeRole events
    to preserve visibility into authentication methods used.
    """

    # MatchLink-specific fields
    source_node_label: str = "AWSSSOUser"  # Match against AWS SSO User nodes
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"user_name": PropertyRef("source_principal_arn")},
    )

    # Standard CartographyRelSchema fields
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("destination_principal_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMED_ROLE_WITH_SAML"
    properties: AssumedRoleWithSAMLRelProperties = AssumedRoleWithSAMLRelProperties()


@dataclass(frozen=True)
class AssumeRoleWithWebIdentityRelProperties(CartographyRelProperties):
    """
    Properties for the ASSUMED_ROLE_WITH_WEB_IDENTITY relationship representing web identity-based role assumption events.
    Focuses specifically on web identity federation role assumptions (Google, Amazon, Facebook, etc.).
    """

    # Mandatory fields for MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # CloudTrail-specific relationship properties
    last_used: PropertyRef = PropertyRef("last_used")
    times_used: PropertyRef = PropertyRef("times_used")
    first_seen_in_time_window: PropertyRef = PropertyRef("first_seen_in_time_window")


@dataclass(frozen=True)
class GitHubRepoAssumeRoleWithWebIdentityMatchLink(CartographyRelSchema):
    """
    MatchLink schema for ASSUMED_ROLE_WITH_WEB_IDENTITY relationships from GitHub Actions to AWS roles.
    Creates relationships like: (GitHubRepository)-[:ASSUMED_ROLE_WITH_WEB_IDENTITY]->(AWSRole)

    This MatchLink provides granular visibility into which specific GitHub repositories are assuming
    AWS roles via GitHub Actions OIDC, rather than just showing provider-level relationships.
    """

    # MatchLink-specific fields for GitHub repositories
    source_node_label: str = "GitHubRepository"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"fullname": PropertyRef("source_repo_fullname")},
    )

    # Standard CartographyRelSchema fields
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("destination_principal_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMED_ROLE_WITH_WEB_IDENTITY"
    properties: AssumeRoleWithWebIdentityRelProperties = (
        AssumeRoleWithWebIdentityRelProperties()
    )
