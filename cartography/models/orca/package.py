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
class OrcaPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Organization ID and normalized package ID, joined by `|`.",
    )
    normalized_id: PropertyRef = PropertyRef(
        "normalized_id",
        extra_index=True,
        description=(
            "Normalized package ID, `{type}|{namespace/}{name}|{version}`, shared "
            "with PackageVersion."
        ),
    )
    name: PropertyRef = PropertyRef("name", description="Package name from the purl.")
    version: PropertyRef = PropertyRef(
        "version",
        description="Package version from the purl.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        description="Package ecosystem from the purl, such as npm, maven, or deb.",
    )
    purl: PropertyRef = PropertyRef(
        "purl",
        description="Package URL that Orca reports for the installed package.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OrcaPackageToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OrcaPackageToOrganizationRel(CartographyRelSchema):
    """Links an Orca organization to a package found on one of its assets."""

    target_node_label: str = "OrcaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORCA_ORGANIZATION_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OrcaPackageToOrganizationRelProperties = (
        OrcaPackageToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OrcaPackageSchema(CartographyNodeSchema):
    """A package version that Orca reports as installed on a vulnerable asset."""

    label: str = "OrcaPackage"
    properties: OrcaPackageNodeProperties = OrcaPackageNodeProperties()
    sub_resource_relationship: OrcaPackageToOrganizationRel = (
        OrcaPackageToOrganizationRel()
    )
