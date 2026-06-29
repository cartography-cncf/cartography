from unittest.mock import patch

from requests import Response
from requests.exceptions import HTTPError

from cartography.intel.github.codeowners import build_codeowner_target_lookups
from cartography.intel.github.codeowners import build_manifest_codeowner_matches
from cartography.intel.github.codeowners import codeowners_pattern_matches
from cartography.intel.github.codeowners import CodeOwnersFileFetchResult
from cartography.intel.github.codeowners import get_effective_codeowners_file
from cartography.intel.github.codeowners import match_codeowner_rule_for_path
from cartography.intel.github.codeowners import normalize_repo_relative_path
from cartography.intel.github.codeowners import parse_codeowners_content
from cartography.intel.github.codeowners import transform_repositories_for_codeowners

ORG_URL = "https://github.com/simpsoncorp"
REPO_URL = "https://github.com/simpsoncorp/sample_repo"


def test_parse_codeowners_content_keeps_supported_rules_and_owner_tokens() -> None:
    # Arrange
    content = """
    # full-line comment
    * @global-owner @simpsoncorp/team-a
    *.js @js-owner # inline comment
    docs/* docs@example.com
    package.json
    !negated @ignored
    [abc].py @ignored
    \\#literal @ignored
    """

    # Act
    rules = parse_codeowners_content(
        content,
        REPO_URL,
        "sample_repo",
        "main",
        "CODEOWNERS",
        ORG_URL,
    )

    # Assert
    assert [rule["pattern"] for rule in rules] == [
        "*",
        "*.js",
        "docs/*",
    ]
    assert rules[0]["owners"] == ["@global-owner", "@simpsoncorp/team-a"]
    assert rules[0]["owner_logins"] == ["global-owner"]
    assert rules[0]["owner_team_slugs"] == ["team-a"]
    assert rules[0]["user_ids"] == ["https://github.com/global-owner"]
    assert rules[0]["team_ids"] == ["https://github.com/orgs/simpsoncorp/teams/team-a"]
    assert rules[1]["owners"] == ["@js-owner"]
    assert rules[2]["owner_emails"] == ["docs@example.com"]


def test_parse_codeowners_content_resolves_canonical_owner_urls() -> None:
    # Arrange
    content = "* @mixedcaseuser @mixedcaseorg/Security-Team"
    owner_targets = build_codeowner_target_lookups(
        [{"login": "MixedCaseUser", "url": "https://github.com/MixedCaseUser"}],
        [
            {
                "org_login": "MixedCaseOrg",
                "name": "security-team",
                "url": "https://github.com/orgs/MixedCaseOrg/teams/security-team",
            },
        ],
    )

    # Act
    rules = parse_codeowners_content(
        content,
        "https://github.com/MixedCaseOrg/sample_repo",
        "sample_repo",
        "main",
        "CODEOWNERS",
        "https://github.com/MixedCaseOrg",
        owner_targets,
    )

    # Assert
    assert rules[0]["owner_logins"] == ["mixedcaseuser"]
    assert rules[0]["owner_team_slugs"] == ["security-team"]
    assert rules[0]["user_ids"] == ["https://github.com/MixedCaseUser"]
    assert rules[0]["team_ids"] == [
        "https://github.com/orgs/MixedCaseOrg/teams/security-team",
    ]


def test_parse_codeowners_content_preserves_quotes_as_pattern_characters() -> None:
    # Arrange
    content = """
    docs/space\\ file.txt @space-owner
    docs/"quoted".txt @quote-owner
    """

    # Act
    rules = parse_codeowners_content(
        content,
        REPO_URL,
        "sample_repo",
        "main",
        "CODEOWNERS",
        ORG_URL,
    )

    # Assert
    assert [rule["pattern"] for rule in rules] == [
        "docs/space file.txt",
        'docs/"quoted".txt',
    ]
    assert rules[0]["owner_logins"] == ["space-owner"]
    assert rules[1]["owner_logins"] == ["quote-owner"]


def test_codeowners_pattern_matching_uses_github_precedence_examples() -> None:
    # Arrange
    rules = [
        {"id": "global", "pattern": "*"},
        {"id": "js", "pattern": "*.js"},
        {"id": "docs-direct", "pattern": "docs/*"},
        {"id": "logs", "pattern": "/build/logs/"},
        {"id": "apps", "pattern": "apps/"},
    ]

    # Act and assert
    assert codeowners_pattern_matches("*.js", "src/index.js")
    assert not codeowners_pattern_matches("docs/*", "docs/deep/guide.md")
    assert codeowners_pattern_matches("/build/logs/", "build/logs/app/run.log")
    assert not codeowners_pattern_matches("/build/logs/", "src/build/logs/app.log")
    assert codeowners_pattern_matches("apps/", "services/apps/api/main.go")
    js_rule = match_codeowner_rule_for_path(rules, "src/index.js")
    docs_rule = match_codeowner_rule_for_path(rules, "docs/getting-started.md")
    deep_docs_rule = match_codeowner_rule_for_path(rules, "docs/deep/guide.md")
    assert js_rule is not None
    assert docs_rule is not None
    assert deep_docs_rule is not None
    assert js_rule["id"] == "js"
    assert docs_rule["id"] == "docs-direct"
    assert deep_docs_rule["id"] == "global"


