from copy import deepcopy
from unittest.mock import patch

import pytest

import cartography.intel.github.repos
from cartography.intel.github.repos import _build_branch_data
from cartography.intel.github.repos import _create_git_url_from_ssh_url
from cartography.intel.github.repos import _get_repo_rulesets_by_url
from cartography.intel.github.repos import _merge_repos_with_privileged_details
from cartography.intel.github.repos import _normalize_rest_ruleset
from cartography.intel.github.repos import _repos_need_privileged_details
from cartography.intel.github.repos import _transform_dependency_graph
from cartography.intel.github.repos import _transform_dependency_manifests
from cartography.intel.github.repos import _transform_python_requirements
from cartography.intel.github.repos import _transform_rulesets
from cartography.intel.github.repos import transform
from tests.data.github.repos import DEP_MANIFESTS_BY_URL
from tests.data.github.repos import DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS
from tests.data.github.repos import GET_REPOS
from tests.data.github.rulesets import RULESET_PRODUCTION

TEST_UPDATE_TAG = 123456789

REST_RULESET_PRODUCTION = {
    "id": 5351760,
    "node_id": "RRS_lACkVXNlcs4AXenizgBRqVA",
    "name": "production-ruleset",
    "target": "branch",
    "source_type": "Organization",
    "source": "simpsoncorp",
    "enforcement": "active",
    "created_at": "2025-05-07T21:04:33Z",
    "updated_at": "2025-05-07T21:04:33Z",
    "conditions": {
        "ref_name": {
            "include": ["~DEFAULT_BRANCH"],
            "exclude": [],
        },
        "repository_name": {
            "include": ["important-*"],
            "exclude": ["important-archive"],
            "protected": False,
        },
        "repository_id": {
            "repository_ids": [123456789],
        },
        "repository_property": {
            "include": [
                {
                    "name": "visibility",
                    "property_values": ["private"],
                    "source": "custom",
                },
            ],
            "exclude": [],
        },
        "organization_property": {
            "include": [
                {
                    "name": "environment",
                    "property_values": ["prod"],
                },
            ],
            "exclude": [
                {
                    "name": "lifecycle",
                    "property_values": ["deprecated"],
                },
            ],
        },
    },
    "rules": [
        {
            "type": "deletion",
        },
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": 2,
                "dismiss_stale_reviews_on_push": True,
                "require_code_owner_review": True,
            },
        },
        {
            "type": "required_status_checks",
            "parameters": {
                "required_status_checks": [
                    {"context": "ci/tests"},
                ],
            },
        },
    ],
}


def test_transform_dependency_manifests_converts_to_expected_format():
    """
    Test that the manifest transformation function correctly processes GitHub API data
    into the format expected for loading manifest nodes into the database.
    """
    # Arrange
    repo_url = "https://github.com/test-org/test-repo"
    output_list = []

    # Act
    _transform_dependency_manifests(
        DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS, repo_url, output_list
    )

    # Assert: Check that 3 manifests were transformed
    assert len(output_list) == 3

    # Assert: Check that expected manifest IDs are present
    manifest_ids = {manifest["id"] for manifest in output_list}
    expected_ids = {
        "https://github.com/test-org/test-repo#/package.json",
        "https://github.com/test-org/test-repo#/requirements.txt",
        "https://github.com/test-org/test-repo#/pom.xml",
    }
    assert manifest_ids == expected_ids

    # Assert: Check that a specific manifest has expected properties
    package_json_manifest = next(
        manifest for manifest in output_list if manifest["filename"] == "package.json"
    )
    assert (
        package_json_manifest["id"]
        == "https://github.com/test-org/test-repo#/package.json"
    )
    assert package_json_manifest["blob_path"] == "/package.json"
    assert package_json_manifest["filename"] == "package.json"
    assert package_json_manifest["dependencies_count"] == 2  # react and lodash
    assert package_json_manifest["repo_url"] == repo_url

    # Assert: Check requirements.txt manifest
    requirements_manifest = next(
        manifest
        for manifest in output_list
        if manifest["filename"] == "requirements.txt"
    )
    assert requirements_manifest["dependencies_count"] == 1  # Django
    assert requirements_manifest["blob_path"] == "/requirements.txt"

    # Assert: Check pom.xml manifest
    pom_manifest = next(
        manifest for manifest in output_list if manifest["filename"] == "pom.xml"
    )
    assert pom_manifest["dependencies_count"] == 1  # spring-core
    assert pom_manifest["blob_path"] == "/pom.xml"


