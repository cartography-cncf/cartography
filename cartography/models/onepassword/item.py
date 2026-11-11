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
from cartography.models.onepassword.account import OnePasswordAccountToResourceRel
from cartography.models.ontology.labels import SECRET


@dataclass(frozen=True)
class OnePasswordItemNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="1Password item UUID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    title: PropertyRef = PropertyRef(
        "title",
        description=(
            "Item title. Present only when the collector runs with "
            "`--include-titles`."
        ),
    )
    category: PropertyRef = PropertyRef(
        "category",
        extra_index=True,
        description=(
            "Item category, such as `LOGIN`, `API_CREDENTIAL`, `SSH_KEY`, or "
            "`SECURE_NOTE`."
        ),
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="`ARCHIVED` for archived items. Active items have no state.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Time when the item was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="Time when the item was last updated.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Item version. 1Password increments it on every change.",
    )
    vault_id: PropertyRef = PropertyRef(
        "vault_id",
        description="UUID of the vault that contains the item.",
    )


@dataclass(frozen=True)
class OnePasswordVaultContainsItemRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OnePasswordVault)-[:CONTAINS]->(:OnePasswordItem)
class OnePasswordVaultContainsItemRel(CartographyRelSchema):
    """Places an item in its vault. Vault access grants access to the item."""

    target_node_label: str = "OnePasswordVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vault_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: OnePasswordVaultContainsItemRelProperties = (
        OnePasswordVaultContainsItemRelProperties()
    )


@dataclass(frozen=True)
class OnePasswordItemSchema(CartographyNodeSchema):
    """
    Metadata for a 1Password item, such as a login or API credential. The graph
    never stores item fields or secret values.
    """

    label: str = "OnePasswordItem"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SECRET])
    properties: OnePasswordItemNodeProperties = OnePasswordItemNodeProperties()
    sub_resource_relationship: OnePasswordAccountToResourceRel = (
        OnePasswordAccountToResourceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [OnePasswordVaultContainsItemRel()],
    )