def test_normalize_repo_relative_path_handles_blob_urls_and_plain_paths() -> None:
    # Act and assert
    assert normalize_repo_relative_path("/package.json", REPO_URL) == "package.json"
    assert normalize_repo_relative_path("src/go.mod", REPO_URL) == "src/go.mod"
    assert (
        normalize_repo_relative_path(
            "/simpsoncorp/sample_repo/blob/main/services/api/go.mod",
            REPO_URL,
            "main",
        )
        == "services/api/go.mod"
    )
    assert (
        normalize_repo_relative_path(
            "/simpsoncorp/sample_repo/blob/release/2026/services/api/go.mod",
            REPO_URL,
            "release/2026",
        )
        == "services/api/go.mod"
    )


def test_build_manifest_codeowner_matches_normalizes_legacy_blob_paths() -> None:
    # Arrange
    rules = [
        {
            "id": "services-owner-rule",
            "repo_url": REPO_URL,
            "pattern": "/services/api/go.mod",
        },
    ]
    manifests = [
        {
            "manifest_id": "legacy-manifest",
            "repo_url": REPO_URL,
            "repo_relative_path": None,
            "blob_path": (
                "/simpsoncorp/sample_repo/blob/release/2026/services/api/go.mod"
            ),
            "default_branch": "release/2026",
        },
    ]

    # Act
    matches = build_manifest_codeowner_matches(rules, manifests)

    # Assert
    assert matches == [
        {
            "manifest_id": "legacy-manifest",
            "rule_id": "services-owner-rule",
            "matched_path": "services/api/go.mod",
            "match_pattern": "/services/api/go.mod",
        },
    ]


def test_transform_repositories_for_codeowners_filters_org_and_sorts_repos() -> None:
    # Arrange
    repositories = [
        {
            "id": "https://github.com/simpsoncorp/z-repo",
            "name": "z-repo",
            "defaultbranch": "main",
            "owner_org_id": ORG_URL,
        },
        {
            "id": "https://github.com/othercorp/other-repo",
            "name": "other-repo",
            "defaultbranch": "main",
            "owner_org_id": "https://github.com/othercorp",
        },
        {
            "id": REPO_URL,
            "name": "sample_repo",
            "defaultbranch": "release/2026",
            "owner_org_id": ORG_URL,
        },
        {
            "name": "missing-id",
            "defaultbranch": "main",
            "owner_org_id": ORG_URL,
        },
    ]

    # Act
    repos = transform_repositories_for_codeowners(repositories, ORG_URL)

    # Assert
    assert repos == [
        {
            "repo_url": REPO_URL,
            "repo_name": "sample_repo",
            "default_branch": "release/2026",
        },
        {
            "repo_url": "https://github.com/simpsoncorp/z-repo",
            "repo_name": "z-repo",
            "default_branch": "main",
        },
    ]


def test_build_manifest_codeowner_matches_uses_repo_sync_manifest_shape() -> None:
    # Arrange
    rules = [
        {
            "id": "services-owner-rule",
            "repo_url": REPO_URL,
            "pattern": "/services/api/go.mod",
        },
    ]
    manifests = [
        {
            "id": f"{REPO_URL}#/services/api/go.mod",
            "repo_url": REPO_URL,
            "repo_relative_path": None,
            "blob_path": (
                "/simpsoncorp/sample_repo/blob/release/2026/services/api/go.mod"
            ),
        },
    ]

    # Act
    matches = build_manifest_codeowner_matches(
        rules,
        manifests,
        {REPO_URL: "release/2026"},
    )

    # Assert
    assert matches == [
        {
            "manifest_id": f"{REPO_URL}#/services/api/go.mod",
            "rule_id": "services-owner-rule",
            "matched_path": "services/api/go.mod",
            "match_pattern": "/services/api/go.mod",
        },
    ]


def test_ownerless_codeowners_rules_do_not_override_valid_matches() -> None:
    # Arrange
    rules = parse_codeowners_content(
        """
        * @global-owner
        package.json
        """,
        REPO_URL,
        "sample_repo",
        "main",
        "CODEOWNERS",
        ORG_URL,
    )

    # Act
    matched_rule = match_codeowner_rule_for_path(rules, "package.json")

    # Assert
    assert matched_rule is not None
    assert matched_rule["owners"] == ["@global-owner"]


@patch("cartography.intel.github.codeowners.get_file_content")
def test_get_effective_codeowners_file_uses_documented_location_order(
    mock_get_file_content,
) -> None:
    # Arrange
    mock_get_file_content.side_effect = [None, "root owners", "docs owners"]

    # Act
    result = get_effective_codeowners_file(
        "token",
        "https://api.github.com/graphql",
        REPO_URL,
        "main",
    )

    # Assert
    assert result == CodeOwnersFileFetchResult(
        "CODEOWNERS",
        "root owners",
        cleanup_safe=True,
    )
    assert [call.args[3] for call in mock_get_file_content.call_args_list] == [
        ".github/CODEOWNERS",
        "CODEOWNERS",
    ]


@patch("cartography.intel.github.codeowners.get_file_content")
def test_get_effective_codeowners_file_marks_http_failures_not_cleanup_safe(
    mock_get_file_content,
) -> None:
    # Arrange
    response = Response()
    response.status_code = 403
    mock_get_file_content.side_effect = HTTPError(response=response)

    # Act
    result = get_effective_codeowners_file(
        "token",
        "https://api.github.com/graphql",
        REPO_URL,
        "main",
    )

    # Assert
    assert result == CodeOwnersFileFetchResult(None, None, cleanup_safe=False)