def test_transform_dependency_converts_to_expected_format():
    """
    Test that the dependency transformation function correctly processes GitHub API data
    into the format expected for loading into the database.
    """
    # Arrange
    repo_url = "https://github.com/test-org/test-repo"
    output_list = []

    # Act
    _transform_dependency_graph(
        DEPENDENCY_GRAPH_WITH_MULTIPLE_ECOSYSTEMS, repo_url, output_list
    )

    # Assert: Check that 4 dependencies were transformed
    assert len(output_list) == 4

    # Assert: Check that expected dependency IDs are present (now using raw requirements)
    dependency_ids = {dep["id"] for dep in output_list}
    expected_ids = {
        "react|18.2.0",
        "lodash",
        "django|= 4.2.0",
        "org.springframework:spring-core|5.3.21",
    }
    assert dependency_ids == expected_ids

    # Assert: Check that a specific dependency has expected properties
    react_dep = next(dep for dep in output_list if dep["original_name"] == "react")
    assert react_dep["id"] == "react|18.2.0"
    assert react_dep["name"] == "react"
    assert react_dep["requirements"] == "18.2.0"
    assert react_dep["ecosystem"] == "npm"
    assert react_dep["package_manager"] == "NPM"
    assert react_dep["manifest_path"] == "/package.json"
    assert react_dep["repo_url"] == repo_url
    assert react_dep["manifest_file"] == "package.json"


def test_transform_python_requirements_skips_flags_and_continuations():
    repo_url = "https://github.com/test-org/test-repo"
    output_list = []
    requirements_list = [
        "requests==2.31.0 \\",
        "    --hash=sha256:1111111111111111111111111111111111111111111111111111111111111111 \\",
        "    --hash=sha256:2222222222222222222222222222222222222222222222222222222222222222",
        "--extra-index-url https://example.com/simple",
        "-r base.txt",
        "boto3==1.34.0 \\",
        '    ; python_version >= "3.9"',
        "pytest==8.0.2",
    ]

    _transform_python_requirements(requirements_list, repo_url, output_list)

    deps_by_name = {dep["name"]: dep for dep in output_list}

    assert set(deps_by_name) == {"boto3", "pytest", "requests"}

    requests_dep = deps_by_name["requests"]
    assert requests_dep["version"] == "2.31.0"
    assert requests_dep["specifier"] == "==2.31.0"
    assert requests_dep["id"] == "requests|2.31.0"
    assert requests_dep["repo_url"] == repo_url

    boto3_dep = deps_by_name["boto3"]
    assert boto3_dep["version"] == "1.34.0"
    assert boto3_dep["specifier"] == "==1.34.0"

    pytest_dep = deps_by_name["pytest"]
    assert pytest_dep["version"] == "8.0.2"
    assert pytest_dep["specifier"] == "==8.0.2"


def test_create_git_url_from_ssh_url():
    """
    Test that _create_git_url_from_ssh_url correctly converts SSH URLs to git:// format.
    """
    # Arrange
    ssh_url = "git@github.com:cartography-cncf/cartography.git"
    expected_result = "git://github.com/cartography-cncf/cartography.git"

    # Act
    result = _create_git_url_from_ssh_url(ssh_url)

    # Assert
    assert result == expected_result

    # Test with nested path (monorepo case)
    ssh_url_nested = "git@github.com:user/nested/path/repo.git"
    expected_nested = "git://github.com/user/nested/path/repo.git"
    result_nested = _create_git_url_from_ssh_url(ssh_url_nested)
    assert result_nested == expected_nested


def test_transform_skips_null_repository_entries():
    repo_with_collab_counts = GET_REPOS[0]

    result = transform(
        [None, repo_with_collab_counts],
        {repo_with_collab_counts["url"]: []},
        {repo_with_collab_counts["url"]: []},
    )

    assert len(result["repos"]) == 1
    assert result["repos"][0]["id"] == repo_with_collab_counts["url"]


