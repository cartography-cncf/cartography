from unittest import mock
from unittest.mock import Mock
from unittest.mock import patch

import botocore
import pytest

import cartography.util
from cartography import util
from cartography.util import aws_handle_regions
from cartography.util import batch
from cartography.util import run_analysis_and_ensure_deps


def test_run_analysis_job_default_package(mocker):
    mocker.patch('cartography.util.GraphJob')
    read_text_mock = mocker.patch('cartography.util.read_text')
    util.run_analysis_job('test.json', mocker.Mock(), mocker.Mock())
    read_text_mock.assert_called_once_with('cartography.data.jobs.analysis', 'test.json')


def test_run_analysis_job_custom_package(mocker):
    mocker.patch('cartography.util.GraphJob')
    read_text_mock = mocker.patch('cartography.util.read_text')
    util.run_analysis_job('test.json', mocker.Mock(), mocker.Mock(), package='a.b.c')
    read_text_mock.assert_called_once_with('a.b.c', 'test.json')


def test_run_scoped_analysis_job_default_package(mocker):
    mocker.patch('cartography.util.GraphJob')
    read_text_mock = mocker.patch('cartography.util.read_text')
    util.run_scoped_analysis_job('test.json', mocker.Mock(), mocker.Mock())
    read_text_mock.assert_called_once_with('cartography.data.jobs.scoped_analysis', 'test.json')


@patch(
    'cartography.util.backoff', Mock(
        on_exception=lambda *args, **kwargs: lambda func: func,
    ),
)
def test_aws_handle_regions(mocker):
    # no exception
    @aws_handle_regions
    def happy_path(a, b):
        return a + b

    assert happy_path(1, 2) == 3

    # returns the default on_exception_return_value=[]
    @aws_handle_regions
    def raises_supported_client_error(a, b):
        e = botocore.exceptions.ClientError(
            {
                'Error': {
                    'Code': 'AccessDenied',
                    'Message': 'aws_handle_regions is not working',
                },
            },
            'FakeOperation',
        )
        raise e

    assert raises_supported_client_error(1, 2) == []

    # unhandled type of ClientError
    @aws_handle_regions
    def raises_unsupported_client_error(a, b):
        e = botocore.exceptions.ClientError(
            {
                'Error': {
                    'Code': '>9000',
                    'Message': 'aws_handle_regions is not working',
                },
            },
            'FakeOperation',
        )
        raise e

    with pytest.raises(botocore.exceptions.ClientError):
        raises_unsupported_client_error(1, 2)

    # other type of error besides ClientError
    @aws_handle_regions
    def raises_unsupported_error(a, b):
        return a / 0

    with pytest.raises(ZeroDivisionError):
        raises_unsupported_error(1, 2)


def test_batch(mocker):
    # Arrange
    x = range(12)
    expected = [
        [0, 1, 2, 3, 4],
        [5, 6, 7, 8, 9],
        [10, 11],
    ]
    # Act
    actual = batch(x, 5)
    # Assert
    assert actual == expected
    # Also check for empty input
    assert batch([], 3) == []


@mock.patch.object(cartography.util, 'run_analysis_job', return_value=None)
def test_run_analysis_and_ensure_deps(mock_run_analysis_job: mock.MagicMock):
    # Arrange
    neo4j_session = mock.MagicMock()
    common_job_parameters = mock.MagicMock()

    # This arg doesn't matter for this test
    requested_syncs = {
        'ec2:instance',
        'iam',
        'resourcegroupstaggingapi',
    }

    # Act
    ec2_asset_exposure_requirements = {
        'ec2:instance',
        'ec2:security_group',
        'ec2:load_balancer',
        'ec2:load_balancer_v2',
    }
    run_analysis_and_ensure_deps(
        'aws_ec2_asset_exposure.json',
        ec2_asset_exposure_requirements,
        requested_syncs,
        common_job_parameters,
        neo4j_session,
    )

    # Assert that the analysis job was not called because the requested sync reqs aren't met
    mock_run_analysis_job.assert_not_called()


@mock.patch.object(cartography.util, 'run_analysis_job', return_value=None)
def test_run_analysis_and_ensure_deps_no_requirements(mock_run_analysis_job: mock.MagicMock):
    # Arrange
    neo4j_session = mock.MagicMock()
    common_job_parameters = mock.MagicMock()

    # This arg doesn't matter for this test
    requested_syncs = {
        'ec2:instance',
        'iam',
        'resourcegroupstaggingapi',
    }

    # Act
    run_analysis_and_ensure_deps(
        'aws_foreign_accounts.json',
        {'iam'},
        requested_syncs,
        common_job_parameters,
        neo4j_session,
    )

    # Assert
    mock_run_analysis_job.assert_called_once_with(
        'aws_foreign_accounts.json',
        neo4j_session,
        common_job_parameters,
    )
