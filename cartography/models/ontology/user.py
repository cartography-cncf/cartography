from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class UserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("email")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    fullname: PropertyRef = PropertyRef("fullname")
    firstname: PropertyRef = PropertyRef("firstname")
    lastname: PropertyRef = PropertyRef("lastname")
    active: PropertyRef = PropertyRef("active")


@dataclass(frozen=True)
class UserToUserAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:User)-[:HAS_ACCOUNT]->(:UserAccount)
# This is a relationship to a sementic label used by modules' users nodes
class UserToUserAccountRel(CartographyRelSchema):
    target_node_label: str = "UserAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCOUNT"
    properties: UserToUserAccountRelProperties = UserToUserAccountRelProperties()


@dataclass(frozen=True)
class UserToOntologyNodeRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# Cleanup-only relationship definitions for custom ontology links.
# These relations are created by ontology analysis jobs, not by load(UserSchema()).
# The PropertyRef values intentionally reference fields absent from user load payloads so
# standard ingestion never creates them, while schema-driven cleanup still knows about them.


@dataclass(frozen=True)
class UserToAWSSSOUserHasAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSSSOUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_cleanup_awssso_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCOUNT"
    properties: UserToOntologyNodeRelProperties = UserToOntologyNodeRelProperties()


@dataclass(frozen=True)
class UserToGitHubUserHasAccountRel(CartographyRelSchema):
    target_node_label: str = "GitHubUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_cleanup_github_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCOUNT"
    properties: UserToOntologyNodeRelProperties = UserToOntologyNodeRelProperties()


@dataclass(frozen=True)
class UserToAPIKeyOwnsRel(CartographyRelSchema):
    target_node_label: str = "APIKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_cleanup_apikey_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "OWNS"
    properties: UserToOntologyNodeRelProperties = UserToOntologyNodeRelProperties()


@dataclass(frozen=True)
class UserToThirdPartyAppAuthorizedRel(CartographyRelSchema):
    target_node_label: str = "ThirdPartyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_cleanup_thirdpartyapp_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "AUTHORIZED"
    properties: UserToOntologyNodeRelProperties = UserToOntologyNodeRelProperties()


@dataclass(frozen=True)
class UserSchema(CartographyNodeSchema):
    label: str = "User"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: UserNodeProperties = UserNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            UserToUserAccountRel(),
            UserToAWSSSOUserHasAccountRel(),
            UserToGitHubUserHasAccountRel(),
            UserToAPIKeyOwnsRel(),
            UserToThirdPartyAppAuthorizedRel(),
        ],
    )
