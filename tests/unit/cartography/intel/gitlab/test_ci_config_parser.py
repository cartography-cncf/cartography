"""Unit tests for the GitLab CI config YAML parser."""

from cartography.intel.gitlab.ci_config_parser import _is_pinned
from cartography.intel.gitlab.ci_config_parser import parse_ci_config
from cartography.intel.gitlab.ci_config_parser import parse_lint_includes
from tests.data.gitlab.ci_configs import PIPELINE_BAD_YAML
from tests.data.gitlab.ci_configs import PIPELINE_EMPTY
from tests.data.gitlab.ci_configs import PIPELINE_LOCAL_LIST
from tests.data.gitlab.ci_configs import PIPELINE_NO_INCLUDES
from tests.data.gitlab.ci_configs import PIPELINE_NOT_A_DICT
from tests.data.gitlab.ci_configs import PIPELINE_SCHEDULED
from tests.data.gitlab.ci_configs import PIPELINE_WITH_MIXED_INCLUDES


def test_parse_includes_string_form_treated_as_local():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    locals_ = [i for i in parsed.includes if i.include_type == "local"]
    assert len(locals_) >= 1
    assert locals_[0].location == "/templates/local-template.yml"
    assert locals_[0].is_pinned is True
    assert locals_[0].is_local is True


def test_parse_includes_project_pinned_vs_unpinned():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    project_includes = [i for i in parsed.includes if i.include_type == "project"]
    assert len(project_includes) == 2
    pinned = [i for i in project_includes if i.is_pinned]
    unpinned = [i for i in project_includes if not i.is_pinned]
    assert len(pinned) == 1
    assert len(unpinned) == 1
    assert pinned[0].ref == "a5ac7e51b41094c92402da3b24376905380afc29"
    assert unpinned[0].ref == "main"


def test_parse_includes_remote_and_template_present():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    types = {i.include_type for i in parsed.includes}
    assert "remote" in types
    assert "template" in types


def test_parse_includes_remote_unpinned_url():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    remote = next(i for i in parsed.includes if i.include_type == "remote")
    assert remote.is_pinned is False


def test_parse_includes_bare_url_string_classified_as_remote():
    """A bare URL string in `include:` should be remote, not local."""
    yaml = """
include:
  - 'https://example.com/templates/foo.yml'
build:
  script:
    - echo
"""
    parsed = parse_ci_config(yaml)
    assert len(parsed.includes) == 1
    inc = parsed.includes[0]
    assert inc.include_type == "remote"
    assert inc.is_local is False
    assert inc.is_pinned is False


def test_parse_includes_project_records_file_field():
    """include:project must capture the `file:` path so the location is accurate."""
    yaml = """
include:
  - project: my-org/shared-ci
    ref: a5ac7e51b41094c92402da3b24376905380afc29
    file: /templates/build.yml
build:
  script:
    - echo
"""
    parsed = parse_ci_config(yaml)
    project_includes = [i for i in parsed.includes if i.include_type == "project"]
    assert len(project_includes) == 1
    assert project_includes[0].location == "my-org/shared-ci:/templates/build.yml"


def test_parse_includes_project_with_file_list_expands_to_one_record_per_file():
    yaml = """
include:
  - project: my-org/shared-ci
    ref: a5ac7e51b41094c92402da3b24376905380afc29
    file:
      - /templates/a.yml
      - /templates/b.yml
build:
  script:
    - echo
"""
    parsed = parse_ci_config(yaml)
    project_includes = [i for i in parsed.includes if i.include_type == "project"]
    assert len(project_includes) == 2
    locations = {i.location for i in project_includes}
    assert locations == {
        "my-org/shared-ci:/templates/a.yml",
        "my-org/shared-ci:/templates/b.yml",
    }


def test_parse_includes_local_list_expands():
    parsed = parse_ci_config(PIPELINE_LOCAL_LIST)
    locals_ = [i for i in parsed.includes if i.include_type == "local"]
    assert len(locals_) == 2
    assert {i.location for i in locals_} == {"/templates/a.yml", "/templates/b.yml"}


def test_parse_stages():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    assert parsed.stages == ["build", "test", "deploy"]


def test_parse_job_count_excludes_reserved_keywords():
    """3 jobs: build, manual_deploy, mr_only. variables/stages/default/include are not jobs."""
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    assert parsed.job_count == 3


def test_parse_default_image_from_default_block():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    assert parsed.default_image == "python:3.13"


