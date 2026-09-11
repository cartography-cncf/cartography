from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class OpsgenieTeamNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Opsgenie team ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Team name.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Team description.",
    )


@dataclass(frozen=True)
class OpsgenieAccountToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OpsgenieAccountToTeamRel(CartographyRelSchema):
    """The account contains the team."""

    target_node_label: str = "OpsgenieAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OpsgenieAccountToTeamRelProperties = (
        OpsgenieAccountToTeamRelProperties()
    )


@dataclass(frozen=True)
class OpsgenieTeamSchema(CartographyNodeSchema):
    """A team in an Opsgenie account."""

    label: str = "OpsgenieTeam"
    properties: OpsgenieTeamNodeProperties = OpsgenieTeamNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])
    sub_resource_relationship: OpsgenieAccountToTeamRel = OpsgenieAccountToTeamRel()
