from cartography.rules.data.frameworks.cis import cis_aws
from cartography.rules.data.frameworks.cis import cis_gcp
from cartography.rules.data.frameworks.cis import cis_google_workspace
from cartography.rules.data.frameworks.cis import cis_kubernetes
from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.nist_ai_rmf import nist_ai_rmf


def test_framework_helpers_preserve_framework_metadata():
    helpers = [
        (
            cis_aws("4.1"),
            "cis aws foundations benchmark",
            "cis",
            "aws",
            "6.0.0",
            "4.1",
            "Ensure CloudTrail is enabled in all regions",
        ),
        (
            cis_gcp("3.1"),
            "cis gcp foundations benchmark",
            "cis",
            "gcp",
            "4.0",
            "3.1",
            "Ensure That the Default Network Does Not Exist in a Project",
        ),
        (
            cis_kubernetes("5.1.1"),
            "cis kubernetes benchmark",
            "cis",
            "kubernetes",
            "1.12",
            "5.1.1",
            "Ensure that the cluster-admin role is only used where required",
        ),
        (
            cis_google_workspace("4.1.1.3"),
            "cis google workspace foundations benchmark",
            "cis",
            "googleworkspace",
            "1.3",
            "4.1.1.3",
            "Ensure 2-Step Verification (Multi-Factor Authentication) is enforced for all users",
        ),
        (
            iso27001_annex_a("8.15"),
            "iso/iec 27001:2022 annex a",
            "iso27001",
            None,
            "2022",
            "8.15",
            "Logging",
        ),
        (
            nist_ai_rmf("MAP 1"),
            "nist ai risk management framework",
            "nist-ai-rmf",
            None,
            "1.0",
            "map 1",
            "Context is established and understood",
        ),
    ]

    for (
        framework,
        name,
        short_name,
        scope,
        revision,
        requirement,
        control_title,
    ) in helpers:
        assert framework.name == name
        assert framework.short_name == short_name
        assert framework.scope == scope
        assert framework.revision == revision
        assert framework.requirement == requirement
        assert framework.control_title == control_title


def test_framework_helpers_allow_explicit_control_title_override():
    framework = cis_aws("4.1", control_title="Custom control title")

    assert framework.control_title == "Custom control title"