def test_transform_includes_branch_protection_rules():
    """
    Test that the transform function includes branch protection rules in the output.
    """
    # Arrange - GET_REPOS[2] has branchProtectionRules
    repo_with_branch_protection_rules = GET_REPOS[2]

    # Act
    result = transform(
        [repo_with_branch_protection_rules],
        {repo_with_branch_protection_rules["url"]: []},
        {repo_with_branch_protection_rules["url"]: []},
    )

    # Assert: Check that branch_protection_rules key is present in the result
    assert "branch_protection_rules" in result

    # Assert: Check that we have 1 branch protection rule from the test data
    assert len(result["branch_protection_rules"]) == 1

    # Assert: Check the branch protection rule has expected properties
    rule = result["branch_protection_rules"][0]
    assert rule["id"] == "BPR_kwDOAbc123=="
    assert rule["pattern"] == "main"
    assert rule["allows_deletions"] is False
    assert rule["requires_approving_reviews"] is True
    assert rule["required_approving_review_count"] == 2
    assert rule["repo_url"] == repo_with_branch_protection_rules["url"]


def test_transform_includes_rulesets():
    """
    Test that the transform function includes rulesets in the output.
    """
    repo_with_rulesets = GET_REPOS[2]

    result = transform(
        [repo_with_rulesets],
        {repo_with_rulesets["url"]: []},
        {repo_with_rulesets["url"]: []},
    )

    assert "rulesets" in result
    assert "ruleset_rules" in result

    assert len(result["rulesets"]) == 1
    assert len(result["ruleset_rules"]) == 3

    ruleset = result["rulesets"][0]
    assert ruleset["id"] == "RRS_lACkVXNlcs4AXenizgBRqVA"
    assert ruleset["name"] == "production-ruleset"
    assert ruleset["target"] == "BRANCH"
    assert ruleset["enforcement"] == "ACTIVE"
    assert ruleset["repo_url"] == repo_with_rulesets["url"]


def test_normalize_rest_ruleset_converts_to_transform_shape():
    normalized = _normalize_rest_ruleset(REST_RULESET_PRODUCTION)

    assert normalized["id"] == "RRS_lACkVXNlcs4AXenizgBRqVA"
    assert normalized["databaseId"] == 5351760
    assert normalized["target"] == "BRANCH"
    assert normalized["enforcement"] == "ACTIVE"
    assert normalized["conditions"]["repositoryId"]["repositoryIds"] == [123456789]
    assert normalized["conditions"]["repositoryProperty"]["include"] == [
        {
            "name": "visibility",
            "propertyValues": ["private"],
            "source": "custom",
        },
    ]

    rule_ids = [rule["id"] for rule in normalized["rules"]["nodes"]]
    assert rule_ids[0].startswith("RRS_lACkVXNlcs4AXenizgBRqVA:rule:0:")
    assert rule_ids == [
        rule["id"]
        for rule in _normalize_rest_ruleset(REST_RULESET_PRODUCTION)["rules"]["nodes"]
    ]
    assert normalized["rules"]["nodes"][1]["type"] == "PULL_REQUEST"
    assert normalized["rules"]["nodes"][1]["parameters"] == {
        "requiredApprovingReviewCount": 2,
        "dismissStaleReviewsOnPush": True,
        "requireCodeOwnerReview": True,
    }


