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
class RenderEnvVarNodeProperties(CartographyNodeProperties):
    # Render's env-var API has no id of its own; `serviceId/key` is unique per service
    # and stable across syncs, matching RenderSecretFile's exact convention.
    # The variable's `value` is intentionally never read into this node - see
    # cartography/intel/render/envvars.py.
    id: PropertyRef = PropertyRef(
        "id", description="Synthetic id: `<service id>/<env var key>`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    key: PropertyRef = PropertyRef(
        "key", extra_index=True, description="Name of the environment variable."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId",
        extra_index=True,
        description="ID of the service the env var belongs to.",
    )


@dataclass(frozen=True)
class RenderEnvVarToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderEnvVar)
class RenderEnvVarToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to an env var that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderEnvVarToTenantRelProperties = RenderEnvVarToTenantRelProperties()


@dataclass(frozen=True)
class RenderEnvVarToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderService)-[:USES_SECRET]->(:RenderEnvVar)
class RenderEnvVarToServiceRel(CartographyRelSchema):
    """
    Connects a Render service to an env var set on it.

    rel_label is USES_SECRET (not e.g. HAS_ENV_VAR) for the same reason as
    RenderSecretFileToServiceRel: RenderService carries the ComputeInstance ontology
    label and RenderEnvVar carries Secret, and the repo enforces USES_SECRET as the
    canonical label for that edge (test_ontology_rel_constraints). Matches the existing
    cross-provider convention of treating generic env-var nodes as Secret-ontology
    (see RailwayVariable, NetlifyEnvVar).
    """

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("serviceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "USES_SECRET"
    properties: RenderEnvVarToServiceRelProperties = (
        RenderEnvVarToServiceRelProperties()
    )


@dataclass(frozen=True)
class RenderEnvVarSchema(CartographyNodeSchema):
    """
    Metadata for an environment variable set directly on a Render service.

    Render's list API returns each env var's full value alongside its key.
    Cartography deliberately ingests only the key - see
    cartography/intel/render/envvars.py for where that value is dropped.
    """

    label: str = "RenderEnvVar"
    properties: RenderEnvVarNodeProperties = RenderEnvVarNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    sub_resource_relationship: RenderEnvVarToTenantRel = RenderEnvVarToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderEnvVarToServiceRel()],
    )
