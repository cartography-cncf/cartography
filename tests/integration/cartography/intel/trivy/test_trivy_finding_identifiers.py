from cartography.intel.trivy.scanner import sync_single_image
from tests.data.trivy.trivy_sample import TRIVY_MIXED_IDENTIFIERS_SAMPLE
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def _get_finding(neo4j_session, finding_id: str) -> dict:
    record = neo4j_session.run(
        """
        MATCH (f:TrivyImageFinding {id: $id})
        RETURN f.name AS name, f.cve_id AS cve_id, f.ghsa_id AS ghsa_id,
               f.vulnerability_ids AS vulnerability_ids,
               f.has_cve AS has_cve, f:CVE AS has_cve_label, f:Risk AS has_risk_label
        """,
        id=finding_id,
    ).single()
    assert record is not None, f"Expected a TrivyImageFinding with id {finding_id}"
    return dict(record)


def test_sync_mixed_identifiers_only_labels_cves(neo4j_session):
    """Trivy findings only carry cve_id and the :CVE label when they are CVE-backed."""
    # Act
    sync_single_image(
        neo4j_session,
        TRIVY_MIXED_IDENTIFIERS_SAMPLE,
        "mixed-ids.json",
        TEST_UPDATE_TAG,
    )

    # Assert - all three identifier schemes are ingested
    assert check_nodes(neo4j_session, "TrivyImageFinding", ["id", "name"]) == {
        ("TIF|CVE-2024-11111", "CVE-2024-11111"),
        ("TIF|GHSA-aaaa-bbbb-cccc", "GHSA-aaaa-bbbb-cccc"),
        ("TIF|TEMP-0000000-ABCDEF", "TEMP-0000000-ABCDEF"),
    }

    # A CVE-backed finding gets cve_id and the :CVE label
    cve = _get_finding(neo4j_session, "TIF|CVE-2024-11111")
    assert cve["cve_id"] == "CVE-2024-11111"
    assert cve["ghsa_id"] is None
    assert cve["has_cve"] == "true"
    assert cve["has_cve_label"] is True
    assert cve["has_risk_label"] is True
    # The vendor advisory id has no dedicated field, but is preserved in the full list
    assert cve["vulnerability_ids"] == ["CVE-2024-11111", "DSA-9999-1"]

    # A GitHub advisory keeps its identifier in ghsa_id and is not a :CVE
    ghsa = _get_finding(neo4j_session, "TIF|GHSA-aaaa-bbbb-cccc")
    assert ghsa["cve_id"] is None
    assert ghsa["ghsa_id"] == "GHSA-aaaa-bbbb-cccc"
    assert ghsa["has_cve"] == "false"
    assert ghsa["has_cve_label"] is False
    assert ghsa["has_risk_label"] is True

    # Any other scheme populates neither identifier field and is not a :CVE
    temp = _get_finding(neo4j_session, "TIF|TEMP-0000000-ABCDEF")
    assert temp["cve_id"] is None
    assert temp["ghsa_id"] is None
    assert temp["has_cve"] == "false"
    assert temp["has_cve_label"] is False
    assert temp["has_risk_label"] is True


def test_sync_removes_stale_cve_label_and_cve_id(neo4j_session):
    """A finding wrongly labelled :CVE by an older sync is corrected on the next sync."""
    # Arrange - simulate the pre-fix state: raw identifier copied into cve_id and
    # :CVE applied unconditionally.
    neo4j_session.run(
        """
        MERGE (f:TrivyImageFinding {id: 'TIF|GHSA-aaaa-bbbb-cccc'})
        SET f:Risk, f:CVE,
            f.name = 'GHSA-aaaa-bbbb-cccc',
            f.cve_id = 'GHSA-aaaa-bbbb-cccc',
            f.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    sync_single_image(
        neo4j_session,
        TRIVY_MIXED_IDENTIFIERS_SAMPLE,
        "mixed-ids.json",
        TEST_UPDATE_TAG,
    )

    # Assert
    ghsa = _get_finding(neo4j_session, "TIF|GHSA-aaaa-bbbb-cccc")
    assert ghsa["cve_id"] is None
    assert ghsa["ghsa_id"] == "GHSA-aaaa-bbbb-cccc"
    assert ghsa["has_cve_label"] is False
