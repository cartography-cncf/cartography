from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class CVEMetadataFeedNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "FEED_ID", description="CVE metadata feed identifier."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    source_nvd: PropertyRef = PropertyRef(
        "source_nvd",
        description="Whether NVD enrichment was enabled for the sync.",
    )
    source_epss: PropertyRef = PropertyRef(
        "source_epss",
        description="Whether EPSS enrichment was enabled for the sync.",
    )
    source_kev: PropertyRef = PropertyRef(
        "source_kev",
        description="Whether CISA KEV catalog enrichment was enabled for the sync.",
    )
    source_vulnrichment: PropertyRef = PropertyRef(
        "source_vulnrichment",
        description="Whether CISA Vulnrichment enrichment was enabled for the sync.",
    )
    kev_catalog_version: PropertyRef = PropertyRef(
        "kev_catalog_version",
        description=(
            "catalogVersion of the KEV catalog used by the sync. Unset when no "
            "catalog was used: the source was disabled, the fetch failed, or the "
            "catalog listed no CVEs."
        ),
    )
    kev_date_released: PropertyRef = PropertyRef(
        "kev_date_released",
        description=(
            "dateReleased of the KEV catalog used by the sync. Unset when no "
            "catalog was used."
        ),
    )
    vulnrichment_commit: PropertyRef = PropertyRef(
        "vulnrichment_commit",
        description=(
            "Git commit of the Vulnrichment repository archive used by the sync, "
            "read from the archive's pax header. Unset when no archive was used "
            "(the source was disabled, or the archive could not be read in full "
            "or held no CVE records) or when it carried no commit."
        ),
    )


@dataclass(frozen=True)
class CVEMetadataFeedSchema(CartographyNodeSchema):
    """The enrichment feed used to manage CVE metadata lifecycle."""

    label: str = "CVEMetadataFeed"
    properties: CVEMetadataFeedNodeProperties = CVEMetadataFeedNodeProperties()
