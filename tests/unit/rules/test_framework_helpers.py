from cartography.rules.data.frameworks.cis import cis_aws
from cartography.rules.data.frameworks.cis import cis_gcp
from cartography.rules.data.frameworks.cis import cis_google_workspace
from cartography.rules.data.frameworks.cis import cis_kubernetes
from cartography.rules.data.frameworks.iso27001 import iso27001_annex_a
from cartography.rules.data.frameworks.nist_ai_rmf import nist_ai_rmf
from cartography.rules.data.frameworks.subimage import subimage_coverage


def test_framework_helpers_preserve_framework_metadata():
    helpers = [
        (
            cis_aws("4.1"),
            "cis aws foundations benchmark",
            "cis",
            "aws",
            "6.0.0",
            "4.1",
        ),
        (
            cis_gcp("3.1"),
            "cis gcp foundations benchmark",
            "cis",
            "gcp",
            "4.0",
            "3.1",
        ),
        (
            cis_kubernetes("5.1.1"),
            "cis kubernetes benchmark",
            "cis",
            "kubernetes",
            "1.12",
            "5.1.1",
        ),
        (
            cis_google_workspace("4.1.1.3"),
            "cis google workspace foundations benchmark",
            "cis",
            "googleworkspace",
            "1.3",
            "4.1.1.3",
        ),
        (
            iso27001_annex_a("8.15"),
            "iso/iec 27001:2022 annex a",
            "27001",
            None,
            "2022",
            "8.15",
        ),
        (
            nist_ai_rmf("MAP 1"),
            "nist ai risk management framework",
            "nist-ai-rmf",
            None,
            "1.0",
            "map 1",
        ),
        (
            subimage_coverage("1.1"),
            "subimage coverage",
            "coverage",
            "subimage",
            None,
            "1.1",
        ),
    ]

    for framework, name, short_name, scope, revision, requirement in helpers:
        assert framework.name == name
        assert framework.short_name == short_name
        assert framework.scope == scope
        assert framework.revision == revision
        assert framework.requirement == requirement
