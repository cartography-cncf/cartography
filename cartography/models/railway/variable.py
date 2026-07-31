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
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
# SECURITY: there is deliberately no `value` property. Railway can return variable values,
# but Cartography ingests names only and must never store secret material. The GraphQL
# document in cartography/intel/railway/queries.py does not request values either.
class RailwayVariableNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Railway variable.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the variable."
    )
    # A sealed variable is write-only: not even the Railway dashboard can read it back.
    is_sealed: PropertyRef = PropertyRef(
        "isSealed",
        description="Whether the variable is write-only and cannot be read back.",
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId",
        description="ID of the scoped service, or null for a shared variable.",
    )
    environment_id: PropertyRef = PropertyRef(
        "environmentId", description="ID of the environment containing the variable."
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt", description="Time when the variable was created."
    )


@dataclass(frozen=True)
class RailwayVariableToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayProject)-[:RESOURCE]->(:RailwayVariable)
class RailwayVariableToProjectRel(CartographyRelSchema):
    """Connects a Railway project to a variable that it contains."""

    target_node_label: str = "RailwayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RailwayVariableToProjectRelProperties = (
        RailwayVariableToProjectRelProperties()
    )


@dataclass(frozen=True)
class RailwayVariableToServiceInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayServiceInstance)-[:USES_SECRET]->(:RailwayVariable)
# Only for service-scoped variables; shared variables have a null serviceId, so the matcher
# finds nothing and the edge is simply not created for them.
class RailwayVariableToServiceInstanceRel(CartographyRelSchema):
    """Identifies a Railway service instance that consumes a service-scoped variable."""

    target_node_label: str = "RailwayServiceInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_id": PropertyRef("serviceId"),
            "environment_id": PropertyRef("environmentId"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES_SECRET"
    properties: RailwayVariableToServiceInstanceRelProperties = (
        RailwayVariableToServiceInstanceRelProperties()
    )


@dataclass(frozen=True)
class RailwayVariableToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RailwayEnvironment)-[:HAS]->(:RailwayVariable)
# Every variable belongs to an environment, whether or not it is scoped to one service.
class RailwayVariableToEnvironmentRel(CartographyRelSchema):
    """Connects a Railway environment to a variable defined within it."""

    target_node_label: str = "RailwayEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("environmentId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: RailwayVariableToEnvironmentRelProperties = (
        RailwayVariableToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class RailwayVariableSchema(CartographyNodeSchema):
    """A named Railway environment variable whose value is not ingested."""

    label: str = "RailwayVariable"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    properties: RailwayVariableNodeProperties = RailwayVariableNodeProperties()
    sub_resource_relationship: RailwayVariableToProjectRel = (
        RailwayVariableToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RailwayVariableToServiceInstanceRel(),
            RailwayVariableToEnvironmentRel(),
        ],
    )
