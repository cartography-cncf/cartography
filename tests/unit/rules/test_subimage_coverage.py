from cartography.rules.data.rules import RULES
from cartography.rules.data.rules.subimage_coverage import aws_account_not_synced
from cartography.rules.data.rules.subimage_coverage import container_image_not_found
from cartography.rules.data.rules.subimage_coverage import (
    repository_without_slsa_provenance,
)
from cartography.rules.data.rules.subimage_coverage import (
    subimage_framework_disabled_module_enabled,
)
from cartography.rules.data.rules.subimage_coverage import (
    subimage_module_not_configured,
)
from cartography.rules.runners import get_all_frameworks
from cartography.rules.spec.model import Module

SUBIMAGE_COVERAGE_RULES = (
    subimage_module_not_configured,
    subimage_framework_disabled_module_enabled,
    container_image_not_found,
    repository_without_slsa_provenance,
    aws_account_not_synced,
)


def test_subimage_coverage_rules_registered_without_frameworks():
    for rule in SUBIMAGE_COVERAGE_RULES:
        assert rule.id in RULES
        assert RULES[rule.id] is rule
        assert rule.version == "0.1.0"
        assert rule.frameworks == ()


def test_subimage_coverage_rules_keep_coverage_tags():
    expected_tags = {
        subimage_module_not_configured.id: {
            "subimage",
            "coverage",
            "misconfiguration",
        },
        subimage_framework_disabled_module_enabled.id: {
            "subimage",
            "coverage",
            "misconfiguration",
        },
        container_image_not_found.id: {
            "subimage",
            "container",
            "coverage",
            "infrastructure",
        },
        repository_without_slsa_provenance.id: {
            "subimage",
            "coverage",
            "supply-chain",
            "slsa",
        },
        aws_account_not_synced.id: {
            "subimage",
            "aws",
            "coverage",
            "infrastructure",
            "misconfiguration",
        },
    }

    for rule in SUBIMAGE_COVERAGE_RULES:
        assert set(rule.tags) == expected_tags[rule.id]


def test_subimage_coverage_rule_modules():
    assert subimage_module_not_configured.modules == {Module.SUBIMAGE}
    assert subimage_framework_disabled_module_enabled.modules == {Module.SUBIMAGE}
    assert container_image_not_found.modules == {Module.CROSS_CLOUD}
    assert repository_without_slsa_provenance.modules == {Module.SUBIMAGE}
    assert aws_account_not_synced.modules == {Module.AWS}


def test_subimage_coverage_not_advertised_as_compliance_framework():
    frameworks = get_all_frameworks()

    assert "coverage" not in frameworks
    for framework_list in frameworks.values():
        for framework in framework_list:
            assert framework.name != "subimage coverage"
            assert not framework.matches("coverage", "subimage")
