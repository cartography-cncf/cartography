"""
Unit tests for GitHub Workflow YAML parser.
"""

from cartography.intel.github.actions import enrich_workflow_with_parsed_content
from cartography.intel.github.workflow_parser import deduplicate_actions
from cartography.intel.github.workflow_parser import extract_secrets_from_string
from cartography.intel.github.workflow_parser import parse_action_reference
from cartography.intel.github.workflow_parser import parse_permissions
from cartography.intel.github.workflow_parser import parse_workflow_yaml
from tests.data.github.workflow_content import WORKFLOW_CI_CONTENT
from tests.data.github.workflow_content import WORKFLOW_DOCKER_ACTION
from tests.data.github.workflow_content import WORKFLOW_EMPTY
from tests.data.github.workflow_content import WORKFLOW_FULL_PERMISSIONS
from tests.data.github.workflow_content import WORKFLOW_LOCAL_ACTION
from tests.data.github.workflow_content import WORKFLOW_MALFORMED
from tests.data.github.workflow_content import WORKFLOW_PINNED_ACTIONS
from tests.data.github.workflow_content import WORKFLOW_READ_ALL_PERMISSIONS
from tests.data.github.workflow_content import WORKFLOW_REUSABLE
from tests.data.github.workflow_content import WORKFLOW_SECRETS_EVERYWHERE

# =============================================================================
# Tests for parse_action_reference
# =============================================================================


def test_parse_action_reference_standard_action():
    result = parse_action_reference("actions/checkout@v4")
    assert result is not None
    assert result.owner == "actions"
    assert result.name == "checkout"
    assert result.version == "v4"
    assert result.is_pinned is False
    assert result.is_local is False
    assert result.full_name == "actions/checkout"


def test_parse_action_reference_pinned_action():
    result = parse_action_reference(
        "actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29"
    )
    assert result is not None
    assert result.owner == "actions"
    assert result.name == "checkout"
    assert result.version == "a5ac7e51b41094c92402da3b24376905380afc29"
    assert result.is_pinned is True


def test_parse_action_reference_local_action():
    result = parse_action_reference("./.github/actions/my-action")
    assert result is not None
    assert result.owner == ""
    assert result.name == "./.github/actions/my-action"
    assert result.is_local is True


def test_parse_action_reference_docker_action():
    result = parse_action_reference("docker://alpine:3.18")
    assert result is not None
    assert result.owner == "docker"
    assert result.name == "alpine:3.18"
    assert result.is_local is False


def test_parse_action_reference_reusable_workflow():
    result = parse_action_reference(
        "octo-org/example-repo/.github/workflows/reusable.yml@main"
    )
    assert result is not None
    assert result.owner == "octo-org"
    assert result.name == "example-repo/.github/workflows/reusable.yml"
    assert result.version == "main"


def test_parse_action_reference_empty_string():
    result = parse_action_reference("")
    assert result is None


def test_parse_action_reference_none():
    result = parse_action_reference(None)
    assert result is None


# =============================================================================
# Tests for secret extraction
# =============================================================================


def test_extract_secrets_single_secret():
    content = "token: ${{ secrets.MY_TOKEN }}"
    secrets = extract_secrets_from_string(content)
    assert secrets == {"MY_TOKEN"}


def test_extract_secrets_multiple_secrets():
    content = """
    env:
      TOKEN: ${{ secrets.TOKEN }}
      KEY: ${{ secrets.API_KEY }}
    """
    secrets = extract_secrets_from_string(content)
    assert secrets == {"TOKEN", "API_KEY"}


def test_extract_secrets_with_spaces():
    content = "${{secrets.NO_SPACE}} ${{ secrets.WITH_SPACE }}"
    secrets = extract_secrets_from_string(content)
    assert "NO_SPACE" in secrets
    assert "WITH_SPACE" in secrets


def test_extract_secrets_no_secrets():
    content = "run: echo hello"
    secrets = extract_secrets_from_string(content)
    assert secrets == set()


def test_extract_secrets_github_token():
    # GITHUB_TOKEN is a built-in, but our regex captures it
    # This is actually desired - we want to know all secret refs
    content = "${{ secrets.GITHUB_TOKEN }}"
    secrets = extract_secrets_from_string(content)
    assert secrets == {"GITHUB_TOKEN"}


def test_extract_secrets_bracket_notation():
    content = "${{ secrets['MY_SECRET'] }}"
    secrets = extract_secrets_from_string(content)
    assert secrets == {"MY_SECRET"}


def test_extract_secrets_bracket_double_quotes():
    content = '${{ secrets["API_KEY"] }}'
    secrets = extract_secrets_from_string(content)
    assert secrets == {"API_KEY"}


def test_extract_secrets_mixed_notations():
    content = """
    token: ${{ secrets.DOT_SECRET }}
    key: ${{ secrets['BRACKET_SECRET'] }}
    """
    secrets = extract_secrets_from_string(content)
    assert secrets == {"DOT_SECRET", "BRACKET_SECRET"}


# =============================================================================
# Tests for parse_permissions
# =============================================================================


def test_parse_permissions_dict():
    perms = {
        "contents": "read",
        "pull-requests": "write",
    }
    result = parse_permissions(perms)
    assert result["contents"] == "read"
    assert result["pull_requests"] == "write"


def test_parse_permissions_read_all():
    result = parse_permissions("read-all")
    assert result["actions"] == "read"
    assert result["contents"] == "read"
    assert result["packages"] == "read"
    assert result["pull_requests"] == "read"
    assert result["issues"] == "read"
    assert result["deployments"] == "read"
    assert result["statuses"] == "read"
    assert result["checks"] == "read"
    assert result["id_token"] == "read"
    assert result["security_events"] == "read"


