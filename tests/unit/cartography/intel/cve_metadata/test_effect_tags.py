from cartography.intel.cve_metadata.effect_tags import _VOCAB_ORDER
from cartography.intel.cve_metadata.effect_tags import derive_effect_tags
from cartography.intel.cve_metadata.effect_tags import unmapped_cwes


def test_unmapped_cwes_excludes_mapped_and_uninformative():
    weaknesses = ["CWE-78", "CWE-9999", "NVD-CWE-noinfo", "CWE-20", "CWE-1213"]
    # CWE-78 is mapped; noinfo/CWE-20 are uninformative; only the unknowns remain.
    assert unmapped_cwes(weaknesses) == ["CWE-9999", "CWE-1213"]


def test_single_cwe_lookup():
    tags, source = derive_effect_tags({"weaknesses": ["CWE-78"]})
    assert tags == ["execute-code"]
    assert source == "cwe"


def test_multi_cwe_union_deduplicated():
    # CWE-787 -> execute/tamper/deny, CWE-125 -> disclose/deny: union, deny dedup.
    tags, source = derive_effect_tags({"weaknesses": ["CWE-787", "CWE-125"]})
    assert source == "cwe"
    assert set(tags) == {"execute-code", "tamper-data", "deny-service", "disclose-data"}
    # Output is vocabulary-ordered and within the controlled set.
    assert tags == sorted(tags, key=_VOCAB_ORDER.index)
    assert set(tags) <= set(_VOCAB_ORDER)


def test_uninformative_cwe_falls_through_to_cvss():
    cve = {
        "weaknesses": ["NVD-CWE-noinfo", "CWE-20"],
        "confidentialityImpact": "HIGH",
    }
    tags, source = derive_effect_tags(cve)
    assert source == "cvss"
    assert tags == ["disclose-data"]


def test_cvss_cia_impact_tags():
    cve = {
        "weaknesses": [],
        "confidentialityImpact": "HIGH",
        "integrityImpact": "HIGH",
        "availabilityImpact": "HIGH",
    }
    tags, source = derive_effect_tags(cve)
    assert source == "cvss"
    assert set(tags) == {"disclose-data", "tamper-data", "deny-service"}


def test_cvss_straight_shot_execute_code():
    cve = {
        "weaknesses": [],
        "attackVector": "NETWORK",
        "privilegesRequired": "NONE",
        "userInteraction": "NONE",
        "integrityImpact": "HIGH",
    }
    tags, source = derive_effect_tags(cve)
    assert source == "cvss"
    assert "execute-code" in tags


def test_cvss_v2_complete_impacts_map():
    # NVD CVSS v2 uses COMPLETE/PARTIAL/NONE (not HIGH). COMPLETE counts as high.
    cve = {
        "weaknesses": [],
        "confidentialityImpact": "COMPLETE",
        "integrityImpact": "COMPLETE",
        "availabilityImpact": "COMPLETE",
    }
    tags, source = derive_effect_tags(cve)
    assert source == "cvss"
    assert set(tags) == {"disclose-data", "tamper-data", "deny-service"}


def test_cvss_v2_skips_straight_shot_cleanly():
    # v2 vectors lack privilegesRequired/userInteraction: straight-shot must not fire,
    # but C/I/A impacts (COMPLETE) still map without error.
    cve = {
        "weaknesses": [],
        "attackVector": "NETWORK",
        "integrityImpact": "COMPLETE",
    }
    tags, source = derive_effect_tags(cve)
    assert source == "cvss"
    assert tags == ["tamper-data"]
    assert "execute-code" not in tags


def test_no_cwe_no_cvss():
    tags, source = derive_effect_tags({"weaknesses": []})
    assert tags == []
    assert source == "none"


def test_cwe_precedence_over_cvss():
    # A usable CWE wins even when CVSS would also produce tags.
    cve = {"weaknesses": ["CWE-78"], "confidentialityImpact": "HIGH"}
    tags, source = derive_effect_tags(cve)
    assert source == "cwe"
    assert tags == ["execute-code"]
