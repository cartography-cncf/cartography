from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class OCITenancyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ocid", description="OCI tenancy OCID.")
    ocid: PropertyRef = PropertyRef(
        "ocid", extra_index=True, description="OCI tenancy OCID."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )
    name: PropertyRef = PropertyRef("name", description="Tenancy profile name.")


@dataclass(frozen=True)
class OCITenancySchema(CartographyNodeSchema):
    """An OCI tenancy that serves as the root OCI resource."""

    label: str = "OCITenancy"
    properties: OCITenancyNodeProperties = OCITenancyNodeProperties()
    # OCITenancy is the root tenant-like object, so it has no sub_resource_relationship
    scoped_cleanup: bool = False
