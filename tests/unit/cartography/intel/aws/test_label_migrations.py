from unittest.mock import MagicMock

import pytest

from cartography.intel.aws import label_migrations


def test_aws_label_migration_registry_is_complete_and_unique():
    old_labels = [
        migration.old_label for migration in label_migrations.AWS_LABEL_MIGRATIONS
    ]
    new_labels = [
        migration.new_label for migration in label_migrations.AWS_LABEL_MIGRATIONS
    ]

    assert len(old_labels) == 103
    assert len(old_labels) == len(set(old_labels))
    assert len(new_labels) == len(set(new_labels))
    assert all(new == f"AWS{old}" for old, new in zip(old_labels, new_labels))


@pytest.mark.parametrize(
    ("old_label", "new_label"),
    [
        ("Bad Label", "AWSBadLabel"),
        ("EC2Instance", "CloudEC2Instance"),
    ],
)
def test_aws_label_migration_rejects_invalid_mapping(old_label, new_label):
    with pytest.raises(ValueError):
        label_migrations.AWSLabelMigration(old_label, new_label)


def test_migrate_legacy_aws_labels_uses_one_scoped_write(mocker):
    neo4j_session = MagicMock()
    run_write_query = mocker.patch(
        "cartography.intel.aws.label_migrations.run_write_query"
    )

    label_migrations.migrate_legacy_aws_labels(
        neo4j_session,
        "123456789012",
    )

    run_write_query.assert_called_once()
    args, kwargs = run_write_query.call_args
    assert args[0] is neo4j_session
    assert "MATCH (:AWSAccount{id: $AWS_ID})-[:RESOURCE]->(n)" in args[1]
    assert "WHEN n:EC2Instance AND NOT n:AWSEC2Instance" in args[1]
    assert "SET n:AWSEC2Instance" in args[1]
    assert kwargs == {"AWS_ID": "123456789012"}


def test_migrate_legacy_public_ssm_parameter_label_uses_global_write(mocker):
    neo4j_session = MagicMock()
    run_write_query = mocker.patch(
        "cartography.intel.aws.label_migrations.run_write_query"
    )

    label_migrations.migrate_legacy_public_ssm_parameter_label(neo4j_session)

    run_write_query.assert_called_once()
    args, kwargs = run_write_query.call_args
    assert args[0] is neo4j_session
    assert "MATCH (parameter:PublicSSMParameter)" in args[1]
    assert "SET parameter:AWSPublicSSMParameter" in args[1]
    assert kwargs == {}
