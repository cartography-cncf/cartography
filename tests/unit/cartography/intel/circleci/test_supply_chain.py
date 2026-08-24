from datetime import datetime
from datetime import timezone

from cartography.intel.circleci.supply_chain import _run_older_than
from cartography.intel.circleci.supply_chain import build_revision_targets
from cartography.intel.circleci.supply_chain import CIRCLECI_TAG_REVISION_CONFIDENCE
from cartography.intel.circleci.supply_chain import images_with_feed_evidence
from cartography.intel.circleci.supply_chain import match_tag_revisions

FULL_SHA = "a" * 40
REPO_URL = "https://github.com/acme/app"

GH_APP = (REPO_URL, "github", "gh/acme/app")


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


def _target_row(digest, target):
    repo_url, provider, project_slug = target
    return {
        "image_digest": digest,
        "repo_url": repo_url,
        "provider": provider,
        "project_slug": project_slug,
        "match_method": "circleci_tag_revision",
        "confidence": CIRCLECI_TAG_REVISION_CONFIDENCE,
    }


def test_build_revision_targets_normalizes_and_keeps_all():
    runs = [
        _run(FULL_SHA, "git@github.com:acme/app.git", "GitHub", "gh/acme/app"),
        # Same SHA, different repo -> kept as a second target (ambiguity resolved at match).
        _run(FULL_SHA, "https://github.com/acme/fork", "GitHub", "gh/acme/fork"),
        # Bitbucket has no target schema -> dropped.
        _run("b" * 40, "https://bitbucket.org/acme/x", "Bitbucket", "bb/acme/x"),
        # Missing revision -> dropped.
        _run("", "https://github.com/acme/y", "GitHub", "gh/acme/y"),
    ]

    result = build_revision_targets(runs)

    assert result == {
        FULL_SHA: {GH_APP, ("https://github.com/acme/fork", "github", "gh/acme/fork")}
    }


def test_match_tag_revisions_exact():
    images = [{"digest": "sha256:1", "tags": [FULL_SHA]}]
    revision_targets = {FULL_SHA: {GH_APP}}

    assert match_tag_revisions(images, revision_targets) == [
        _target_row("sha256:1", GH_APP)
    ]


def test_match_tag_revisions_short_sha_prefix():
    images = [{"digest": "sha256:1", "tags": ["latest", FULL_SHA[:8]]}]
    revision_targets = {FULL_SHA: {GH_APP}}

    matches = match_tag_revisions(images, revision_targets)

    assert len(matches) == 1
    assert matches[0]["repo_url"] == REPO_URL


def test_match_tag_revisions_exact_ambiguous_skipped():
    # Same full SHA built from two repos -> ambiguous -> no edge.
    images = [{"digest": "sha256:1", "tags": [FULL_SHA]}]
    revision_targets = {
        FULL_SHA: {GH_APP, ("https://github.com/acme/fork", "github", "gh/acme/fork")}
    }

    assert match_tag_revisions(images, revision_targets) == []


def test_match_tag_revisions_prefix_collides_with_ambiguous_revision():
    # A short prefix matches a UNIQUE revision (rev_b) AND an AMBIGUOUS one (rev_a).
    # Resolving against the full multimap must treat the prefix as ambiguous, not match
    # rev_b's single target.
    rev_a = "abcdef0" + "1" * 33  # ambiguous: two repos
    rev_b = "abcdef0" + "2" * 33  # unique: one repo
    revision_targets = {
        rev_a: {
            ("https://github.com/acme/a", "github", "gh/acme/a"),
            ("https://github.com/acme/c", "github", "gh/acme/c"),
        },
        rev_b: {("https://github.com/acme/b", "github", "gh/acme/b")},
    }
    images = [{"digest": "sha256:1", "tags": ["abcdef0"]}]

    assert match_tag_revisions(images, revision_targets) == []


def test_match_tag_revisions_multiple_tags_to_different_repos_ambiguous():
    # Two SHA tags on one image resolve to different repos -> ambiguous, order-independent.
    sha_b = "b" * 40
    images = [{"digest": "sha256:1", "tags": [FULL_SHA, sha_b]}]
    revision_targets = {
        FULL_SHA: {GH_APP},
        sha_b: {("https://github.com/acme/b", "github", "gh/acme/b")},
    }

    assert match_tag_revisions(images, revision_targets) == []


def test_match_tag_revisions_no_match():
    images = [{"digest": "sha256:1", "tags": ["latest", "v1.2.3"]}]
    revision_targets = {FULL_SHA: {GH_APP}}

    assert match_tag_revisions(images, revision_targets) == []


def test_run_older_than():
    cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert _run_older_than({"created_at": "2025-12-31T23:00:00Z"}, cutoff) is True
    assert _run_older_than({"created_at": "2026-01-02T00:00:00Z"}, cutoff) is False
    # No/blank/unparseable timestamp is treated as within the window.
    assert _run_older_than({}, cutoff) is False
    assert _run_older_than({"created_at": "not-a-date"}, cutoff) is False


def test_images_with_feed_evidence_includes_ambiguous():
    # Ambiguous revisions still count as evidence for cleanup scoping.
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
