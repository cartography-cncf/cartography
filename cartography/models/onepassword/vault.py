from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.onepassword.account import OnePasswordAccountToResourceRel


@dataclass(frozen=True)
class OnePasswordVaultNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="1Password vault UUID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        description=(
            "Vault name. Present only when the collector runs with "
            "`--include-titles`."
        ),
    )


@dataclass(frozen=True)
class OnePasswordVaultSchema(CartographyNodeSchema):
    """A 1Password vault in the collector's configured scope."""

    label: str = "OnePasswordVault"
    properties: OnePasswordVaultNodeProperties = OnePasswordVaultNodeProperties()
    sub_resource_relationship: OnePasswordAccountToResourceRel = (
        OnePasswordAccountToResourceRel()
    )


@dataclass(frozen=True)
class OnePasswordCanAccessVaultRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    permissions: PropertyRef = PropertyRef(
        "permissions",
        description=(
            "Lowercase names of the granted vault permissions, such as "
            "`read_items`, `reveal_item_password`, and `manage_vault`."
        ),
    )
    permissions_bitmask: PropertyRef = PropertyRef(
        "permissions_bitmask",
        description=(
            "Raw permission bitmask from the 1Password SDK. It keeps bits that "
            "have no name in `permissions`."
        ),
    )


@dataclass(frozen=True)
# (:OnePasswordUser)-[:CAN_ACCESS]->(:OnePasswordVault)
class OnePasswordUserCanAccessVaultRel(CartographyRelSchema):
    """A direct vault grant to a user. Access through groups is a separate path."""

    source_node_label: str = "OnePasswordUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    target_node_label: str = "OnePasswordVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vault_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: OnePasswordCanAccessVaultRelProperties = (
        OnePasswordCanAccessVaultRelProperties()
    )


@dataclass(frozen=True)
# (:OnePasswordServiceAccount)-[:CAN_ACCESS]->(:OnePasswordVault)
class OnePasswordServiceAccountCanAccessVaultRel(CartographyRelSchema):
    """A direct vault grant to a service account."""

    source_node_label: str = "OnePasswordServiceAccount"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    target_node_label: str = "OnePasswordVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vault_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: OnePasswordCanAccessVaultRelProperties = (
        OnePasswordCanAccessVaultRelProperties()
    )


@dataclass(frozen=True)
# (:OnePasswordGroup)-[:CAN_ACCESS]->(:OnePasswordVault)
class OnePasswordGroupCanAccessVaultRel(CartographyRelSchema):
    """A vault grant to a group. Every group member receives these permissions."""

    source_node_label: str = "OnePasswordGroup"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("principal_id")},
    )
    target_node_label: str = "OnePasswordVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("vault_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_ACCESS"
    properties: OnePasswordCanAccessVaultRelProperties = (
        OnePasswordCanAccessVaultRelProperties()
    )
