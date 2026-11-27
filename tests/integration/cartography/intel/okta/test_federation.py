import cartography.intel.okta.federation
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_ORG_ID = "test-okta-org-id"
OTHER_ORG_ID = "other-okta-org-id"


def _setup_federation_graph(neo4j_session) -> None:
    neo4j_session.run(
        """
        MERGE (org:OktaOrganization {id: $ORG_ID})
        MERGE (other_org:OktaOrganization {id: $OTHER_ORG_ID})

        MERGE (slack_app:OktaApplication {id: "app-slack-grid"})
        SET slack_app.name = "slack",
            slack_app.sign_on_mode = "SAML_2_0",
            slack_app.settings_app_domain = "acme-grid.enterprise"
        MERGE (org)-[:RESOURCE]->(slack_app)

        MERGE (gh_app:OktaApplication {id: "app-github"})
        SET gh_app.name = "githubcloud",
            gh_app.sign_on_mode = "SAML_2_0",
            gh_app.settings_app_github_org = "Acme-Org"
        MERGE (org)-[:RESOURCE]->(gh_app)

        MERGE (google_app:OktaApplication {id: "app-google"})
        SET google_app.name = "google",
            google_app.sign_on_mode = "BROWSER_PLUGIN",
            google_app.settings_app_domain = "acme.example.test"
        MERGE (org)-[:RESOURCE]->(google_app)

        MERGE (sf_app:OktaApplication {id: "app-salesforce"})
        SET sf_app.name = "salesforce",
            sf_app.sign_on_mode = "SAML_2_0",
            sf_app.settings_app_login_url = "https://acme.my.salesforce.com",
            sf_app.settings_app_instance_type = "PRODUCTION",
            sf_app.settings_app_custom_domain = "acme"
        MERGE (org)-[:RESOURCE]->(sf_app)

        MERGE (other_app:OktaApplication {id: "app-other-org-google"})
        SET other_app.name = "google",
            other_app.sign_on_mode = "SAML_2_0",
            other_app.settings_app_domain = "other.example.test"
        MERGE (other_org)-[:RESOURCE]->(other_app)

        MERGE (t1:SlackTeam {id: "T_GRID_1"})
        SET t1.domain = "acme-eng",
            t1.enterprise_domain = "acme-grid"
        MERGE (t2:SlackTeam {id: "T_GRID_2"})
        SET t2.domain = "acme-sec",
            t2.enterprise_domain = "acme-grid"

        MERGE (gh:GitHubOrganization {id: "https://github.com/acme-org"})
        SET gh.username = "acme-org"

        MERGE (gw1:GoogleWorkspaceTenant {id: "C_ACME"})
        SET gw1.domain = "acme.example.test"
        MERGE (gw2:GoogleWorkspaceTenant {id: "C_OTHER"})
        SET gw2.domain = "other.example.test"

        MERGE (sf:SalesforceOrganization {id: "00D_ACME"})
        SET sf.instance_url = "https://acme.my.salesforce.com",
            sf.is_sandbox = false
        """,
        ORG_ID=TEST_ORG_ID,
        OTHER_ORG_ID=OTHER_ORG_ID,
    )


