import ast
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cartography.intel.aws import label_migrations

REPOSITORY_ROOT = Path(__file__).parents[5]
LEGACY_LABEL_SCAN_ALLOWLIST = {
    Path("cartography/intel/aws/label_migrations.py"),
    Path("tests/integration/cartography/intel/aws/test_label_migrations.py"),
    Path("tests/unit/cartography/intel/aws/test_label_migrations.py"),
}
LABEL_ARGUMENT_CALLS = {
    "AddRelationship",
    "AddToSet",
    "AddValuesToSet",
    "PropertyEffect",
    "RelationshipEffect",
    "ScopeById",
    "SetProperty",
    "check_nodes",
    "check_rels",
}


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


def test_legacy_aws_labels_only_appear_in_migration_code():
    legacy_label_set = {
        migration.old_label for migration in label_migrations.AWS_LABEL_MIGRATIONS
    }
    legacy_labels = "|".join(re.escape(label) for label in legacy_label_set)
    legacy_label_pattern = re.compile(rf"(?::|%3A)(?:{legacy_labels})\b")
    violations = []

    for root_name in ("cartography", "docs", "tests", ".agents/skills"):
        for path in (REPOSITORY_ROOT / root_name).rglob("*"):
            if not path.is_file() or path.suffix not in {
                ".json",
                ".md",
                ".py",
                ".yaml",
                ".yml",
            }:
                continue
            relative_path = path.relative_to(REPOSITORY_ROOT)
            if relative_path in LEGACY_LABEL_SCAN_ALLOWLIST:
                continue

            for line_number, line in enumerate(path.read_text().splitlines(), start=1):
                if legacy_label_pattern.search(line):
                    violations.append(f"{relative_path}:{line_number}: {line.strip()}")

            if path.suffix != ".py":
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                function_name = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else (
                        node.func.attr if isinstance(node.func, ast.Attribute) else None
                    )
                )
                if function_name not in LABEL_ARGUMENT_CALLS:
                    continue
                for argument in (*node.args, *(kw.value for kw in node.keywords)):
                    if (
                        isinstance(argument, ast.Constant)
                        and isinstance(argument.value, str)
                        and argument.value in legacy_label_set
                    ):
                        violations.append(
                            f"{relative_path}:{node.lineno}: "
                            f"{function_name} uses {argument.value!r}"
                        )

    assert not violations, "Legacy AWS labels found outside migration code:\n  - " + (
        "\n  - ".join(violations)
    )


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
