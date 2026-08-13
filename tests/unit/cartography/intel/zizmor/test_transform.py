"""
Unit tests for the zizmor JSON v1 transform.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from cartography.intel.zizmor.transform import _build_action_id
from cartography.intel.zizmor.transform import _extract_uses_reference
from cartography.intel.zizmor.transform import _format_route
from cartography.intel.zizmor.transform import _looks_like_uses_reference
from cartography.intel.zizmor.transform import _normalize_workflow_path
from cartography.intel.zizmor.transform import looks_like_zizmor_report
from cartography.intel.zizmor.transform import transform_zizmor_report

REPO_CONTEXT = {
    "owner": "simpsoncorp",
    "repo": "sample_repo",
    "repositoryName": "simpsoncorp/sample_repo",
    "repositoryUrl": "https://github.com/simpsoncorp/sample_repo",
    "branch": "main",
}


def _load_sample() -> list[dict]:
    return json.loads(Path("tests/data/zizmor/zizmor_report.json").read_text())


def _by_route(rows: list[dict], route: str) -> dict:
    return next(row for row in rows if row["yaml_route"] == route)


def _location(route: list[dict], feature: str, kind: str = "Primary") -> dict:
    return {
        "symbolic": {
            "key": {"Local": {"verbatim_path": "./.github/workflows/ci.yml"}},
            "annotation": "an annotation",
            "route": {"route": route},
            "feature_kind": "Normal",
            "kind": kind,
        },
        "concrete": {
            "location": {
                "start_point": {"row": 0, "column": 0},
                "end_point": {"row": 0, "column": 1},
            },
            "feature": feature,
            "comments": [],
        },
    }


# =============================================================================
# looks_like_zizmor_report
# =============================================================================


def test_looks_like_zizmor_report_accepts_sample():
    assert looks_like_zizmor_report(_load_sample()) is True


def test_looks_like_zizmor_report_accepts_empty_list():
    assert looks_like_zizmor_report([]) is True


def test_looks_like_zizmor_report_rejects_object():
    document = json.loads(Path("tests/data/zizmor/non_zizmor_report.json").read_text())
    assert looks_like_zizmor_report(document) is False


def test_looks_like_zizmor_report_rejects_list_of_wrong_shape():
    assert looks_like_zizmor_report([{"foo": "bar"}]) is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("ident", None),
        ("ident", 42),
        ("desc", 123),
        ("url", None),
        ("determinations", "not-a-dict"),
        ("locations", "not-a-list"),
    ],
)
def test_looks_like_zizmor_report_rejects_wrong_field_types(field, value):
    """
    Presence alone is not enough. A null `ident` would be stringified into a
    synthetic "None" audit, which both invents a finding and changes the id of
    the real one, so cleanup would delete the real one as stale.
    """
    finding = _load_sample()[0]
    finding[field] = value

    assert looks_like_zizmor_report([finding]) is False


def test_looks_like_zizmor_report_rejects_corruption_past_the_first_entry():
    """
    Checking only the opening element would let a truncated report through, and
    the entries the transform could not read would then be cleaned up as though
    they had been fixed.
    """
    assert looks_like_zizmor_report(_load_sample() + [{"malformed": True}]) is False


# =============================================================================
# _normalize_workflow_path
# =============================================================================


@pytest.mark.parametrize(
    "key,expected",
    [
        (
            {"Local": {"verbatim_path": "./.github/workflows/ci.yml"}},
            ".github/workflows/ci.yml",
        ),
        (
            {"Local": {"verbatim_path": ".github/workflows/ci.yml"}},
            ".github/workflows/ci.yml",
        ),
        # Absolute paths are refused: nothing in the report says where the
        # repository root is, so they cannot be made repository-relative.
        (
            {
                "Local": {
                    "verbatim_path": "/home/runner/work/repo/repo/.github/workflows/ci.yml"
                }
            },
            None,
        ),
        # A repository named `.github` is why guessing the root cannot work: no
        # rule picking a `.github/` segment is right for both this and the above.
        (
            {
                "Local": {
                    "verbatim_path": "/home/runner/work/.github/.github/.github/workflows/ci.yml"
                }
            },
            None,
        ),
        (
            {"Local": {"verbatim_path": "/home/runner/work/repo/repo/action.yml"}},
            None,
        ),
        (
            {"Local": {"verbatim_path": "../other/.github/workflows/ci.yml"}},
            None,
        ),
        (
            {
                "Remote": {
                    "slug": {"owner": "o", "repo": "r", "git_ref": None},
                    "path": ".github/workflows/deploy.yml",
                }
            },
            ".github/workflows/deploy.yml",
        ),
        # A non-workflow input such as a Dependabot config keeps its relative path.
        (
            {"Local": {"verbatim_path": "./action.yml"}},
            "action.yml",
        ),
        ({"Stdin": {}}, None),
        ({"Local": {"verbatim_path": "   "}}, None),
        ("not-a-dict", None),
    ],
)
def test_normalize_workflow_path(key, expected):
    assert _normalize_workflow_path(key) == expected


# =============================================================================
# _extract_uses_reference and _build_action_id
# =============================================================================


def test_extract_uses_reference_from_primary_location():
    locations = [
        _location(
            [
                {"Key": "jobs"},
                {"Key": "a"},
                {"Key": "steps"},
                {"Index": 0},
                {"Key": "uses"},
            ],
            "uses: actions/checkout@v4",
        )
    ]
    assert _extract_uses_reference(locations) == "actions/checkout@v4"


def test_extract_uses_reference_from_related_location():
    locations = [
        _location(
            [{"Key": "jobs"}, {"Key": "a"}, {"Key": "steps"}, {"Index": 0}],
            "uses: actions/checkout@v4",
            kind="Primary",
        ),
        _location(
            [
                {"Key": "jobs"},
                {"Key": "a"},
                {"Key": "steps"},
                {"Index": 0},
                {"Key": "uses"},
            ],
            "actions/checkout@v4",
            kind="Related",
        ),
    ]
    assert _extract_uses_reference(locations) == "actions/checkout@v4"


@pytest.mark.parametrize(
    "feature,expected",
    [
        ("uses: actions/checkout@v4", "actions/checkout@v4"),
        ("actions/checkout@v4", "actions/checkout@v4"),
        ("uses: './.github/actions/build'", "./.github/actions/build"),
        ("uses: docker://alpine:3.8", "docker://alpine:3.8"),
        # A KeyOnly location carries only the key, not the value.
        ("uses", None),
    ],
)
def test_extract_uses_reference_feature_forms(feature, expected):
    locations = [_location([{"Key": "jobs"}, {"Key": "uses"}], feature)]
    assert _extract_uses_reference(locations) == expected


def test_extract_uses_reference_is_none_for_run_block():
    locations = [
        _location(
            [
                {"Key": "jobs"},
                {"Key": "a"},
                {"Key": "steps"},
                {"Index": 0},
                {"Key": "run"},
            ],
            'echo "hello"',
        )
    ]
    assert _extract_uses_reference(locations) is None


def test_extract_uses_reference_prefers_a_complete_reference_over_a_fragment():
    """
    `ref-version-mismatch` makes the version comment its primary location, so
    that location's feature is just `v3` while a related one holds the whole
    reference. Building an action id from `v3` loses the AFFECTS edge.

    This is real `zizmor --persona=pedantic` output.
    """
    document = json.loads(
        Path("tests/data/zizmor/zizmor_report_ref_version_mismatch.json").read_text()
    )
    visible = [
        location
        for location in document[0]["locations"]
        if location["symbolic"]["kind"] != "Hidden"
    ]
    primaries = [loc for loc in visible if loc["symbolic"]["kind"] == "Primary"]
    related = [loc for loc in visible if loc["symbolic"]["kind"] != "Primary"]
    # Both are routed at the same `uses` key, and the transform looks at the
    # primary first, which here carries only the version comment.
    assert primaries[0]["concrete"]["feature"] == "v3"
    assert _format_route(primaries[0]["symbolic"]).endswith(".uses")

    assert (
        _extract_uses_reference([*primaries, *related])
        == "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
    )


def test_transform_zizmor_report_resolves_action_for_ref_version_mismatch():
    document = json.loads(
        Path("tests/data/zizmor/zizmor_report_ref_version_mismatch.json").read_text()
    )

    rows = transform_zizmor_report(document, REPO_CONTEXT).rows

    assert len(rows) == 1
    assert rows[0]["audit_id"] == "ref-version-mismatch"
    assert (
        rows[0]["action_id"]
        == "simpsoncorp:actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"
    )


@pytest.mark.parametrize(
    "candidate,expected",
    [
        ("actions/checkout@v4", True),
        ("actions/checkout", True),
        ("octo-org/repo/.github/workflows/wf.yml@v1", True),
        ("./.github/actions/build", True),
        ("docker://alpine:3.8", True),
        # Fragments of a reference, not a reference.
        ("v3", False),
        ("", False),
        ("/leading-slash", False),
    ],
)
def test_looks_like_uses_reference(candidate, expected):
    assert _looks_like_uses_reference(candidate) is expected


def test_build_action_id_matches_github_module():
    assert (
        _build_action_id("simpsoncorp", "sample_repo", "actions/checkout@v4")
        == "simpsoncorp:actions/checkout@v4"
    )
    assert (
        _build_action_id("simpsoncorp", "sample_repo", "./.github/actions/build")
        == "simpsoncorp/sample_repo:./.github/actions/build"
    )


# =============================================================================
# transform_zizmor_report
# =============================================================================


def test_transform_zizmor_report_empty_document():
    assert transform_zizmor_report([], REPO_CONTEXT).rows == []


def test_transform_zizmor_report_emits_one_row_per_finding():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    assert len(rows) == 5


def test_transform_zizmor_report_uses_primary_location_and_drops_hidden():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    finding = _by_route(rows, "jobs.greet.steps.0.run")

    assert finding["audit_id"] == "template-injection"
    assert finding["annotation"] == "may expand into attacker-controllable code"
    # The Hidden location spans rows 6-7; the Primary one is row 6 only.
    assert finding["snippet"] == 'echo "Hello ${{ github.event.issue.title }}"'


def test_transform_zizmor_report_converts_to_one_based_positions():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    finding = _by_route(rows, "jobs.greet.steps.0.run")

    # Zizmor reports row 6, column 29 to row 6, column 53, zero-based.
    assert finding["start_line"] == 7
    assert finding["start_col"] == 30
    assert finding["end_line"] == 7
    assert finding["end_col"] == 54


def test_transform_zizmor_report_normalizes_case():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    finding = _by_route(rows, "jobs.greet.steps.0.run")

    assert finding["severity"] == "high"
    assert finding["confidence"] == "high"
    assert finding["persona"] == "regular"
    assert finding["fix_titles"] == ["replace expression with environment variable"]
    assert finding["fix_dispositions"] == ["unsafe"]


def test_transform_zizmor_report_keeps_ignored_findings():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    finding = _by_route(rows, "permissions")

    assert finding["audit_id"] == "excessive-permissions"
    assert finding["ignored"] is True
    # Absolute verbatim_path is cut down to the repository-relative path.
    assert finding["file_path"] == ".github/workflows/deploy.yml"


def test_transform_zizmor_report_resolves_action_for_uses_findings():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows

    remote_action = _by_route(rows, "jobs.greet.steps.1")
    assert remote_action["uses_reference"] == "actions/checkout@v4"
    assert remote_action["action_id"] == "simpsoncorp:actions/checkout@v4"

    local_action = _by_route(rows, "jobs.greet.steps.2.uses")
    assert local_action["uses_reference"] == "./.github/actions/build"
    assert (
        local_action["action_id"] == "simpsoncorp/sample_repo:./.github/actions/build"
    )


def test_transform_zizmor_report_emits_a_row_per_primary_location():
    """
    Several audits report more than one primary location. `undocumented-permissions`
    emits one per undocumented permission key, and each is a separate problem.
    """
    finding = {
        "ident": "undocumented-permissions",
        "desc": "undocumented permission",
        "url": "https://docs.zizmor.sh/audits/#undocumented-permissions",
        "determinations": {
            "confidence": "High",
            "severity": "Low",
            "persona": "Pedantic",
        },
        "locations": [
            _location([{"Key": "permissions"}, {"Key": "issues"}], "issues: write"),
            _location(
                [{"Key": "permissions"}, {"Key": "pull-requests"}],
                "pull-requests: write",
            ),
        ],
        "ignored": False,
        "fixes": [],
    }

    rows = transform_zizmor_report([finding], REPO_CONTEXT).rows

    assert {row["yaml_route"] for row in rows} == {
        "permissions.issues",
        "permissions.pull-requests",
    }
    assert len({row["id"] for row in rows}) == 2


def test_transform_zizmor_report_scopes_uses_extraction_to_each_primary():
    """
    A related `uses` location belongs to the finding, so it applies to every
    primary; a primary that is itself a `uses` must not leak into the others.
    """
    finding = {
        "ident": "undocumented-permissions",
        "desc": "undocumented permission",
        "url": "https://docs.zizmor.sh/audits/#undocumented-permissions",
        "determinations": {
            "confidence": "High",
            "severity": "Low",
            "persona": "Pedantic",
        },
        "locations": [
            _location([{"Key": "permissions"}, {"Key": "issues"}], "issues: write"),
            _location(
                [{"Key": "jobs"}, {"Key": "a"}, {"Key": "uses"}],
                "uses: actions/checkout@v4",
                kind="Related",
            ),
        ],
        "ignored": False,
        "fixes": [],
    }

    rows = transform_zizmor_report([finding], REPO_CONTEXT).rows

    assert len(rows) == 1
    assert rows[0]["uses_reference"] == "actions/checkout@v4"


def test_transform_zizmor_report_leaves_action_unset_for_non_uses_findings():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    finding = _by_route(rows, "jobs.greet.steps.0.run")

    assert finding["uses_reference"] is None
    assert finding["action_id"] is None


def test_transform_zizmor_report_handles_remote_input_key():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    finding = _by_route(rows, "jobs.publish.steps.0.uses")

    assert finding["audit_id"] == "impostor-commit"
    assert finding["file_path"] == ".github/workflows/deploy.yml"


def test_transform_zizmor_report_carries_repository_context():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    for row in rows:
        assert row["repositoryName"] == "simpsoncorp/sample_repo"
        assert row["repositoryUrl"] == "https://github.com/simpsoncorp/sample_repo"
        assert row["branch"] == "main"


def test_transform_zizmor_report_ids_are_unique():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    assert len({row["id"] for row in rows}) == len(rows)


def test_transform_zizmor_report_id_is_stable_across_line_shifts():
    """Adding lines above a finding must not mint a new node."""
    document = _load_sample()
    before = transform_zizmor_report(document, REPO_CONTEXT).rows

    for finding in document:
        for location in finding["locations"]:
            concrete_location = location["concrete"]["location"]
            concrete_location["start_point"]["row"] += 10
            concrete_location["end_point"]["row"] += 10
    after = transform_zizmor_report(document, REPO_CONTEXT).rows

    assert [row["id"] for row in before] == [row["id"] for row in after]


def test_transform_zizmor_report_id_differs_across_repositories():
    rows = transform_zizmor_report(_load_sample(), REPO_CONTEXT).rows
    other_rows = transform_zizmor_report(
        _load_sample(),
        {**REPO_CONTEXT, "repositoryUrl": "https://github.com/other/other"},
    ).rows

    assert {row["id"] for row in rows}.isdisjoint({row["id"] for row in other_rows})


def test_transform_zizmor_report_skips_stdin_findings_and_counts_them():
    """
    A stdin finding is well-formed but has nothing to join to. It must be
    reported as skipped so the caller knows the repository was not fully
    observed and holds off on cleanup.
    """
    document = _load_sample()[:1]
    document[0]["locations"][1]["symbolic"]["key"] = {"Stdin": {}}

    result = transform_zizmor_report(document, REPO_CONTEXT)

    assert result.rows == []
    assert result.skipped == 1


def test_transform_zizmor_report_reports_nothing_skipped_on_a_clean_report():
    assert transform_zizmor_report(_load_sample(), REPO_CONTEXT).skipped == 0


def test_transform_zizmor_report_rejects_malformed_entry():
    """
    A corrupt entry must fail the report rather than be dropped: a silently
    dropped finding looks like a fixed one, and cleanup would delete it.
    """
    document = _load_sample() + [{"malformed": True}]

    with pytest.raises(
        ValueError, match="Zizmor report contains an entry that is not a finding"
    ):
        transform_zizmor_report(document, REPO_CONTEXT)


@pytest.mark.parametrize(
    "field,value",
    [
        ("ident", None),
        ("desc", 123),
        ("url", None),
        ("determinations", "not-a-dict"),
        ("locations", "not-a-list"),
    ],
)
def test_transform_zizmor_report_rejects_wrong_field_types(field, value):
    """
    The transform must reject the same entries the validator does, so a report
    can never be counted as fully observed while a finding in it was dropped.
    """
    finding = _load_sample()[0]
    finding[field] = value

    with pytest.raises(
        ValueError, match="Zizmor report contains an entry that is not a finding"
    ):
        transform_zizmor_report([finding], REPO_CONTEXT)


@pytest.mark.parametrize(
    "location",
    [
        "not-a-location",
        {"concrete": {}},
        {"symbolic": "not-a-dict", "concrete": {}},
        {"symbolic": {}, "concrete": "not-a-dict"},
    ],
)
def test_transform_zizmor_report_rejects_malformed_locations(location):
    """
    Dropping a malformed location silently costs whatever it carried, such as
    the `uses` location that resolves the action, while the finding still looks
    complete enough for its report to authorize cleanup.
    """
    finding = _load_sample()[1]
    finding["locations"].append(location)

    assert looks_like_zizmor_report([finding]) is False
    with pytest.raises(
        ValueError, match="Zizmor report contains an entry that is not a finding"
    ):
        transform_zizmor_report([finding], REPO_CONTEXT)


def test_transform_zizmor_report_skips_findings_with_absolute_paths():
    """
    An absolute path cannot be made repository-relative, so it would match no
    workflow. It is skipped and counted, which withholds cleanup.
    """
    finding = _load_sample()[0]
    for location in finding["locations"]:
        location["symbolic"]["key"] = {
            "Local": {"verbatim_path": "/home/runner/work/repo/repo/.github/wf.yml"}
        }

    result = transform_zizmor_report([finding], REPO_CONTEXT)

    assert result.rows == []
    assert result.skipped == 1


def test_transform_zizmor_report_rejects_non_list_document():
    # A zizmor report is a bare array. An object here means the caller passed
    # something else, such as a SARIF report or another scanner's output.
    document: Any = {"findings": []}
    with pytest.raises(
        ValueError, match="Zizmor report must be a top-level list of findings."
    ):
        transform_zizmor_report(document, REPO_CONTEXT)
