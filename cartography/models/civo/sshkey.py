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
class CivoSSHKeyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Civo SSH key ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Name of the SSH key."
    )
    fingerprint: PropertyRef = PropertyRef(
        "fingerprint",
        extra_index=True,
        description="Fingerprint of the SSH public key (not the key material itself).",
    )
    account_id: PropertyRef = PropertyRef(
        "ACCOUNT_ID", set_in_kwargs=True, description="Civo account ID."
    )


@dataclass(frozen=True)
class CivoSSHKeyToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:CivoAccount)-[:RESOURCE]->(:CivoSSHKey)
class CivoSSHKeyToAccountRel(CartographyRelSchema):
    """Connects `CivoAccount` to `CivoSSHKey` through `RESOURCE`."""

    target_node_label: str = "CivoAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CivoSSHKeyToAccountRelProperties = CivoSSHKeyToAccountRelProperties()


@dataclass(frozen=True)
class CivoSSHKeySchema(CartographyNodeSchema):
    """Represents an SSH public key registered on a Civo account. Only the
    fingerprint is stored - the API never returns private key material."""

    label: str = "CivoSSHKey"
    properties: CivoSSHKeyNodeProperties = CivoSSHKeyNodeProperties()
    sub_resource_relationship: CivoSSHKeyToAccountRel = CivoSSHKeyToAccountRel()
