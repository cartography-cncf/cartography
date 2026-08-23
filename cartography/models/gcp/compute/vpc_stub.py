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
class GCPVpcStubNodeProperties(CartographyNodeProperties):
    """
    Minimal properties for GCPVpc stub nodes.
    These are created from VPC peering `peerNetwork` references so that
    PEER_NETWORK relationships can be established even when the peer VPC's
    project is not synced.
    """

    id: PropertyRef = PropertyRef(
        "partial_uri",
        description="The partial resource URI representing this VPC.  Has the form `projects/{project_name}/global/networks/{vpc name}`.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    partial_uri: PropertyRef = PropertyRef(
        "partial_uri", extra_index=True, description="Same as `id`."
    )
    # NOTE: descriptions for properties shared with GCPVpcSchema must match it
    # exactly; the schema-docs generator rejects conflicting descriptions for
    # the same (label, property) pair.
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="The project ID that this VPC belongs to.",
    )


@dataclass(frozen=True)
class GCPVpcStubToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPVpcStubToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    # Matched on the peer project parsed from the stub's own partial URI (data
    # field), not on the PROJECT_ID kwarg of the syncing project: the stub
    # represents a VPC owned by the *peer* project.
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPVpcStubToProjectRelProperties = GCPVpcStubToProjectRelProperties()


@dataclass(frozen=True)
class GCPVpcStubSchema(CartographyNodeSchema):
    """Representation of a GCP [VPC](https://cloud.google.com/compute/docs/reference/rest/v1/networks/) placeholder."""

    label: str = "GCPVpc"
    properties: GCPVpcStubNodeProperties = GCPVpcStubNodeProperties()
    # Deliberately no `VirtualNetwork` semantic label here: stubs only carry
    # partial_uri and would surface in cross-cloud `(:VirtualNetwork)` queries
    # with a null _ont_name (the GCP mapping resolves the ontology name from the
    # `name` field, which the stub lacks). The full GCPVpcSchema attaches the
    # VirtualNetwork label and _ont_* fields once the real VPC data is synced.
    sub_resource_relationship: GCPVpcStubToProjectRel = GCPVpcStubToProjectRel()