def test_parse_permissions_write_all():
    result = parse_permissions("write-all")
    assert result["actions"] == "write"
    assert result["contents"] == "write"
    assert len(result) == 10


def test_parse_permissions_none():
    result = parse_permissions(None)
    assert result == {}


# =============================================================================
# Tests for parse_workflow_yaml
# =============================================================================


def test_parse_workflow_yaml_ci_workflow():
    result = parse_workflow_yaml(WORKFLOW_CI_CONTENT)
    assert result is not None

    # Check trigger events
    assert "push" in result.trigger_events
    assert "pull_request" in result.trigger_events

    # Check permissions
    assert result.permissions.get("contents") == "read"
    assert result.permissions.get("pull_requests") == "write"

    # Check env vars
    assert "NODE_VERSION" in result.env_vars

    # Check jobs
    assert result.job_count == 2

    # Check actions
    action_uses = [a.raw_uses for a in result.actions]
    assert "actions/checkout@v4" in action_uses
    assert "actions/setup-node@v4" in action_uses

    # Check secrets
    assert "NPM_TOKEN" in result.secret_refs
    assert "DATABASE_URL" in result.secret_refs
    assert "API_KEY" in result.secret_refs


def test_parse_workflow_yaml_pinned_actions():
    result = parse_workflow_yaml(WORKFLOW_PINNED_ACTIONS)
    assert result is not None

    # All actions should be pinned
    for action in result.actions:
        assert action.is_pinned is True


def test_parse_workflow_yaml_reusable():
    result = parse_workflow_yaml(WORKFLOW_REUSABLE)
    assert result is not None

    # Check reusable workflow calls
    assert len(result.reusable_workflow_calls) == 2
    assert "./.github/workflows/build.yml" in result.reusable_workflow_calls

    # Check secrets from reusable workflow call
    assert "DEPLOY_KEY" in result.secret_refs


def test_parse_workflow_yaml_full_permissions():
    result = parse_workflow_yaml(WORKFLOW_FULL_PERMISSIONS)
    assert result is not None

    # All permission types should be present
    assert result.permissions.get("actions") == "write"
    assert result.permissions.get("contents") == "write"
    assert result.permissions.get("packages") == "write"
    assert result.permissions.get("pull_requests") == "write"
    assert result.permissions.get("issues") == "write"
    assert result.permissions.get("deployments") == "write"
    assert result.permissions.get("statuses") == "write"
    assert result.permissions.get("checks") == "write"
    assert result.permissions.get("id_token") == "write"
    assert result.permissions.get("security_events") == "write"


def test_parse_workflow_yaml_docker_action():
    result = parse_workflow_yaml(WORKFLOW_DOCKER_ACTION)
    assert result is not None

    docker_actions = [a for a in result.actions if a.owner == "docker"]
    assert len(docker_actions) == 2


def test_parse_workflow_yaml_local_action():
    result = parse_workflow_yaml(WORKFLOW_LOCAL_ACTION)
    assert result is not None

    local_actions = [a for a in result.actions if a.is_local]
    assert len(local_actions) == 1
    assert "./.github/actions/my-custom-action" in local_actions[0].name


def test_parse_workflow_yaml_empty():
    result = parse_workflow_yaml(WORKFLOW_EMPTY)
    assert result is None


def test_parse_workflow_yaml_malformed():
    result = parse_workflow_yaml(WORKFLOW_MALFORMED)
    assert result is None


def test_parse_workflow_yaml_secrets_everywhere():
    result = parse_workflow_yaml(WORKFLOW_SECRETS_EVERYWHERE)
    assert result is not None

    expected_secrets = {
        "GLOBAL_SECRET",
        "JOB_SECRET",
        "STEP_SECRET",
        "AUTH_TOKEN",
        "STEP_ENV_SECRET",
        "WITH_SECRET",
        "ANOTHER_SECRET",
    }
    assert set(result.secret_refs) == expected_secrets


# =============================================================================
# Tests for deduplicate_actions
# =============================================================================


def test_deduplicate_actions():
    action1 = parse_action_reference("actions/checkout@v4")
    action2 = parse_action_reference("actions/checkout@v4")
    action3 = parse_action_reference("actions/setup-node@v4")

    result = deduplicate_actions([action1, action2, action3])
    assert len(result) == 2


def test_deduplicate_actions_different_versions():
    action1 = parse_action_reference("actions/checkout@v4")
    action2 = parse_action_reference("actions/checkout@v3")

    result = deduplicate_actions([action1, action2])
    assert len(result) == 2


# =============================================================================
# Tests for enrich_workflow_with_parsed_content (global permissions)
# =============================================================================


def test_enrich_workflow_read_all_permissions():
    """Test that read-all permissions are expanded to all scopes after enrichment."""
    parsed = parse_workflow_yaml(WORKFLOW_READ_ALL_PERMISSIONS)
    assert parsed is not None

    workflow: dict = {"id": 1, "name": "Read All"}
    enriched = enrich_workflow_with_parsed_content(workflow, parsed, "myorg", "myrepo")

    assert enriched["permissions_actions"] == "read"
    assert enriched["permissions_contents"] == "read"
    assert enriched["permissions_packages"] == "read"
    assert enriched["permissions_pull_requests"] == "read"
    assert enriched["permissions_issues"] == "read"
    assert enriched["permissions_deployments"] == "read"
    assert enriched["permissions_statuses"] == "read"
    assert enriched["permissions_checks"] == "read"
    assert enriched["permissions_id_token"] == "read"
    assert enriched["permissions_security_events"] == "read"
