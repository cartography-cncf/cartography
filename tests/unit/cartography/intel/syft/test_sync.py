import json
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.syft import sync_syft_from_report_reader
from tests.data.syft.syft_sample import SYFT_INVALID_NO_ARTIFACTS
from tests.data.trivy.trivy_sample import TRIVY_SAMPLE


@pytest.mark.parametrize(
    "invalid_report",
    [
        pytest.param(TRIVY_SAMPLE, id="trivy"),
        pytest.param(SYFT_INVALID_NO_ARTIFACTS, id="missing-artifacts"),
        pytest.param({"artifacts": None}, id="null-artifacts"),
        pytest.param({"artifacts": {}}, id="object-artifacts"),
        pytest.param({"artifacts": ""}, id="string-artifacts"),
        pytest.param({"artifacts": False}, id="boolean-artifacts"),
        pytest.param({"artifacts": 0}, id="number-artifacts"),
        pytest.param([], id="array-root"),
        pytest.param(None, id="null-root"),
        pytest.param("syft", id="string-root"),
        pytest.param(True, id="boolean-root"),
        pytest.param(1, id="number-root"),
    ],
)
def test_sync_rejects_invalid_report_before_ingestion_or_cleanup(
    tmp_path,
    invalid_report,
    caplog,
):
    # Arrange
    report_path = tmp_path / "invalid.json"
    report_path.write_text(json.dumps(invalid_report), encoding="utf-8")

    with (
        patch("cartography.intel.syft.sync_single_syft") as sync_single,
        patch("cartography.intel.syft.cleanup_syft") as cleanup,
    ):
        # Act
        sync_syft_from_report_reader(
            MagicMock(), LocalReportReader(str(tmp_path)), 123, {"UPDATE_TAG": 123}
        )

    # Assert
    sync_single.assert_not_called()
    cleanup.assert_not_called()
    assert str(report_path) in caplog.text
    assert "Invalid Syft report" in caplog.text
    assert "Skipping Syft cleanup" in caplog.text
