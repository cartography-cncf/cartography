from datetime import datetime
from datetime import timezone

from cartography.intel.circleci.supply_chain import _registry_namespace
from cartography.intel.circleci.supply_chain import _run_older_than
from cartography.intel.circleci.supply_chain import build_config_bindings
from cartography.intel.circleci.supply_chain import build_revision_repo_map
from cartography.intel.circleci.supply_chain import CIRCLECI_CONFIG_BINDING_CONFIDENCE
from cartography.intel.circleci.supply_chain import CIRCLECI_TAG_REVISION_CONFIDENCE
from cartography.intel.circleci.supply_chain import match_config_bindings
from cartography.intel.circleci.supply_chain import match_tag_revisions
from cartography.intel.circleci.supply_chain import parse_registry_destinations

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


def test_match_tag_revisions_exact():
    images = [{"digest": "sha256:1", "uri": "reg/acme/app", "tags": [FULL_SHA]}]
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
    images = [{"digest": "sha256:1", "uri": "reg/acme/app", "tags": ["latest", short]}]
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


def test_build_revision_repo_map_drops_ambiguous_sha():
    # Same SHA built from two different repos (fork/mirror) -> dropped, not last-wins.
    runs = [
        _run(FULL_SHA, "https://github.com/acme/app", "GitHub", "gh/acme/app", "p1"),
        _run(FULL_SHA, "https://github.com/acme/fork", "GitHub", "gh/acme/fork", "p2"),
        # A distinct, unambiguous SHA is still kept.
        _run("c" * 40, "https://github.com/acme/solo", "GitHub", "gh/acme/solo", "p3"),
    ]

    result = build_revision_repo_map(runs)

    assert FULL_SHA not in result
    assert result["c" * 40]["repo_url"] == "https://github.com/acme/solo"


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
    images = [{"digest": "sha256:1", "uri": "reg/acme/app", "tags": ["abcdef0"]}]

    assert match_tag_revisions(images, revision_map) == []


def test_match_tag_revisions_no_match():
    images = [
        {"digest": "sha256:1", "uri": "reg/acme/app", "tags": ["latest", "v1.2.3"]}
    ]
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
    # No/blank/unparseable timestamp is treated as within the window: it must never
    # truncate the feed nor (running inside stop_when) raise and abort the fetch.
    assert _run_older_than({}, cutoff) is False
    assert _run_older_than({"created_at": "not-a-date"}, cutoff) is False


def test_registry_namespace():
    assert (
        _registry_namespace("123456789.dkr.ecr.us-east-1.amazonaws.com/team/app:sha")
        == "123456789.dkr.ecr.us-east-1.amazonaws.com/team"
    )
    assert _registry_namespace("myorg/app@sha256:deadbeef") == "myorg"
    # Bare image name has no namespace to bind on.
    assert _registry_namespace("app") is None


def test_parse_registry_destinations():
    config = """
    steps:
      - run: docker build -t myorg/app:$TAG .
      - run: docker push myorg/app:latest
      - run: |
          docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/team/svc:1
    """

    assert parse_registry_destinations(config) == {
        "myorg",
        "123456789.dkr.ecr.us-east-1.amazonaws.com/team",
    }


def test_parse_registry_destinations_skips_variable_refs():
    assert parse_registry_destinations("docker push $IMAGE_REF") == set()


def test_build_config_bindings_singleton_and_ambiguous():
    runs = [
        _run(FULL_SHA, "https://github.com/acme/app", "GitHub", "gh/acme/app", "p1"),
        _run(
            "c" * 40, "https://github.com/acme/other", "GitHub", "gh/acme/other", "p2"
        ),
    ]
    configs = {
        # app pushes to two namespaces; one of them is also pushed to by 'other'.
        "p1": "docker push solo/app:1\ndocker push shared/x:1",
        "p2": "docker push shared/y:1",
    }

    namespace_binding, repo_meta = build_config_bindings(
        runs, lambda pid: configs.get(pid)
    )

    # 'solo' has a single repo -> bound. 'shared' has two repos -> dropped.
    assert namespace_binding == {"solo": "https://github.com/acme/app"}
    assert repo_meta["https://github.com/acme/app"] == {
        "provider": "github",
        "project_slug": "gh/acme/app",
    }


def test_match_config_bindings():
    images = [
        {"digest": "sha256:1", "uri": "solo/app:latest", "tags": []},
        {"digest": "sha256:2", "uri": "unbound/app:latest", "tags": []},
    ]
    namespace_binding = {"solo": REPO_URL}
    repo_meta = {REPO_URL: {"provider": "github", "project_slug": "gh/acme/app"}}

    matches = match_config_bindings(images, namespace_binding, repo_meta)

    assert matches == [
        {
            "image_digest": "sha256:1",
            "repo_url": REPO_URL,
            "provider": "github",
            "project_slug": "gh/acme/app",
            "match_method": "circleci_config_binding",
            "confidence": CIRCLECI_CONFIG_BINDING_CONFIDENCE,
        }
    ]
