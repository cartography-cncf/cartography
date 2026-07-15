from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class VercelSharedEnvVarNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Shared environment variable ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )
    key: PropertyRef = PropertyRef(
        "key", extra_index=True, description="Shared environment variable name."
    )
    type: PropertyRef = PropertyRef(
        "type", description="Shared environment variable type."
    )
    target: PropertyRef = PropertyRef(
        "target", description="Target environments for the shared variable."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Timestamp when the shared variable was created."
    )
    updated_at: PropertyRef = PropertyRef(
        "updatedAt", description="Timestamp when the shared variable was last updated."
    )
    # NOTE: Value is intentionally omitted to avoid storing secrets.


@dataclass(frozen=True)
class VercelSharedEnvVarToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:VercelTeam)-[:RESOURCE]->(:VercelSharedEnvironmentVariable)
class VercelSharedEnvVarToTeamRel(CartographyRelSchema):
    """The Vercel team contains this shared environment variable as a resource."""

    target_node_label: str = "VercelTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TEAM_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: VercelSharedEnvVarToTeamRelProperties = (
        VercelSharedEnvVarToTeamRelProperties()
    )


@dataclass(frozen=True)
class VercelSharedEnvironmentVariableSchema(CartographyNodeSchema):
    """A team-scoped Vercel environment variable whose value is not stored."""

    label: str = "VercelSharedEnvironmentVariable"
    properties: VercelSharedEnvVarNodeProperties = VercelSharedEnvVarNodeProperties()
    sub_resource_relationship: VercelSharedEnvVarToTeamRel = (
        VercelSharedEnvVarToTeamRel()
    )
