from typing import Any

from cartography.intel.okta.federation import resolve_okta_federation_links


def test_slack_enterprise_domain_links_to_all_grid_teams() -> None:
    okta_apps = [
        {
            "id": "app-slack-grid",
            "name": "slack",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "Example-Grid.enterprise",
            "settings_app_github_org": None,
        },
    ]
    slack_teams = [
        {"id": "T1", "domain": "ws-one", "enterprise_domain": "example-grid"},
        {"id": "T2", "domain": "ws-two", "enterprise_domain": "example-grid"},
        {"id": "T3", "domain": "ws-other", "enterprise_domain": "other-grid"},
    ]

    result = resolve_okta_federation_links(okta_apps, slack_teams, [], [])

    assert result["SlackTeam"] == [
        {
            "okta_app_id": "app-slack-grid",
            "target_id": "T1",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.domain",
        },
        {
            "okta_app_id": "app-slack-grid",
            "target_id": "T2",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.domain",
        },
    ]
    assert result["GitHubOrganization"] == []
    assert result["GoogleWorkspaceTenant"] == []
    assert result["SalesforceOrganization"] == []


def test_slack_plain_domain_links_only_when_unique() -> None:
    okta_apps = [
        {
            "id": "app-slack-unique",
            "name": "slack",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "unique-ws",
            "settings_app_github_org": None,
        },
        {
            "id": "app-slack-ambiguous",
            "name": "slack",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "shared-ws",
            "settings_app_github_org": None,
        },
    ]
    slack_teams = [
        {"id": "T1", "domain": "UNIQUE-WS", "enterprise_domain": None},
        {"id": "T2", "domain": "shared-ws", "enterprise_domain": None},
        {"id": "T3", "domain": "shared-ws", "enterprise_domain": None},
    ]

    result = resolve_okta_federation_links(okta_apps, slack_teams, [], [])

    assert result["SlackTeam"] == [
        {
            "okta_app_id": "app-slack-unique",
            "target_id": "T1",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.domain",
        },
    ]


def test_github_login_match_is_case_insensitive() -> None:
    okta_apps = [
        {
            "id": "app-gh",
            "name": "githubcloud",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": None,
            "settings_app_github_org": "Example-Org",
        },
    ]
    github_orgs = [
        {"id": "https://github.com/example-org", "username": "example-org"},
    ]

    result = resolve_okta_federation_links(okta_apps, [], github_orgs, [])

    assert result["GitHubOrganization"] == [
        {
            "okta_app_id": "app-gh",
            "target_id": "https://github.com/example-org",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.githubOrg",
        },
    ]


def test_github_and_google_require_exactly_one_candidate() -> None:
    okta_apps = [
        {
            "id": "app-gh-none",
            "name": "githubcloud",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": None,
            "settings_app_github_org": "missing-org",
        },
        {
            "id": "app-gh-two",
            "name": "githubcloud",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": None,
            "settings_app_github_org": "dup-org",
        },
        {
            "id": "app-google-none",
            "name": "google",
            "sign_on_mode": "BROWSER_PLUGIN",
            "settings_app_domain": "missing.example.test",
            "settings_app_github_org": None,
        },
        {
            "id": "app-google-two",
            "name": "google",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "dup.example.test",
            "settings_app_github_org": None,
        },
        {
            "id": "app-google-one",
            "name": "google",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "One.Example.Test",
            "settings_app_github_org": None,
        },
    ]
    github_orgs = [
        {"id": "https://github.com/dup-1", "username": "dup-org"},
        {"id": "https://github.com/dup-2", "username": "DUP-ORG"},
    ]
    google_tenants = [
        {"id": "C0001", "domain": "dup.example.test"},
        {"id": "C0002", "domain": "DUP.EXAMPLE.TEST"},
        {"id": "C0003", "domain": "one.example.test"},
    ]

    result = resolve_okta_federation_links(okta_apps, [], github_orgs, google_tenants)

    assert result["GitHubOrganization"] == []
    assert result["GoogleWorkspaceTenant"] == [
        {
            "okta_app_id": "app-google-one",
            "target_id": "C0003",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.domain",
        },
    ]


