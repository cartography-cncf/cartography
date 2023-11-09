import pytest

from cartography.sync import build_default_sync
from cartography.sync import build_sync
from cartography.sync import parse_and_validate_selected_modules
from cartography.sync import TOP_LEVEL_MODULES


def test_build_default_sync():
    sync = build_default_sync()
    # Use list because order matters
    assert [name for name in sync._stages.keys()] == list(TOP_LEVEL_MODULES.keys())


def test_build_sync():
    # Arrange
    selected_modules = 'aws, gcp, analysis'

    # Act
    sync = build_sync(selected_modules)

    # Assert
    assert [name for name in sync._stages.keys()] == selected_modules.split(', ')


def test_parse_and_validate_selected_modules():
    no_spaces = "aws,gcp,oci,analysis"
    assert parse_and_validate_selected_modules(no_spaces) == ['aws', 'gcp', 'oci', 'analysis']

    mismatch_spaces = 'gcp, oci,analysis'
    assert parse_and_validate_selected_modules(mismatch_spaces) == ['gcp', 'oci', 'analysis']

    sync_that_does_not_exist = 'gcp, thisdoesnotexist, aws'
    with pytest.raises(ValueError):
        parse_and_validate_selected_modules(sync_that_does_not_exist)

    absolute_garbage = '#@$@#RDFFHKjsdfkjsd,KDFJHW#@,'
    with pytest.raises(ValueError):
        parse_and_validate_selected_modules(absolute_garbage)
