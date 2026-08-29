from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ModalDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Domain ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    domain_name: PropertyRef = PropertyRef(
        "domain_name", extra_index=True, description="The custom hostname."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="When the domain was added."
    )
    # Raw CERTIFICATE_STATUS_* value. A domain stuck PENDING or gone FAILED/REVOKED is serving
    # traffic without a valid certificate, which is why this is indexed.
    certificate_status: PropertyRef = PropertyRef(
        "certificate_status",
        extra_index=True,
        description="Raw `CERTIFICATE_STATUS_*` value. A domain stuck `PENDING`, or `FAILED`/`REVOKED`, is serving without a valid certificate.",
    )


@dataclass(frozen=True)
class ModalDomainToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspace)-[:RESOURCE]->(:ModalDomain)
class ModalDomainToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalDomainToWorkspaceRelProperties = (
        ModalDomainToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
# A custom domain attached to a Modal workspace, used to serve web endpoints on your own
# hostname. Workspace-scoped: the `DomainList` RPC is workspace-wide, not per environment.
#
# It carries no ontology label. `DNSZone` would be wrong (this is a hostname, not a zone), and
# `Certificate` would be a one-field stub since Modal exposes only a status, no issuer or
# expiry.
#
# Requires a paid Modal add-on. On workspaces without it the API answers UNIMPLEMENTED, which
# the adapter treats as "no domains" rather than an error, so this node type is simply absent
# there.
class ModalDomainSchema(CartographyNodeSchema):
    """Represents a custom domain attached to a Modal workspace, used to serve web endpoints on your own hostname. **Workspace-scoped**, not environment-scoped: the underlying API call is workspace-wide. Custom domains require a paid Modal add-on. On workspaces without it the API answers `UNIMPLEMENTED`, which Cartography treats as \"no domains\" rather than an error, so this node type is simply absent there. This node carries no ontology label: `DNSZone` would be wrong (a hostname is not a zone) and `Certificate` would be a one-field stub, since Modal exposes only a status with no issuer or expiry."""

    label: str = "ModalDomain"
    properties: ModalDomainNodeProperties = ModalDomainNodeProperties()
    sub_resource_relationship: ModalDomainToWorkspaceRel = ModalDomainToWorkspaceRel()


@dataclass(frozen=True)
class ModalDomainDNSRecordNodeProperties(CartographyNodeProperties):
    # Modal gives these records no id, so it is synthesised as
    # "<domain_id>/<type>/<name>", which is unique per domain.
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthesised as `<domain_id>/<type>/<name>`; Modal gives these records no id.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Raw DNS_RECORD_TYPE_* value: A, TXT or CNAME.
    type: PropertyRef = PropertyRef(
        "type", description="Raw `DNS_RECORD_TYPE_*` value: A, TXT or CNAME."
    )
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Record name."
    )
    value: PropertyRef = PropertyRef("value", description="Record value.")
    domain_id: PropertyRef = PropertyRef(
        "domain_id", description="ID of the owning domain."
    )


@dataclass(frozen=True)
class ModalDomainDNSRecordToWorkspaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalWorkspace)-[:RESOURCE]->(:ModalDomainDNSRecord)
class ModalDomainDNSRecordToWorkspaceRel(CartographyRelSchema):
    target_node_label: str = "ModalWorkspace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKSPACE_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ModalDomainDNSRecordToWorkspaceRelProperties = (
        ModalDomainDNSRecordToWorkspaceRelProperties()
    )


@dataclass(frozen=True)
class ModalDomainToRecordRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ModalDomain)-[:HAS_RECORD]->(:ModalDomainDNSRecord)
class ModalDomainToRecordRel(CartographyRelSchema):
    target_node_label: str = "ModalDomain"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("domain_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_RECORD"
    properties: ModalDomainToRecordRelProperties = ModalDomainToRecordRelProperties()


@dataclass(frozen=True)
# A DNS record Modal asks you to create in order to validate a custom domain.
#
# Deliberately NOT labelled DNSRecord. These are records Modal *requests*, i.e. desired
# configuration, not DNS state observed in the wild. Labelling them would feed the DNS record
# linking analysis entries that may not exist in any zone, producing phantom resolution paths.
class ModalDomainDNSRecordSchema(CartographyNodeSchema):
    """Represents a DNS record Modal asks you to create in order to validate a custom domain. Deliberately **not** labelled `DNSRecord`. These are records Modal *requests*, meaning desired configuration, not DNS state observed in the wild. Labelling them would feed the DNS record linking analysis entries that may not exist in any zone, producing phantom resolution paths."""

    label: str = "ModalDomainDNSRecord"
    properties: ModalDomainDNSRecordNodeProperties = (
        ModalDomainDNSRecordNodeProperties()
    )
    sub_resource_relationship: ModalDomainDNSRecordToWorkspaceRel = (
        ModalDomainDNSRecordToWorkspaceRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ModalDomainToRecordRel()],
    )