def test_unknown_app_and_missing_or_empty_values_produce_no_rows() -> None:
    okta_apps: list[dict[str, Any]] = [
        {
            "id": "app-unknown",
            "name": "workday",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "example.test",
            "settings_app_github_org": "example-org",
        },
        {
            "id": "app-slack-none",
            "name": "slack",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": None,
            "settings_app_github_org": None,
        },
        {
            "id": "app-slack-empty",
            "name": "slack",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "",
            "settings_app_github_org": None,
        },
        {
            "id": "app-gh-empty",
            "name": "githubcloud",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": None,
            "settings_app_github_org": "",
        },
        {
            "id": "app-google-none",
            "name": "google",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": None,
            "settings_app_github_org": None,
        },
        {
            "id": "app-sf-missing",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": None,
            "settings_app_instance_type": None,
            "settings_app_custom_domain": "",
        },
    ]
    slack_teams = [{"id": "T1", "domain": "example.test", "enterprise_domain": None}]
    github_orgs = [{"id": "https://github.com/example-org", "username": "example-org"}]
    google_tenants = [{"id": "C0001", "domain": "example.test"}]
    salesforce_orgs = [
        {
            "id": "00D000000000001EAA",
            "instance_url": "https://example.my.salesforce.com",
            "is_sandbox": False,
        },
    ]

    result = resolve_okta_federation_links(
        okta_apps, slack_teams, github_orgs, google_tenants, salesforce_orgs
    )

    assert result == {
        "SlackTeam": [],
        "GitHubOrganization": [],
        "GoogleWorkspaceTenant": [],
        "SalesforceOrganization": [],
    }


def test_salesforce_login_url_and_custom_domain_matching() -> None:
    okta_apps: list[dict[str, Any]] = [
        {
            "id": "app-sf-login-url",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://Example.My.Salesforce.com/login",
            "settings_app_instance_type": "PRODUCTION",
            "settings_app_custom_domain": "other",
        },
        {
            "id": "app-sf-custom-domain",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://login.salesforce.com",
            "settings_app_instance_type": None,
            "settings_app_custom_domain": "Acme-Sandbox",
        },
    ]
    salesforce_orgs = [
        {
            "id": "00D_PROD",
            "instance_url": "https://example.my.salesforce.com",
            "is_sandbox": False,
        },
        {
            "id": "00D_SANDBOX",
            "instance_url": "https://acme-sandbox.my.salesforce.com",
            "is_sandbox": True,
        },
    ]

    result = resolve_okta_federation_links(okta_apps, [], [], [], salesforce_orgs)

    assert result["SalesforceOrganization"] == [
        {
            "okta_app_id": "app-sf-login-url",
            "target_id": "00D_PROD",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.loginUrl",
        },
        {
            "okta_app_id": "app-sf-custom-domain",
            "target_id": "00D_SANDBOX",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.customDomain",
        },
    ]


def test_salesforce_instance_type_mismatch_and_duplicate_hosts_block_link() -> None:
    okta_apps = [
        {
            "id": "app-sf-prod-vs-sandbox",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://sandbox.my.salesforce.com",
            "settings_app_instance_type": "PRODUCTION",
            "settings_app_custom_domain": None,
        },
        {
            "id": "app-sf-sandbox-vs-prod",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://prod.my.salesforce.com",
            "settings_app_instance_type": "SANDBOX",
            "settings_app_custom_domain": None,
        },
        {
            "id": "app-sf-dup-host",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://dup.my.salesforce.com",
            "settings_app_instance_type": "OTHER",
            "settings_app_custom_domain": None,
        },
    ]
    salesforce_orgs = [
        {
            "id": "00D_SANDBOX",
            "instance_url": "https://sandbox.my.salesforce.com",
            "is_sandbox": True,
        },
        {
            "id": "00D_PROD",
            "instance_url": "https://prod.my.salesforce.com",
            "is_sandbox": False,
        },
        {
            "id": "00D_DUP_1",
            "instance_url": "https://dup.my.salesforce.com",
            "is_sandbox": False,
        },
        {
            "id": "00D_DUP_2",
            "instance_url": "https://DUP.my.salesforce.com",
            "is_sandbox": False,
        },
    ]

    result = resolve_okta_federation_links(okta_apps, [], [], [], salesforce_orgs)

    assert result["SalesforceOrganization"] == []


