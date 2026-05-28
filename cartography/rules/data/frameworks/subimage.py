"""SubImage framework helpers."""

from cartography.rules.spec.model import Framework

SUBIMAGE_COVERAGE_FRAMEWORK_NAME = "SubImage Coverage"
SUBIMAGE_COVERAGE_SHORT_NAME = "Coverage"
SUBIMAGE_COVERAGE_SCOPE = "subimage"


def subimage_coverage(requirement: str) -> Framework:
    return Framework(
        name=SUBIMAGE_COVERAGE_FRAMEWORK_NAME,
        short_name=SUBIMAGE_COVERAGE_SHORT_NAME,
        requirement=requirement,
        scope=SUBIMAGE_COVERAGE_SCOPE,
    )
