"""ISO/IEC 27001:2022 Annex A framework helpers.

Cartography exposes this as framework short name "27001" because users usually
run compliance reporting against ISO/IEC 27001. The requirement identifiers
below are Annex A control identifiers from ISO/IEC 27001:2022, which are
derived from and aligned with ISO/IEC 27002:2022 controls.
"""

from cartography.rules.spec.model import Framework

ISO27001_FRAMEWORK_NAME = "ISO/IEC 27001:2022 Annex A"
ISO27001_SHORT_NAME = "27001"
ISO27001_REVISION = "2022"


def iso27001_annex_a(requirement: str) -> Framework:
    return Framework(
        name=ISO27001_FRAMEWORK_NAME,
        short_name=ISO27001_SHORT_NAME,
        revision=ISO27001_REVISION,
        requirement=requirement,
    )
