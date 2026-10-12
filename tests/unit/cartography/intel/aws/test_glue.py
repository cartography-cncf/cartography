from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from cartography.intel.aws import glue


def _client_error(code: str, status: int) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": ""},
            "ResponseMetadata": {"HTTPStatusCode": status},
        },
        "GetJobs",
    )


def test_get_glue_jobs_raises_transient_region_failure_on_internal_failure():
    boto3_session = MagicMock()
    paginator = boto3_session.client.return_value.get_paginator.return_value
    paginator.paginate.side_effect = _client_error("InternalFailure", 500)

    with pytest.raises(glue.GlueTransientRegionFailure):
        glue.get_glue_jobs(boto3_session, "me-central-1")


def test_sync_skips_failed_region_and_cleanup_after_transient_failure(mocker):
    def get_jobs(boto3_session, region):
        if region == "me-central-1":
            raise glue.GlueTransientRegionFailure("temporary failure")
        return []

    mocker.patch.object(glue, "get_glue_connections", return_value=[])
    mocker.patch.object(glue, "get_glue_jobs", side_effect=get_jobs)
    load_jobs = mocker.patch.object(glue, "load_glue_jobs")
    cleanup = mocker.patch.object(glue, "cleanup")

    glue.sync(
        MagicMock(),
        MagicMock(),
        ["us-east-1", "me-central-1", "eu-west-1"],
        "123456789012",
        1,
        {},
    )

    assert [call.args[2] for call in load_jobs.call_args_list] == [
        "us-east-1",
        "eu-west-1",
    ]
    cleanup.assert_not_called()


def test_sync_cleans_up_when_every_region_succeeds(mocker):
    mocker.patch.object(glue, "get_glue_connections", return_value=[])
    mocker.patch.object(glue, "get_glue_jobs", return_value=[])
    mocker.patch.object(glue, "load_glue_connections")
    mocker.patch.object(glue, "load_glue_jobs")
    cleanup = mocker.patch.object(glue, "cleanup")

    glue.sync(MagicMock(), MagicMock(), ["us-east-1"], "123456789012", 1, {})

    cleanup.assert_called_once()
