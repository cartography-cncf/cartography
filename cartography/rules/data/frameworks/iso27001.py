"""ISO/IEC 27001:2022 Annex A framework helpers.

Cartography exposes this as framework filter "iso:27001", following the same
short-name + scope pattern as CIS benchmark filters. The requirement
identifiers below are Annex A control identifiers from ISO/IEC 27001:2022,
which are derived from and aligned with ISO/IEC 27002:2022 controls.
"""

from cartography.rules.spec.model import Framework

ISO27001_FRAMEWORK_NAME = "ISO/IEC 27001:2022 Annex A"
ISO27001_SHORT_NAME = "ISO"
ISO27001_SCOPE = "27001"
ISO27001_REVISION = "2022"


def iso27001_annex_a(requirement: str) -> Framework:
    return Framework(
        name=ISO27001_FRAMEWORK_NAME,
        short_name=ISO27001_SHORT_NAME,
        scope=ISO27001_SCOPE,
        revision=ISO27001_REVISION,
        requirement=requirement,
    )