@patch.object(cartography.intel.github.repos, "call_github_rest_api")
@patch.object(cartography.intel.github.repos, "fetch_all_rest_api_pages")
def test_get_repo_rulesets_by_url_fetches_rest_ruleset_details_and_reuses_cache(
    mock_fetch_all_rest_api_pages,
    mock_call_github_rest_api,
):
    repos = [
        {
            "name": "repo-one",
            "url": "https://github.com/simpsoncorp/repo-one",
        },
        {
            "name": "repo-two",
            "url": "https://github.com/simpsoncorp/repo-two",
        },
    ]
    ruleset_summary = {
        "id": 5351760,
        "node_id": "RRS_lACkVXNlcs4AXenizgBRqVA",
        "source_type": "Organization",
        "source": "simpsoncorp",
    }
    mock_fetch_all_rest_api_pages.side_effect = [
        [ruleset_summary],
        [ruleset_summary],
    ]
    mock_call_github_rest_api.return_value = REST_RULESET_PRODUCTION

    result = _get_repo_rulesets_by_url(
        "token",
        "https://api.github.com/graphql",
        "simpsoncorp",
        repos,
    )

    assert set(result) == {
        "https://github.com/simpsoncorp/repo-one",
        "https://github.com/simpsoncorp/repo-two",
    }
    assert result["https://github.com/simpsoncorp/repo-one"]["totalCount"] == 1
    assert result["https://github.com/simpsoncorp/repo-two"]["nodes"][0]["id"] == (
        "RRS_lACkVXNlcs4AXenizgBRqVA"
    )
    assert mock_fetch_all_rest_api_pages.call_count == 2
    assert mock_fetch_all_rest_api_pages.call_args_list[0].args == (
        "token",
        "https://api.github.com",
        "/repos/simpsoncorp/repo-one/rulesets",
    )
    assert mock_fetch_all_rest_api_pages.call_args_list[0].kwargs["result_key"] == (
        "rulesets"
    )
    assert mock_fetch_all_rest_api_pages.call_args_list[0].kwargs["params"] == {
        "per_page": 100,
        "includes_parents": "true",
    }
    assert mock_fetch_all_rest_api_pages.call_args_list[0].kwargs[
        "raise_on_status"
    ] == (403, 404)
    mock_call_github_rest_api.assert_called_once_with(
        "/repos/simpsoncorp/repo-one/rulesets/5351760",
        "token",
        "https://api.github.com",
        params={"includes_parents": "true"},
    )


def test_transform_rulesets_requires_ruleset_id():
    out_rulesets = []
    out_rules = []

    with pytest.raises(KeyError):
        _transform_rulesets(
            [
                {
                    "rules": {"nodes": []},
                }
            ],
            "https://github.com/simpsoncorp/repo",
            out_rulesets,
            out_rules,
        )


def test_transform_rulesets_requires_rule_id():
    ruleset = deepcopy(RULESET_PRODUCTION)
    del ruleset["rules"]["nodes"][0]["id"]
    out_rulesets = []
    out_rules = []

    with pytest.raises(KeyError):
        _transform_rulesets(
            [ruleset],
            "https://github.com/simpsoncorp/repo",
            out_rulesets,
            out_rules,
        )


def test_transform_rulesets_skips_null_rulesets_and_rules():
    ruleset = deepcopy(RULESET_PRODUCTION)
    ruleset["rules"]["nodes"] = [None]
    out_rulesets = []
    out_rules = []

    _transform_rulesets(
        [None, ruleset],
        "https://github.com/simpsoncorp/repo",
        out_rulesets,
        out_rules,
    )

    assert [ruleset["id"] for ruleset in out_rulesets] == [RULESET_PRODUCTION["id"]]
    assert out_rules == []


def test_transform_prefers_dependency_graph_over_requirements_txt():
    repo = dict(GET_REPOS[2])
    repo_url = repo["url"]
    # Simulate what sync() does: inject dep manifests fetched separately
    repo["dependencyGraphManifests"] = DEP_MANIFESTS_BY_URL[repo_url]

    result = transform(
        [repo],
        {repo_url: []},
        {repo_url: []},
    )

    # Dependency graph is present; requirements files are used only as fallback
    assert result["python_requirements"] == []
    # Dependencies should still come from the dependency graph data
    dependency_ids = {dep["id"] for dep in result["dependencies"]}
    assert dependency_ids == {
        "react|18.2.0",
        "lodash",
        "django|= 4.2.0",
        "org.springframework:spring-core|5.3.21",
    }


def test_transform_uses_requirements_when_dependency_graph_missing():
    repo = GET_REPOS[0]
    repo_url = repo["url"]

    result = transform(
        [repo],
        {repo_url: []},
        {repo_url: []},
    )

    # No dependency graph data, so requirements parsing should run
    requirement_names = {req["name"] for req in result["python_requirements"]}
    assert {"cartography", "httplib2", "jinja2", "lxml"}.issubset(requirement_names)


