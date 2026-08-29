from unittest.mock import MagicMock

from cartography.intel.crowdstrike import label_migrations as crowdstrike_migrations
from cartography.intel.github import label_migrations as github_migrations
from cartography.intel.semgrep import label_migrations as semgrep_migrations
from cartography.intel.spacelift import label_migrations as spacelift_migrations


def _query_and_kwargs(run_write_query):
    run_write_query.assert_called_once()
    args, kwargs = run_write_query.call_args
    return args[1], kwargs


def test_github_label_migration_is_scoped(mocker):
    run_write_query = mocker.patch.object(github_migrations, "run_write_query")

    github_migrations.migrate_dependency_graph_manifest_label(
        MagicMock(),
        "https://github.com/acme",
    )

    query, kwargs = _query_and_kwargs(run_write_query)
    assert "org:GitHubOrganization{id: $owner_org_id}" in query
    assert "manifest:DependencyGraphManifest" in query
    assert "SET manifest:GitHubDependencyGraphManifest" in query
    assert kwargs == {"owner_org_id": "https://github.com/acme"}


def test_semgrep_label_migration_is_scoped(mocker):
    run_write_query = mocker.patch.object(semgrep_migrations, "run_write_query")

    semgrep_migrations.migrate_dependency_labels(MagicMock(), "deployment-1")

    query, kwargs = _query_and_kwargs(run_write_query)
    assert "SemgrepDeployment{id: $DEPLOYMENT_ID}" in query
    assert "SET dependency:SemgrepGoLibrary" in query
    assert "SET dependency:SemgrepNpmLibrary" in query
    assert kwargs == {"DEPLOYMENT_ID": "deployment-1"}


def test_crowdstrike_label_migration_is_additive(mocker):
    run_write_query = mocker.patch.object(crowdstrike_migrations, "run_write_query")

    crowdstrike_migrations.migrate_spotlight_vulnerability_label(MagicMock())

    query, kwargs = _query_and_kwargs(run_write_query)
    assert "vulnerability:SpotlightVulnerability" in query
    assert "SET vulnerability:CrowdstrikeSpotlightVulnerability" in query
    assert "REMOVE" not in query
    assert kwargs == {}


def test_spacelift_label_migration_is_scoped(mocker):
    run_write_query = mocker.patch.object(spacelift_migrations, "run_write_query")

    spacelift_migrations.migrate_cloudtrail_event_label(MagicMock(), "acme")

    query, kwargs = _query_and_kwargs(run_write_query)
    assert "SpaceliftAccount{id: $spacelift_account_id}" in query
    assert "event:CloudTrailSpaceliftEvent" in query
    assert "SET event:SpaceliftCloudTrailEvent" in query
    assert kwargs == {"spacelift_account_id": "acme"}
