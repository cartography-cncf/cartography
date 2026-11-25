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
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class PylonTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Pylon team ID.")
    name: PropertyRef = PropertyRef("name", description="Team name.")
    assignment_method: PropertyRef = PropertyRef(
        "assignment_method",
        description=(
            "How the team routes issues to its members: `routing`, "
            "`schedule`, `manual`, or `pull_queue`."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class PylonTeamToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PylonOrganization)-[:RESOURCE]->(:PylonTeam)
class PylonTeamToOrganizationRel(CartographyRelSchema):
    """The organization contains the team."""

    target_node_label: str = "PylonOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: PylonTeamToOrganizationRelProperties = (
        PylonTeamToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class PylonUserToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PylonUser)-[:MEMBER_OF]->(:PylonTeam)
class PylonUserToTeamRel(CartographyRelSchema):
    """The user is a member of the team."""

    target_node_label: str = "PylonUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: PylonUserToTeamRelProperties = PylonUserToTeamRelProperties()


@dataclass(frozen=True)
class PylonServiceAccountToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:PylonServiceAccount)-[:MEMBER_OF]->(:PylonTeam)
class PylonServiceAccountToTeamRel(CartographyRelSchema):
    """The service account is a member of the team."""

    target_node_label: str = "PylonServiceAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("member_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: PylonServiceAccountToTeamRelProperties = (
        PylonServiceAccountToTeamRelProperties()
    )


@dataclass(frozen=True)
class PylonTeamSchema(CartographyNodeSchema):
    """A team in a Pylon organization, read from `GET /teams`.

    Teams group users for issue routing. Cartography doesn't read team
    schedules.
    """

    label: str = "PylonTeam"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
    properties: PylonTeamNodeProperties = PylonTeamNodeProperties()
    sub_resource_relationship: PylonTeamToOrganizationRel = PylonTeamToOrganizationRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [PylonUserToTeamRel(), PylonServiceAccountToTeamRel()],
    )