def test_sync_okta_federation_links_tenants_and_scopes_to_org(neo4j_session) -> None:
    _setup_federation_graph(neo4j_session)

    cartography.intel.okta.federation.sync_okta_federation(
        neo4j_session,
        TEST_UPDATE_TAG,
        TEST_ORG_ID,
    )

    assert check_rels(
        neo4j_session,
        "OktaApplication",
        "id",
        "SlackTeam",
        "id",
        "FEDERATES_TO",
        rel_direction_right=True,
    ) == {
        ("app-slack-grid", "T_GRID_1"),
        ("app-slack-grid", "T_GRID_2"),
    }

    assert check_rels(
        neo4j_session,
        "OktaApplication",
        "id",
        "GitHubOrganization",
        "id",
        "FEDERATES_TO",
        rel_direction_right=True,
    ) == {
        ("app-github", "https://github.com/acme-org"),
    }

    # Only the current OktaOrganization's Google app is linked; other_org's is not.
    assert check_rels(
        neo4j_session,
        "OktaApplication",
        "id",
        "GoogleWorkspaceTenant",
        "id",
        "FEDERATES_TO",
        rel_direction_right=True,
    ) == {
        ("app-google", "C_ACME"),
    }

    assert check_rels(
        neo4j_session,
        "OktaApplication",
        "id",
        "SalesforceOrganization",
        "id",
        "FEDERATES_TO",
        rel_direction_right=True,
    ) == {
        ("app-salesforce", "00D_ACME"),
    }

    rel_props = neo4j_session.run(
        """
        MATCH (app:OktaApplication)-[r:FEDERATES_TO]->(target)
        RETURN app.id AS app_id,
               target.id AS target_id,
               r.sign_on_mode AS sign_on_mode,
               r.matched_on AS matched_on,
               r.lastupdated AS lastupdated,
               r._sub_resource_label AS sub_resource_label,
               r._sub_resource_id AS sub_resource_id
        """,
    ).data()
    assert {
        (
            row["app_id"],
            row["target_id"],
            row["sign_on_mode"],
            row["matched_on"],
            row["lastupdated"],
            row["sub_resource_label"],
            row["sub_resource_id"],
        )
        for row in rel_props
    } == {
        (
            "app-slack-grid",
            "T_GRID_1",
            "SAML_2_0",
            "settings.app.domain",
            TEST_UPDATE_TAG,
            "OktaOrganization",
            TEST_ORG_ID,
        ),
        (
            "app-slack-grid",
            "T_GRID_2",
            "SAML_2_0",
            "settings.app.domain",
            TEST_UPDATE_TAG,
            "OktaOrganization",
            TEST_ORG_ID,
        ),
        (
            "app-github",
            "https://github.com/acme-org",
            "SAML_2_0",
            "settings.app.githubOrg",
            TEST_UPDATE_TAG,
            "OktaOrganization",
            TEST_ORG_ID,
        ),
        (
            "app-google",
            "C_ACME",
            "BROWSER_PLUGIN",
            "settings.app.domain",
            TEST_UPDATE_TAG,
            "OktaOrganization",
            TEST_ORG_ID,
        ),
        (
            "app-salesforce",
            "00D_ACME",
            "SAML_2_0",
            "settings.app.loginUrl",
            TEST_UPDATE_TAG,
            "OktaOrganization",
            TEST_ORG_ID,
        ),
    }


def test_sync_okta_federation_removes_stale_links(neo4j_session) -> None:
    _setup_federation_graph(neo4j_session)
    cartography.intel.okta.federation.sync_okta_federation(
        neo4j_session,
        TEST_UPDATE_TAG,
        TEST_ORG_ID,
    )

    # Change the Google app's domain to another tenant and re-sync with a newer update tag.
    neo4j_session.run(
        """
        MATCH (app:OktaApplication {id: "app-google"})
        SET app.settings_app_domain = "other.example.test"
        """,
    )
    cartography.intel.okta.federation.sync_okta_federation(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        TEST_ORG_ID,
    )

    assert check_rels(
        neo4j_session,
        "OktaApplication",
        "id",
        "GoogleWorkspaceTenant",
        "id",
        "FEDERATES_TO",
        rel_direction_right=True,
    ) == {
        ("app-google", "C_OTHER"),
    }


def test_sync_okta_federation_cleanup_keeps_other_orgs_links(neo4j_session) -> None:
    # Arrange: the other Okta org syncs first and links its Google app
    _setup_federation_graph(neo4j_session)
    cartography.intel.okta.federation.sync_okta_federation(
        neo4j_session,
        TEST_UPDATE_TAG,
        OTHER_ORG_ID,
    )

    # Act: this org syncs later with a newer update tag, which runs its cleanup
    cartography.intel.okta.federation.sync_okta_federation(
        neo4j_session,
        TEST_UPDATE_TAG + 1,
        TEST_ORG_ID,
    )

    # Assert: the other org's older link survives this org's cleanup
    assert ("app-other-org-google", "C_OTHER") in check_rels(
        neo4j_session,
        "OktaApplication",
        "id",
        "GoogleWorkspaceTenant",
        "id",
        "FEDERATES_TO",
        rel_direction_right=True,
    )
