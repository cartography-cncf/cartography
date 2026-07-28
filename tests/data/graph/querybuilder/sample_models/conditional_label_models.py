from dataclasses import dataclass
from typing import Optional

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.nodes import LabelKind
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ContainerImageProperties(CartographyNodeProperties):
    """Properties for a container image node - mimics ECR image use case."""

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    digest: PropertyRef = PropertyRef("digest")
    image_type: PropertyRef = PropertyRef("image_type")
    repository: PropertyRef = PropertyRef("repository")


RESOURCE = ExtraNodeLabel(
    label="Resource",
    description="A generic resource used in query-builder tests.",
)


IMAGE = ExtraNodeLabel(
    label="Image",
    description="A container image used in query-builder tests.",
    kind=LabelKind.ONTOLOGY,
)


IMAGE_ATTESTATION = ExtraNodeLabel(
    label="ImageAttestation",
    description="A container-image attestation used in query-builder tests.",
    kind=LabelKind.ONTOLOGY,
)


IMAGE_MANIFEST_LIST = ExtraNodeLabel(
    label="ImageManifestList",
    description="A multi-platform image manifest used in query-builder tests.",
    kind=LabelKind.ONTOLOGY,
)


SECURITY_FINDING = ExtraNodeLabel(
    label="SecurityFinding",
    description="A generic security finding used in query-builder tests.",
)


CRITICAL = ExtraNodeLabel(
    label="Critical",
    description="A critical finding used in query-builder tests.",
)


URGENT = ExtraNodeLabel(
    label="Urgent",
    description="An urgent finding used in query-builder tests.",
)


@dataclass(frozen=True)
class ContainerImageToRegistryRelProps(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ContainerImageToRegistryRel(CartographyRelSchema):
    """
    Define a sub resource relationship.
    (:ContainerImage)<-[:RESOURCE]-(:ContainerRegistry)
    """

    target_node_label: str = "ContainerRegistry"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("REGISTRY_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ContainerImageToRegistryRelProps = ContainerImageToRegistryRelProps()


@dataclass(frozen=True)
class ContainerImageSchema(CartographyNodeSchema):
    """
    Schema for container images with conditional labels based on image type.
    This mimics the ECR use case where different image types map to different ontology labels.
    """

    label: str = "ContainerImage"
    properties: ContainerImageProperties = ContainerImageProperties()
    sub_resource_relationship: ContainerImageToRegistryRel = (
        ContainerImageToRegistryRel()
    )
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            RESOURCE,
            IMAGE.when(image_type="IMAGE"),
            IMAGE_ATTESTATION.when(image_type="IMAGE_ATTESTATION"),
            IMAGE_MANIFEST_LIST.when(image_type="IMAGE_MANIFEST_LIST"),
        ],
    )


@dataclass(frozen=True)
class ContainerImageSchemaNoSubResource(CartographyNodeSchema):
    """
    Schema for container images without sub-resource (unscoped).
    Used to test conditional labels without scoping.
    """

    label: str = "ContainerImage"
    properties: ContainerImageProperties = ContainerImageProperties()
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            RESOURCE,
            IMAGE.when(image_type="IMAGE"),
            IMAGE_ATTESTATION.when(image_type="IMAGE_ATTESTATION"),
        ],
    )
    scoped_cleanup: bool = False


@dataclass(frozen=True)
class VulnerabilityProperties(CartographyNodeProperties):
    """Properties for a vulnerability node - tests multi-condition labels."""

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    severity: PropertyRef = PropertyRef("severity")
    is_exploitable: PropertyRef = PropertyRef("is_exploitable")
    has_fix: PropertyRef = PropertyRef("has_fix")


@dataclass(frozen=True)
class VulnerabilitySchema(CartographyNodeSchema):
    """
    Schema for vulnerabilities with conditional labels based on multiple conditions.
    """

    label: str = "Vulnerability"
    properties: VulnerabilityProperties = VulnerabilityProperties()
    extra_node_labels: Optional[ExtraNodeLabels] = ExtraNodeLabels(
        [
            SECURITY_FINDING,
            CRITICAL.when(severity="critical"),
            URGENT.when(severity="critical", is_exploitable="true"),
        ],
    )
    scoped_cleanup: bool = False
