"""
Unit tests for Semgrep findings helpers.
"""

import copy

from cartography.intel.semgrep.findings import transform_sca_vulns
from tests.data.semgrep.sca import SCA_RESPONSE


def test_transform_sca_vulns_uppercases_reachability():
    raw_vulns = copy.deepcopy(SCA_RESPONSE["findings"])

    vulns, _ = transform_sca_vulns(raw_vulns)

    assert vulns[0]["reachability"] == "REACHABLE"
    assert vulns[1]["reachability"] == "UNREACHABLE"


def test_transform_sca_vulns_handles_null_reachability():
    # Semgrep only runs reachability analysis for supported ecosystems/rules, so
    # `reachability` comes back as null otherwise. transform_sca_vulns must not
    # crash on it (regression test for AttributeError on None.upper()).
    raw_vulns = copy.deepcopy(SCA_RESPONSE["findings"])
    raw_vulns[0]["reachability"] = None

    vulns, _ = transform_sca_vulns(raw_vulns)

    assert vulns[0]["reachability"] is None
