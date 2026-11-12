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
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class OnePasswordAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="1Password account UUID, lowercased by the collector.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    snapshot_id: PropertyRef = PropertyRef(
        "snapshot_id",
        description="Unique ID of the collector run that produced the ingested snapshot.",
    )
    snapshot_collected_at: PropertyRef = PropertyRef(
        "snapshot_collected_at",
        description=(
            "UTC time when the collector finished the ingested snapshot. "
            "Use it to judge how current the account's access data is."
        ),
    )
    collector_version: PropertyRef = PropertyRef(
        "collector_version",
        description="Version of the collector that produced the ingested snapshot.",
    )
    vault_scope: PropertyRef = PropertyRef(
        "vault_scope",
        description=(
            "IDs of the vaults the snapshot covers. Vaults outside this list are "
            "not collected."
        ),
    )


@dataclass(frozen=True)
class OnePasswordAccountSchema(CartographyNodeSchema):
    """A 1Password account (business tenant) described by a collector snapshot."""

    label: str = "OnePasswordAccount"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    properties: OnePasswordAccountNodeProperties = OnePasswordAccountNodeProperties()


@dataclass(frozen=True)
class OnePasswordAccountToResourceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OnePasswordAccount)-[:RESOURCE]->(:OnePassword*)
class OnePasswordAccountToResourceRel(CartographyRelSchema):
    """Scopes a 1Password resource to the account that owns it."""

    target_node_label: str = "OnePasswordAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OnePasswordAccountToResourceRelProperties = (
        OnePasswordAccountToResourceRelProperties()
    )
