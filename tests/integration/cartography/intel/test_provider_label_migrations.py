from cartography.intel.crowdstrike.label_migrations import (
    migrate_spotlight_vulnerability_label,
)
from cartography.intel.github.label_migrations import (
    migrate_dependency_graph_manifest_label,
)
from cartography.intel.semgrep.label_migrations import migrate_dependency_labels
from cartography.intel.spacelift.label_migrations import migrate_cloudtrail_event_label


def test_provider_label_migrations_are_additive_scoped_and_idempotent(
    neo4j_session,
):
    original_ids = neo4j_session.run(
        """
        CREATE (github_org:GitHubOrganization{id: 'github-org'})
        CREATE (other_github_org:GitHubOrganization{id: 'other-github-org'})
        CREATE (repo:GitHubRepository{id: 'github-repo'})
        CREATE (manifest:DependencyGraphManifest{id: 'manifest'})
        CREATE (other_manifest:DependencyGraphManifest{id: 'other-manifest'})
        CREATE (repo)-[:OWNER]->(github_org)
        CREATE (repo)-[:HAS_MANIFEST]->(manifest)
        CREATE (other_github_org)-[:RESOURCE]->(other_manifest)

        CREATE (semgrep:SemgrepDeployment{id: 'semgrep'})
        CREATE (other_semgrep:SemgrepDeployment{id: 'other-semgrep'})
        CREATE (go:GoLibrary{id: 'go'})
        CREATE (npm:NpmLibrary{id: 'npm'})
        CREATE (other_go:GoLibrary{id: 'other-go'})
        CREATE (semgrep)-[:RESOURCE]->(go)
        CREATE (semgrep)-[:RESOURCE]->(npm)
        CREATE (other_semgrep)-[:RESOURCE]->(other_go)

        CREATE (host:CrowdstrikeHost{id: 'host'})
        CREATE (vulnerability:SpotlightVulnerability{id: 'vulnerability'})
        CREATE (host)-[:HAS_VULNERABILITY]->(vulnerability)

        CREATE (spacelift:SpaceliftAccount{id: 'spacelift'})
        CREATE (other_spacelift:SpaceliftAccount{id: 'other-spacelift'})
        CREATE (event:CloudTrailSpaceliftEvent{id: 'event'})
        CREATE (other_event:CloudTrailSpaceliftEvent{id: 'other-event'})
        CREATE (spacelift)-[:RESOURCE]->(event)
        CREATE (other_spacelift)-[:RESOURCE]->(other_event)

        RETURN elementId(manifest) AS manifest,
               elementId(go) AS go,
               elementId(npm) AS npm,
               elementId(vulnerability) AS vulnerability,
               elementId(event) AS event
        """
    ).single()

    for _ in range(2):
        migrate_dependency_graph_manifest_label(neo4j_session, "github-org")
        migrate_dependency_labels(neo4j_session, "semgrep")
        migrate_spotlight_vulnerability_label(neo4j_session)
        migrate_cloudtrail_event_label(neo4j_session, "spacelift")

    migrated = neo4j_session.run(
        """
        MATCH (manifest{id: 'manifest'})
        MATCH (go{id: 'go'})
        MATCH (npm{id: 'npm'})
        MATCH (vulnerability{id: 'vulnerability'})
        MATCH (event{id: 'event'})
        RETURN elementId(manifest) AS manifest_id,
               labels(manifest) AS manifest_labels,
               elementId(go) AS go_id,
               labels(go) AS go_labels,
               elementId(npm) AS npm_id,
               labels(npm) AS npm_labels,
               elementId(vulnerability) AS vulnerability_id,
               labels(vulnerability) AS vulnerability_labels,
               elementId(event) AS event_id,
               labels(event) AS event_labels,
               count {
                   (:CrowdstrikeHost{id: 'host'})
                   -[:HAS_VULNERABILITY]->(vulnerability)
               } AS vulnerability_relationships
        """
    ).single()

    assert migrated["manifest_id"] == original_ids["manifest"]
    assert {"DependencyGraphManifest", "GitHubDependencyGraphManifest"} <= set(
        migrated["manifest_labels"]
    )
    assert migrated["go_id"] == original_ids["go"]
    assert {"GoLibrary", "SemgrepGoLibrary"} <= set(migrated["go_labels"])
    assert migrated["npm_id"] == original_ids["npm"]
    assert {"NpmLibrary", "SemgrepNpmLibrary"} <= set(migrated["npm_labels"])
    assert migrated["vulnerability_id"] == original_ids["vulnerability"]
    assert {
        "SpotlightVulnerability",
        "CrowdstrikeSpotlightVulnerability",
    } <= set(migrated["vulnerability_labels"])
    assert migrated["event_id"] == original_ids["event"]
    assert {"CloudTrailSpaceliftEvent", "SpaceliftCloudTrailEvent"} <= set(
        migrated["event_labels"]
    )
    assert migrated["vulnerability_relationships"] == 1

    untouched = neo4j_session.run(
        """
        MATCH (other_manifest:DependencyGraphManifest{id: 'other-manifest'})
        MATCH (other_go:GoLibrary{id: 'other-go'})
        MATCH (other_event:CloudTrailSpaceliftEvent{id: 'other-event'})
        RETURN other_manifest:GitHubDependencyGraphManifest AS github,
               other_go:SemgrepGoLibrary AS semgrep,
               other_event:SpaceliftCloudTrailEvent AS spacelift
        """
    ).single()
    assert untouched["github"] is False
    assert untouched["semgrep"] is False
    assert untouched["spacelift"] is False
