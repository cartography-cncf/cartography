from datetime import datetime
from datetime import timezone

from cartography.intel.circleci.supply_chain import _run_older_than
from cartography.intel.circleci.supply_chain import build_revision_repo_map
from cartography.intel.circleci.supply_chain import CIRCLECI_TAG_REVISION_CONFIDENCE
from cartography.intel.circleci.supply_chain import collect_feed_revisions
from cartography.intel.circleci.supply_chain import images_with_feed_evidence
from cartography.intel.circleci.supply_chain import match_tag_revisions

FULL_SHA = "a" * 40
REPO_URL = "https://github.com/acme/app"


def _run(revision, repo_url, provider_name, project_slug, run_id="p1"):
    return {
        "id": run_id,
        "project_slug": project_slug,
        "vcs": {
            "provider_name": provider_name,
            "target_repository_url": repo_url,
            "revision": revision,
        },
    }


def test_build_revision_repo_map_normalizes_and_filters():
    runs = [
        _run(FULL_SHA, "git@github.com:acme/app.git", "GitHub", "gh/acme/app"),
        # Bitbucket has no target schema -> dropped.
        _run("b" * 40, "https://bitbucket.org/acme/x", "Bitbucket", "bb/acme/x"),
        # Missing revision -> dropped.
        _run("", "https://github.com/acme/y", "GitHub", "gh/acme/y"),
    ]

    result = build_revision_repo_map(runs)

    assert result == {
        FULL_SHA: {
            "repo_url": REPO_URL,
            "provider": "github",
            "project_slug": "gh/acme/app",
        }
    }


def test_build_revision_repo_map_drops_ambiguous_sha():
    # Same SHA built from two different repos (fork/mirror) -> dropped, not last-wins.
    runs = [
        _run(FULL_SHA, "https://github.com/acme/app", "GitHub", "gh/acme/app", "p1"),
        _run(FULL_SHA, "https://github.com/acme/fork", "GitHub", "gh/acme/fork", "p2"),
        _run("c" * 40, "https://github.com/acme/solo", "GitHub", "gh/acme/solo", "p3"),
    ]

    result = build_revision_repo_map(runs)

    assert FULL_SHA not in result
    assert result["c" * 40]["repo_url"] == "https://github.com/acme/solo"


def test_match_tag_revisions_exact():
    images = [{"digest": "sha256:1", "tags": [FULL_SHA]}]
    revision_map = {
        FULL_SHA: {
            "repo_url": REPO_URL,
            "provider": "github",
            "project_slug": "gh/acme/app",
        }
    }

    matches = match_tag_revisions(images, revision_map)

    assert matches == [
        {
            "image_digest": "sha256:1",
            "repo_url": REPO_URL,
            "provider": "github",
            "project_slug": "gh/acme/app",
            "match_method": "circleci_tag_revision",
            "confidence": CIRCLECI_TAG_REVISION_CONFIDENCE,
        }
    ]


def test_match_tag_revisions_short_sha_prefix():
    short = FULL_SHA[:8]
    images = [{"digest": "sha256:1", "tags": ["latest", short]}]
    revision_map = {
        FULL_SHA: {
            "repo_url": REPO_URL,
            "provider": "github",
            "project_slug": "gh/acme/app",
        }
    }

    matches = match_tag_revisions(images, revision_map)

    assert len(matches) == 1
    assert matches[0]["image_digest"] == "sha256:1"
    assert matches[0]["repo_url"] == REPO_URL


def test_match_tag_revisions_ambiguous_short_prefix_skipped():
    # Two full revisions share a 7-char prefix but resolve to different repos.
    rev_a = "abcdef0" + "1" * 33
    rev_b = "abcdef0" + "2" * 33
    revision_map = {
        rev_a: {
            "repo_url": "https://github.com/acme/a",
            "provider": "github",
            "project_slug": "gh/acme/a",
        },
        rev_b: {
            "repo_url": "https://github.com/acme/b",
            "provider": "github",
            "project_slug": "gh/acme/b",
        },
    }
    images = [{"digest": "sha256:1", "tags": ["abcdef0"]}]

    assert match_tag_revisions(images, revision_map) == []


def test_match_tag_revisions_no_match():
    images = [{"digest": "sha256:1", "tags": ["latest", "v1.2.3"]}]
    revision_map = {
        FULL_SHA: {
            "repo_url": REPO_URL,
            "provider": "github",
            "project_slug": "gh/acme/app",
        }
    }

    assert match_tag_revisions(images, revision_map) == []


def test_run_older_than():
    cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert _run_older_than({"created_at": "2025-12-31T23:00:00Z"}, cutoff) is True
    assert _run_older_than({"created_at": "2026-01-02T00:00:00Z"}, cutoff) is False
    # No/blank/unparseable timestamp is treated as within the window.
    assert _run_older_than({}, cutoff) is False
    assert _run_older_than({"created_at": "not-a-date"}, cutoff) is False


def test_collect_feed_revisions_includes_ambiguous():
    # Ambiguous revisions are dropped from the unique map but still count as evidence.
    runs = [
        _run(FULL_SHA, "https://github.com/acme/app", "GitHub", "gh/acme/app", "p1"),
        _run(FULL_SHA, "https://github.com/acme/fork", "GitHub", "gh/acme/fork", "p2"),
    ]
    assert collect_feed_revisions(runs) == {FULL_SHA}
    assert build_revision_repo_map(runs) == {}


def test_images_with_feed_evidence():
    feed_revisions = {FULL_SHA}
    images = [
        {"digest": "sha256:matched", "tags": [FULL_SHA]},
        {"digest": "sha256:prefix", "tags": [FULL_SHA[:9]]},
        {"digest": "sha256:none", "tags": ["latest", "b" * 40]},
    ]

    assert images_with_feed_evidence(images, feed_revisions) == {
        "sha256:matched",
        "sha256:prefix",
    }