def test_parse_default_image_top_level():
    parsed = parse_ci_config(PIPELINE_NO_INCLUDES)
    assert parsed.default_image == "alpine:3.20"


def test_parse_referenced_variables_excludes_predefined():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    assert "DATABASE_URL" in parsed.referenced_variable_keys
    assert "DEPLOY_TOKEN" in parsed.referenced_variable_keys
    # Predefined variables filtered
    assert "CI_PROJECT_NAME" not in parsed.referenced_variable_keys
    assert "CI_PIPELINE_SOURCE" not in parsed.referenced_variable_keys


def test_parse_trigger_rules_detects_manual_and_merge_request():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    assert "manual" in parsed.trigger_rules
    assert "merge_requests" in parsed.trigger_rules


def test_parse_trigger_rules_detects_schedule():
    parsed = parse_ci_config(PIPELINE_SCHEDULED)
    assert "schedules" in parsed.trigger_rules


def test_parse_empty_yaml_returns_empty():
    parsed = parse_ci_config(PIPELINE_EMPTY)
    assert parsed.includes == []
    assert parsed.job_count == 0


def test_parse_non_dict_yaml_returns_empty():
    parsed = parse_ci_config(PIPELINE_NOT_A_DICT)
    assert parsed.includes == []
    assert parsed.job_count == 0


def test_parse_bad_yaml_returns_empty():
    parsed = parse_ci_config(PIPELINE_BAD_YAML)
    assert parsed.includes == []
    assert parsed.job_count == 0


def test_parse_propagates_is_valid():
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES, is_valid=True)
    assert parsed.is_valid is True
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES, is_valid=False)
    assert parsed.is_valid is False
    parsed = parse_ci_config(PIPELINE_WITH_MIXED_INCLUDES)
    assert parsed.is_valid is None


def test_parse_lint_includes_normalises_file_with_project_to_project_shape():
    """
    GitLab's /ci/lint returns project includes as ``type: "file"`` with
    ``extra.project`` set. We normalise back to the YAML parser's shape
    (``include_type="project"``, ``location="<project>:<file>"``) so the
    lint and raw paths produce equivalent GitLabCIInclude nodes.
    """
    lint_includes = [
        {
            "type": "file",
            "location": "/templates/build.yml",
            "extra": {
                "project": "my-org/shared-ci",
                "ref": "a" * 40,
            },
        },
        {
            "type": "file",
            "location": "/templates/deploy.yml",
            "extra": {
                "project": "my-org/shared-ci",
                "ref": "main",
            },
        },
    ]
    parsed = parse_lint_includes(lint_includes)

    assert [(p.include_type, p.location, p.is_pinned) for p in parsed] == [
        ("project", "my-org/shared-ci:/templates/build.yml", True),
        ("project", "my-org/shared-ci:/templates/deploy.yml", False),
    ]


def test_parse_lint_includes_keeps_non_project_types_unchanged():
    """Non-``file`` types (local/remote/template/component) pass through as-is."""
    lint_includes = [
        {"type": "local", "location": "/templates/local.yml"},
        {"type": "remote", "location": "https://example.com/foo.yml"},
        {"type": "template", "location": "Auto-DevOps.gitlab-ci.yml"},
    ]
    parsed = parse_lint_includes(lint_includes)
    assert [(p.include_type, p.location, p.is_local) for p in parsed] == [
        ("local", "/templates/local.yml", True),
        ("remote", "https://example.com/foo.yml", False),
        ("template", "Auto-DevOps.gitlab-ci.yml", False),
    ]


def test_is_pinned_logic():
    # Local: always pinned
    assert _is_pinned("local", None, "/foo.yml") is True
    # Project with SHA: pinned
    assert _is_pinned("project", "a" * 40, "loc") is True
    # Project with branch: not pinned
    assert _is_pinned("project", "main", "loc") is False
    assert _is_pinned("project", None, "loc") is False
    # Remote with SHA in path: pinned
    assert (
        _is_pinned(
            "remote",
            None,
            "https://example.com/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/file.yml",
        )
        is True
    )
    # Remote without SHA: not pinned
    assert _is_pinned("remote", None, "https://example.com/templates/foo.yml") is False
    # Template / component: never pinned
    assert _is_pinned("template", None, "Auto-DevOps.gitlab-ci.yml") is False
    assert _is_pinned("component", None, "comp/foo@1") is False
