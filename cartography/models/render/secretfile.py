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
class RenderSecretFileNodeProperties(CartographyNodeProperties):
    # Render's secret-file API has no id of its own; `serviceId/name` is unique per
    # service and stable across syncs, so it is used as the node's primary key.
    # The file's `content` is intentionally never read into this node - see
    # cartography/intel/render/secretfiles.py.
    id: PropertyRef = PropertyRef(
        "id", description="Synthetic id: `<service id>/<secret file name>`."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the secret file."
    )
    owner_id: PropertyRef = PropertyRef(
        "ownerId", description="ID of the owning Render workspace."
    )
    service_id: PropertyRef = PropertyRef(
        "serviceId", extra_index=True, description="ID of the service the secret file belongs to."
    )


@dataclass(frozen=True)
class RenderSecretFileToTenantRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderTenant)-[:RESOURCE]->(:RenderSecretFile)
class RenderSecretFileToTenantRel(CartographyRelSchema):
    """Connects a Render workspace to a secret file that it contains."""

    target_node_label: str = "RenderTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OWNER_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RenderSecretFileToTenantRelProperties = (
        RenderSecretFileToTenantRelProperties()
    )


@dataclass(frozen=True)
class RenderSecretFileToServiceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:RenderService)-[:HAS_SECRET]->(:RenderSecretFile)
class RenderSecretFileToServiceRel(CartographyRelSchema):
    """Connects a Render service to a secret file mounted on it."""

    target_node_label: str = "RenderService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("serviceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SECRET"
    properties: RenderSecretFileToServiceRelProperties = (
        RenderSecretFileToServiceRelProperties()
    )


@dataclass(frozen=True)
class RenderSecretFileSchema(CartographyNodeSchema):
    """
    Metadata for a secret file mounted on a Render service.

    Render's list API returns each secret file's full plaintext content alongside its
    name. Cartography deliberately ingests only the name - see
    cartography/intel/render/secretfiles.py for where that content is dropped.
    """

    label: str = "RenderSecretFile"
    properties: RenderSecretFileNodeProperties = RenderSecretFileNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    sub_resource_relationship: RenderSecretFileToTenantRel = (
        RenderSecretFileToTenantRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [RenderSecretFileToServiceRel()],
    )