def test_merge_repos_with_privileged_details_merges_by_url():
    base_repos = deepcopy(GET_REPOS[:2])
    for repo in base_repos:
        repo.pop("directCollaborators", None)
        repo.pop("outsideCollaborators", None)
        repo.pop("branchProtectionRules", None)
        repo.pop("rulesets", None)

    privileged_repo_data = {
        base_repos[0]["url"]: {
            "directCollaborators": {"totalCount": 0},
            "outsideCollaborators": {"totalCount": 0},
            "branchProtectionRules": {"nodes": []},
            "rulesets": {"nodes": []},
        },
        "https://github.com/simpsoncorp/non_matching_repo": {
            "directCollaborators": {"totalCount": 99},
            "outsideCollaborators": {"totalCount": 99},
            "branchProtectionRules": {"nodes": []},
            "rulesets": {"nodes": []},
        },
    }

    merged_repos, merged_repo_count, missing_repo_count = (
        _merge_repos_with_privileged_details(base_repos, privileged_repo_data)
    )

    assert merged_repo_count == 1
    assert missing_repo_count == 1
    assert merged_repos[0]["directCollaborators"] == {"totalCount": 0}
    assert merged_repos[0]["outsideCollaborators"] == {"totalCount": 0}
    assert merged_repos[0]["branchProtectionRules"] == {"nodes": []}
    assert merged_repos[0]["rulesets"] == {"nodes": []}
    assert "directCollaborators" not in merged_repos[1]
    assert "outsideCollaborators" not in merged_repos[1]
    assert "branchProtectionRules" not in merged_repos[1]
    assert "rulesets" not in merged_repos[1]
    # Ensure input repos are not mutated by merge.
    assert "directCollaborators" not in base_repos[0]


def test_repos_need_privileged_details_when_fields_missing():
    repo = deepcopy(GET_REPOS[0])
    repo.pop("directCollaborators", None)
    repo.pop("outsideCollaborators", None)
    repo.pop("branchProtectionRules", None)
    repo.pop("rulesets", None)

    assert _repos_need_privileged_details([repo]) is True


def test_repos_need_privileged_details_when_fields_present():
    assert _repos_need_privileged_details([GET_REPOS[0], GET_REPOS[2]]) is False


def test_build_branch_data_includes_owner_org_id():
    transformed_repo = {
        "id": "https://github.com/simpsoncorp/sample_repo",
        "defaultbranch": "main",
        "defaultbranchid": "branch_ref_id==",
        "owner_org_id": "https://github.com/simpsoncorp",
    }

    assert _build_branch_data([transformed_repo]) == [
        {
            "id": "branch_ref_id==",
            "name": "main",
            "repo_id": "https://github.com/simpsoncorp/sample_repo",
            "owner_org_id": "https://github.com/simpsoncorp",
        }
    ]


@patch.object(cartography.intel.github.repos, "run_analysis_job")
@patch.object(cartography.intel.github.repos, "cleanup_rulesets")
@patch.object(cartography.intel.github.repos, "cleanup_branch_protection_rules")
@patch.object(cartography.intel.github.repos, "cleanup_github_manifests")
@patch.object(cartography.intel.github.repos, "cleanup_github_dependencies")
@patch.object(cartography.intel.github.repos, "cleanup_python_requirements")
@patch.object(cartography.intel.github.repos, "cleanup_github_collaborators")
@patch.object(cartography.intel.github.repos, "cleanup_github_owners")
@patch.object(cartography.intel.github.repos, "cleanup_github_languages")
@patch.object(cartography.intel.github.repos, "cleanup_github_branches")
@patch.object(cartography.intel.github.repos, "cleanup_github_repos")
@patch.object(cartography.intel.github.repos, "load")
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
    return_value={},
)
@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value={},
)
@patch.object(cartography.intel.github.repos, "get", return_value=[])
def test_sync_cleans_up_branches_when_org_has_no_repos(
    mock_get,
    mock_get_dep_manifests,
    mock_get_repo_collaborators,
    mock_load,
    mock_cleanup_github_repos,
    mock_cleanup_github_branches,
    mock_cleanup_github_languages,
    mock_cleanup_github_owners,
    mock_cleanup_github_collaborators,
    mock_cleanup_python_requirements,
    mock_cleanup_github_dependencies,
    mock_cleanup_github_manifests,
    mock_cleanup_branch_protection_rules,
    mock_cleanup_rulesets,
    mock_run_analysis_job,
):
    cartography.intel.github.repos.sync(
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        "token",
        "https://api.github.com/graphql",
        "example-org",
    )

    mock_cleanup_github_repos.assert_not_called()
    mock_cleanup_github_branches.assert_called_once_with(
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        "https://github.com/example-org",
    )
    mock_cleanup_github_languages.assert_not_called()
    mock_cleanup_github_owners.assert_not_called()
    mock_cleanup_github_collaborators.assert_not_called()
    mock_cleanup_python_requirements.assert_not_called()
    # cleanup_github_dependencies runs in cleanup_global_resources (once per
    # sync cycle), not from per-org sync(); see GitHubDependencySchema.
    mock_cleanup_github_dependencies.assert_not_called()
    mock_cleanup_github_manifests.assert_called_once_with(
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        "https://github.com/example-org",
    )
    mock_cleanup_branch_protection_rules.assert_called_once_with(
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        "https://github.com/example-org",
    )
    mock_cleanup_rulesets.assert_called_once_with(
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        "https://github.com/example-org",
    )


