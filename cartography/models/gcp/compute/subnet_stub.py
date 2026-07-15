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
class GCPSubnetStubNodeProperties(CartographyNodeProperties):
    """
    Minimal properties for GCPSubnet stub nodes.
    These are created to ensure PART_OF_SUBNET relationships can be established
    even before the full subnet data is loaded.
    """

    id: PropertyRef = PropertyRef(
        "partial_uri",
        description="A partial resource URI representing this Subnet.  Has the form `projects/{project}/regions/{region}/subnetworks/{subnet name}`.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    partial_uri: PropertyRef = PropertyRef(
        "partial_uri", extra_index=True, description="Same as `id`."
    )


@dataclass(frozen=True)
class GCPSubnetStubToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPSubnetStubToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("PROJECT_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPSubnetStubToProjectRelProperties = (
        GCPSubnetStubToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPSubnetStubSchema(CartographyNodeSchema):
    """Representation of a GCP [Subnetwork](https://cloud.google.com/compute/docs/reference/rest/v1/subnetworks)."""

    label: str = "GCPSubnet"
    properties: GCPSubnetStubNodeProperties = GCPSubnetStubNodeProperties()
    # Deliberately no `Subnet` semantic label here: stubs only carry partial_uri
    # and would surface in cross-cloud `(:Subnet)` queries with a null _ont_name
    # (the GCP mapping resolves the ontology name from the `name` field, which the
    # stub lacks). The full GCPSubnetSchema attaches the Subnet label and _ont_*
    # fields once the real subnet data is synced.
    sub_resource_relationship: GCPSubnetStubToProjectRel = GCPSubnetStubToProjectRel()
