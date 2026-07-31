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
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class FlySecretNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Synthesized `<app_id>/<secret name>` key."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Secret name."
    )
    digest: PropertyRef = PropertyRef(
        "digest", description="Fly.io digest for the secret value."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    app_id: PropertyRef = PropertyRef("APP_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class FlySecretToAppRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:FlyApp)-[:RESOURCE]->(:FlySecret)
class FlySecretToAppRel(CartographyRelSchema):
    """Connects `FlyApp` to `FlySecret` through `RESOURCE`."""

    target_node_label: str = "FlyApp"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("APP_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: FlySecretToAppRelProperties = FlySecretToAppRelProperties()


@dataclass(frozen=True)
class FlySecretSchema(CartographyNodeSchema):
    """Represents a Fly app secret. Secret values are not read or stored."""

    label: str = "FlySecret"
    properties: FlySecretNodeProperties = FlySecretNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    sub_resource_relationship: FlySecretToAppRel = FlySecretToAppRel()