def test_inactive_okta_app_is_not_linked() -> None:
    okta_apps = [
        {
            "id": "app-google-inactive",
            "name": "google",
            "status": "INACTIVE",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "example.com",
        },
        {
            "id": "app-google-active",
            "name": "google",
            "status": "ACTIVE",
            "sign_on_mode": "SAML_2_0",
            "settings_app_domain": "example.com",
        },
    ]
    google_tenants = [{"id": "C0example", "domain": "example.com"}]

    result = resolve_okta_federation_links(okta_apps, [], [], google_tenants)

    assert [row["okta_app_id"] for row in result["GoogleWorkspaceTenant"]] == [
        "app-google-active"
    ]


def test_malformed_salesforce_login_url_does_not_raise() -> None:
    okta_apps = [
        {
            "id": "app-sf-bad-url",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://[bad-host/login",
            "settings_app_instance_type": "PRODUCTION",
            "settings_app_custom_domain": "example",
        },
    ]
    salesforce_orgs = [
        {
            "id": "00D_PROD",
            "instance_url": "https://example.my.salesforce.com",
            "is_sandbox": False,
        },
        {
            "id": "00D_BAD",
            "instance_url": "https://[broken",
            "is_sandbox": False,
        },
    ]

    result = resolve_okta_federation_links(okta_apps, [], [], [], salesforce_orgs)

    assert [row["target_id"] for row in result["SalesforceOrganization"]] == [
        "00D_PROD"
    ]


def test_salesforce_sandbox_custom_domain_matches_sandbox_host() -> None:
    okta_apps = [
        {
            "id": "app-sf-sandbox",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://test.salesforce.com",
            "settings_app_instance_type": "SANDBOX",
            "settings_app_custom_domain": "Acme",
        },
        {
            "id": "app-sf-sandbox-ambiguous",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://test.salesforce.com",
            "settings_app_instance_type": "SANDBOX",
            "settings_app_custom_domain": "multi",
        },
    ]
    salesforce_orgs = [
        {
            "id": "00D_PROD",
            "instance_url": "https://acme.my.salesforce.com",
            "is_sandbox": False,
        },
        {
            "id": "00D_UAT",
            "instance_url": "https://acme--uat.sandbox.my.salesforce.com",
            "is_sandbox": True,
        },
        {
            "id": "00D_MULTI_1",
            "instance_url": "https://multi--dev.sandbox.my.salesforce.com",
            "is_sandbox": True,
        },
        {
            "id": "00D_MULTI_2",
            "instance_url": "https://multi--qa.sandbox.my.salesforce.com",
            "is_sandbox": True,
        },
    ]

    result = resolve_okta_federation_links(okta_apps, [], [], [], salesforce_orgs)

    assert result["SalesforceOrganization"] == [
        {
            "okta_app_id": "app-sf-sandbox",
            "target_id": "00D_UAT",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.customDomain",
        },
    ]


def test_resolve_salesforce_sandbox_exact_custom_domain():
    okta_apps = [
        {
            "id": "app-sf-sandbox-full",
            "name": "salesforce",
            "sign_on_mode": "SAML_2_0",
            "settings_app_login_url": "https://test.salesforce.com",
            "settings_app_instance_type": "SANDBOX",
            "settings_app_custom_domain": "multi--dev",
        },
    ]
    salesforce_orgs = [
        {
            "id": "00D_MULTI_1",
            "instance_url": "https://multi--dev.sandbox.my.salesforce.com",
            "is_sandbox": True,
        },
        {
            "id": "00D_MULTI_2",
            "instance_url": "https://multi--qa.sandbox.my.salesforce.com",
            "is_sandbox": True,
        },
    ]

    result = resolve_okta_federation_links(okta_apps, [], [], [], salesforce_orgs)

    assert result["SalesforceOrganization"] == [
        {
            "okta_app_id": "app-sf-sandbox-full",
            "target_id": "00D_MULTI_1",
            "sign_on_mode": "SAML_2_0",
            "matched_on": "settings.app.customDomain",
        },
    ]
