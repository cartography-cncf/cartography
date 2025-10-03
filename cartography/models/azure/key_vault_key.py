import logging
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureKeyVaultKeyProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    enabled: PropertyRef = PropertyRef("enabled")
    created_on: PropertyRef = PropertyRef("createdOn")
    updated_on: PropertyRef = PropertyRef("updatedOn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultKeyToVaultRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureKeyVaultKeyToVaultRel(CartographyRelSchema):
    target_node_label: str = "AzureKeyVault"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("VAULT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: AzureKeyVaultKeyToVaultRelProperties = (
        AzureKeyVaultKeyToVaultRelProperties()
    )


@dataclass(frozen=True)
class AzureKeyVaultKeySchema(CartographyNodeSchema):
    label: str = "AzureKeyVaultKey"
    properties: AzureKeyVaultKeyProperties = AzureKeyVaultKeyProperties()
    sub_resource_relationship: AzureKeyVaultKeyToVaultRel = AzureKeyVaultKeyToVaultRel()
