import logging
import pathlib
import types
import pytest
from unittest import mock

import cartography.intel.analysis as analysis_mod

class DummySession:
    pass

class DummyConfig:
    def __init__(self, analysis_job_directory, update_tag=123):
        self.analysis_job_directory = analysis_job_directory
        self.update_tag = update_tag


def test_aws_s3acl_analysis_skipped_when_aws_id_missing(tmp_path, caplog):
    # Create a dummy aws_s3acl_analysis.json file in a temp directory
    job_file = tmp_path / "aws_s3acl_analysis.json"
    job_file.write_text("{}")
    # Create a dummy config with no AWS_ID
    config = DummyConfig(str(tmp_path))
    caplog.set_level(logging.WARNING)
    # Patch GraphJob.run_from_json_file to ensure it is not called for the skipped job
    with mock.patch.object(analysis_mod.GraphJob, 'run_from_json_file') as mock_run:
        analysis_mod.run(DummySession(), config)
        # Should not call run_from_json_file for the skipped job
        mock_run.assert_not_called()
    # Check the warning was logged
    assert any(
        "Skipping aws_s3acl_analysis.json because AWS_ID is missing" in r.message for r in caplog.records
    )