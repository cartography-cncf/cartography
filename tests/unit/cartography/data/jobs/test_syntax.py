import json
import sys

import pytest
if sys.version_info >= (3, 7):
    from importlib.resources import contents, read_text
else:
    from importlib_resources import contents, read_text


def test_analysis_jobs_are_valid_json():
    for job_name in contents('cartography.data.jobs.analysis'):
        if not job_name.endswith('.json'):
            continue
        blob = read_text('cartography.data.jobs.analysis', job_name)
        try:
            json.loads(blob)
        except Exception as e:
            pytest.fail(f"json.loads failed for analysis job '{job_name}' with exception: {e}")


def test_cleanup_jobs_are_valid_json():
    for job_name in contents('cartography.data.jobs.cleanup'):
        if not job_name.endswith('json'):
            continue
        blob = read_text('cartography.data.jobs.cleanup', job_name)
        try:
            json.loads(blob)
        except Exception as e:
            pytest.fail(f"json.loads failed for cleanup job '{job_name}' with exception: {e}")


def test_scoped_analysis_jobs_are_valid_json():
    for job_name in contents('cartography.data.jobs.scoped_analysis'):
        if not job_name.endswith('.json'):
            continue
        blob = read_text('cartography.data.jobs.scoped_analysis', job_name)
        try:
            json.loads(blob)
        except Exception as e:
            pytest.fail(f"json.loads failed for scoped analysis job '{job_name}' with exception: {e}")
