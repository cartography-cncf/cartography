import pytest

from cartography.config import Config
from cartography.sync import build_default_sync
from cartography.sync import build_sync
from cartography.sync import parse_and_validate_selected_modules
from cartography.sync import run_with_config
from cartography.sync import Sync
from cartography.sync import TOP_LEVEL_MODULES


def test_available_modules_import():
    # Check if all available modules are defined in the TOP_LEVEL_MODULES list
    assert sorted(TOP_LEVEL_MODULES.keys()) == sorted(Sync.list_intel_modules().keys())


def test_build_default_sync():
    sync = build_default_sync()
    # Use list because order matters
    assert [name for name in sync._stages.keys()] == list(TOP_LEVEL_MODULES.keys())


def test_build_sync():
    # Arrange
    selected_modules = "aws, gcp, analysis"

    # Act
    sync = build_sync(selected_modules)

    # Assert
    assert [name for name in sync._stages.keys()] == selected_modules.split(", ")


def test_parse_and_validate_selected_modules():
    no_spaces = "aws,gcp,oci,analysis"
    assert parse_and_validate_selected_modules(no_spaces) == [
        "aws",
        "gcp",
        "oci",
        "analysis",
    ]

    mismatch_spaces = "gcp, oci,analysis"
    assert parse_and_validate_selected_modules(mismatch_spaces) == [
        "gcp",
        "oci",
        "analysis",
    ]

    sync_that_does_not_exist = "gcp, thisdoesnotexist, aws"
    with pytest.raises(ValueError):
        parse_and_validate_selected_modules(sync_that_does_not_exist)

    absolute_garbage = "#@$@#RDFFHKjsdfkjsd,KDFJHW#@,"
    with pytest.raises(ValueError):
        parse_and_validate_selected_modules(absolute_garbage)


def test_run_with_config_forwards_optional_driver_kwargs(mocker):
    sync = mocker.Mock()
    driver = object()
    driver_mock = mocker.patch(
        "cartography.sync.GraphDatabase.driver", return_value=driver
    )
    mocker.patch("cartography.sync.time.time", return_value=123)

    config = Config(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        neo4j_max_connection_lifetime=300,
        neo4j_liveness_check_timeout=30,
        neo4j_connection_timeout=15.0,
        neo4j_keep_alive=True,
        neo4j_max_transaction_retry_time=30.0,
        neo4j_max_connection_pool_size=64,
        neo4j_connection_acquisition_timeout=60.0,
    )

    run_with_config(sync, config)

    driver_mock.assert_called_once_with(
        "bolt://localhost:7687",
        auth=("neo4j", "password"),
        max_connection_lifetime=300,
        liveness_check_timeout=30,
        connection_timeout=15.0,
        keep_alive=True,
        max_transaction_retry_time=30.0,
        max_connection_pool_size=64,
        connection_acquisition_timeout=60.0,
    )
    sync.run.assert_called_once_with(driver, config)
    assert config.update_tag == 123


def test_run_with_config_omits_unset_optional_driver_kwargs(mocker):
    sync = mocker.Mock()
    driver_mock = mocker.patch(
        "cartography.sync.GraphDatabase.driver", return_value=object()
    )
    mocker.patch("cartography.sync.time.time", return_value=123)

    config = Config(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
    )

    run_with_config(sync, config)

    driver_mock.assert_called_once_with(
        "bolt://localhost:7687",
        auth=("neo4j", "password"),
    )


def test_config_preserves_existing_positional_arguments():
    config = Config(
        "bolt://localhost:7687",
        "neo4j",
        "password",
        300,
        30,
        "neo4j-db",
        "aws,analysis",
        456,
    )

    assert config.neo4j_database == "neo4j-db"
    assert config.selected_modules == "aws,analysis"
    assert config.update_tag == 456