@patch.object(
    cartography.intel.github.repos,
    "get_repo_privileged_details_by_url",
    side_effect=ValueError("privileged fetch failed"),
)
@patch.object(cartography.intel.github.repos, "run_analysis_job")
@patch.object(cartography.intel.github.repos, "cleanup_rulesets")
@patch.object(cartography.intel.github.repos, "cleanup_branch_protection_rules")
@patch.object(cartography.intel.github.repos, "cleanup_github_manifests")
@patch.object(cartography.intel.github.repos, "cleanup_github_dependencies")
@patch.object(cartography.intel.github.repos, "cleanup_python_requirements")
@patch.object(cartography.intel.github.repos, "cleanup_github_collaborators")
@patch.object(cartography.intel.github.repos, "cleanup_github_owners")
@patch.object(cartography.intel.github.repos, "cleanup_github_languages")
@patch.object(cartography.intel.github.repos, "cleanup_github_branches")
@patch.object(cartography.intel.github.repos, "cleanup_github_repos")
@patch.object(cartography.intel.github.repos, "load")
@patch.object(
    cartography.intel.github.repos,
    "_get_repo_collaborators_for_multiple_repos",
    return_value={},
)
@patch.object(
    cartography.intel.github.repos,
    "_get_dep_manifests_for_repos",
    return_value={},
)
@patch.object(cartography.intel.github.repos, "get")
def test_sync_continues_when_privileged_fetch_fails(
    mock_get,
    mock_get_dep_manifests,
    mock_get_repo_collaborators,
    mock_load,
    mock_cleanup_github_repos,
    mock_cleanup_github_branches,
    mock_cleanup_github_languages,
    mock_cleanup_github_owners,
    mock_cleanup_github_collaborators,
    mock_cleanup_python_requirements,
    mock_cleanup_github_dependencies,
    mock_cleanup_github_manifests,
    mock_cleanup_branch_protection_rules,
    mock_cleanup_rulesets,
    mock_run_analysis_job,
    mock_get_privileged,
):
    repo = deepcopy(GET_REPOS[0])
    repo.pop("directCollaborators", None)
    repo.pop("outsideCollaborators", None)
    repo.pop("branchProtectionRules", None)
    repo.pop("rulesets", None)
    mock_get.return_value = [repo]

    cartography.intel.github.repos.sync(
        None,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
        "token",
        "https://api.github.com/graphql",
        "example-org",
    )

    mock_get_privileged.assert_called_once_with(
        "token",
        "https://api.github.com/graphql",
        "example-org",
    )
    assert mock_get_repo_collaborators.call_count == 2
    mock_load.assert_called_once()
    mock_cleanup_github_repos.assert_not_called()
    mock_cleanup_github_branches.assert_called_once()
    mock_cleanup_github_languages.assert_not_called()
    mock_cleanup_github_owners.assert_not_called()
    mock_cleanup_github_collaborators.assert_not_called()
    mock_cleanup_python_requirements.assert_not_called()
    # cleanup_github_dependencies runs in cleanup_global_resources (once per
    # sync cycle), not from per-org sync(); see GitHubDependencySchema.
    mock_cleanup_github_dependencies.assert_not_called()
    mock_cleanup_github_manifests.assert_called_once()
    mock_cleanup_branch_protection_rules.assert_called_once()
    mock_cleanup_rulesets.assert_not_called()
