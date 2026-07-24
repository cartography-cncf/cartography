import logging
import re
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.intel.circleci.util import _TIMEOUT
from cartography.intel.circleci.util import paginated_get
from cartography.intel.circleci.util import parse_iso
from cartography.intel.supply_chain import normalize_vcs_url
from cartography.models.circleci.packaged_matchlink import (
    CircleCIGitHubRepoPackagedFromMatchLink,
)
from cartography.models.circleci.packaged_matchlink import (
    CircleCIGitLabProjectPackagedFromMatchLink,
)
from cartography.models.circleci.packaged_matchlink import (
    ImagePackagedByCircleCIProjectMatchLink,
)
from cartography.util import timeit

logger = logging.getLogger(__name__)

# Fallback rungs run below the SLSA-provenance / Dockerfile-analysis / package-owner
# ladder. Confidence values are data (consumers filter at their own threshold) and are
# tunable: tag=SHA resolves a specific image (medium); config binding is namespace-wide
# (low). Both sit below the GHCR package_owner_repo rung (0.6).
CIRCLECI_TAG_REVISION_CONFIDENCE = 0.5
CIRCLECI_CONFIG_BINDING_CONFIDENCE = 0.25

# The /pipeline feed is time-bounded rather than page-bounded: it returns runs
# newest-first, so we page until a run older than the lookback window, then stop. This
# gives a meaningful "recent builds" window (mirrors the CloudTrail lookback pattern)
# instead of an arbitrary page count. _MAX_FEED_PAGES is only a runaway-pagination guard.
_FEED_LOOKBACK_DAYS = 30
_MAX_FEED_PAGES = 100

_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
# docker push <ref> and docker build ... -t <ref>: the two shapes that name a push
# destination in a CircleCI config's shell steps.
_DOCKER_PUSH_RE = re.compile(r"docker\s+push\s+(\S+)")
_DOCKER_BUILD_TAG_RE = re.compile(r"docker\s+build\b[^\n]*?-t\s+(\S+)")


def _normalize_provider(vcs: dict[str, Any], repo_url: str) -> str | None:
    """
    Resolve a CircleCI vcs block to one of the providers we can target ("github" or
    "gitlab"). Falls back to the repo URL host when provider_name is absent. Returns None
    for providers with no PACKAGED_FROM target schema (e.g. Bitbucket).
    """
    name = (vcs.get("provider_name") or "").lower()
    host = repo_url.lower()
    if "github" in name or "github.com" in host:
        return "github"
    if "gitlab" in name or "gitlab.com" in host:
        return "gitlab"
    return None


def _is_probable_sha(value: str) -> bool:
    return bool(_SHA_RE.match(value))


def _run_older_than(run: dict[str, Any], cutoff: datetime) -> bool:
    """
    True if a pipeline-feed run's created_at is strictly before the cutoff. Runs with a
    missing or unparseable created_at are treated as within the window (kept, and do not
    stop paging), so a bad timestamp never silently truncates nor, since this runs inside
    stop_when, aborts the whole feed fetch.
    """
    try:
        created = parse_iso(run.get("created_at"))
    except (ValueError, TypeError):
        return False
    if created is None:
        return False
    return created < cutoff


def _registry_namespace(reference: str) -> str | None:
    """
    Reduce a full image reference to its registry namespace (everything up to, but not
    including, the leaf image name), stripping any tag or digest. The namespace is the
    grouping key for the config-binding rung: sibling images pushed under the same
    namespace inherit the same repo.

    Examples:
      123456789.dkr.ecr.us-east-1.amazonaws.com/team/app:sha -> 123456789.dkr.ecr.us-east-1.amazonaws.com/team
      myorg/app@sha256:...                                   -> myorg
      app                                                    -> None (bare name, too ambiguous)
    """
    if not reference:
        return None
    ref = reference.strip()
    # Strip digest first, then tag on the final path segment.
    ref = ref.split("@", 1)[0]
    segments = ref.split("/")
    if len(segments) < 2:
        return None
    # The tag colon only applies to the leaf segment (host may contain a port colon).
    leaf = segments[-1].split(":", 1)[0]
    if not leaf:
        return None
    return "/".join(segments[:-1])


@timeit
def get_unmatched_circleci_candidate_images(
    neo4j_session: neo4j.Session,
    org_id: str,
    update_tag: int,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Query container images not yet matched to a code repository in this sync iteration,
    returning each image's digest, uri, and the full set of its tag names.

    Cross-provider gating is implicit: images that already received a PACKAGED_FROM this
    run (e.g. from the GitHub/GitLab provenance or Dockerfile rungs, which run earlier in
    the sync, or from an earlier CircleCI rung) are excluded. Images with only a stale
    PACKAGED_FROM from a prior iteration are included so they can be re-matched. The second
    clause skips images already claimed by a different CircleCI org.

    :param neo4j_session: Neo4j session
    :param org_id: CircleCI organization id used for scoping
    :param update_tag: The current sync update tag
    :param limit: Optional cap on the number of images returned
    :return: List of {"digest", "uri", "tags": [tag name, ...]} dicts
    """
    query = """
        MATCH (img:Image)<-[:IMAGE]-(t:ImageTag)<-[:REPO_IMAGE]-(repo:ContainerRegistry)
        WHERE NOT exists((img)-[:PACKAGED_FROM {lastupdated: $update_tag}]->())
          AND (
              NOT exists((img)-[:PACKAGED_FROM {_sub_resource_label: 'CircleCIOrganization'}]->())
              OR exists((
                  img
              )-[:PACKAGED_FROM {
                  _sub_resource_label: 'CircleCIOrganization',
                  _sub_resource_id: $org_id
              }]->())
          )
        WITH img,
             [u IN collect(DISTINCT t.uri) WHERE u IS NOT NULL] AS tag_uris,
             collect(DISTINCT t.name) AS tags
        // Prefer the image's own uri, else a tag reference. ECR images (AWSECRImage) carry
        // no uri, so the ImageTag uri is what lets _registry_namespace recover the registry
        // namespace for the config-binding rung.
        RETURN img.digest AS digest,
               coalesce(img.uri, head(tag_uris), img.digest) AS uri,
               tags
    """
    if limit:
        query += f" LIMIT {limit}"

    result = neo4j_session.run(query, update_tag=update_tag, org_id=org_id)
    images = [
        {
            "digest": record["digest"],
            "uri": record["uri"] or "",
            "tags": [t for t in (record["tags"] or []) if t],
        }
        for record in result
    ]
    logger.info(
        "Found %d unmatched candidate image(s) for CircleCI org %s",
        len(images),
        org_id,
    )
    return images


@timeit
def get_pipeline_runs(
    api_session: requests.Session,
    base_url: str,
    org_slug: str,
    lookback_days: int = _FEED_LOOKBACK_DAYS,
) -> list[dict[str, Any]]:
    """
    Fetch pipeline runs built within the lookback window from the /pipeline feed. The feed
    is newest-first, so we stop paging as soon as a run predates the cutoff, then drop any
    older stragglers from the final (boundary) page. These are high-volume ephemeral CI
    telemetry, consumed transiently in memory and never loaded as graph nodes.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    runs = paginated_get(
        api_session,
        f"{base_url}/pipeline",
        params={"org-slug": org_slug},
        max_pages=_MAX_FEED_PAGES,
        stop_when=lambda run: _run_older_than(run, cutoff),
    )
    return [run for run in runs if not _run_older_than(run, cutoff)]


def build_revision_repo_map(runs: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """
    Build {revision_sha -> {"repo_url", "provider", "project_slug"}} from pipeline-feed
    runs. Only github/gitlab-backed runs with a revision and repo URL are kept; the repo
    URL is normalized to the canonical HTTPS form used by GitHubRepository.id /
    GitLabProject.web_url.

    A revision is dropped when it resolves to more than one distinct target (a commit
    shared across forks/mirrors would otherwise attribute an image to an arbitrary repo).
    Only revisions with a unique target are retained.
    """
    candidates: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for run in runs:
        vcs = run.get("vcs") or {}
        revision = (vcs.get("revision") or "").strip().lower()
        raw_url = vcs.get("target_repository_url") or vcs.get("origin_repository_url")
        project_slug = run.get("project_slug")
        if not revision or not raw_url or not project_slug:
            continue
        repo_url = normalize_vcs_url(raw_url)
        provider = _normalize_provider(vcs, repo_url)
        if provider is None:
            continue
        candidates[revision].add((repo_url, provider, project_slug))

    revision_map: dict[str, dict[str, str]] = {}
    for revision, targets in candidates.items():
        if len(targets) != 1:
            continue
        repo_url, provider, project_slug = next(iter(targets))
        revision_map[revision] = {
            "repo_url": repo_url,
            "provider": provider,
            "project_slug": project_slug,
        }
    return revision_map


def match_tag_revisions(
    images: list[dict[str, Any]],
    revision_map: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    """
    Match images whose tag name equals a known build revision (git SHA). Supports exact
    matches and short-SHA prefixes (a hex tag of length >= 7 that prefixes a known
    revision). Produces at most one row per image digest.

    revision_map already holds only revisions with a unique target. A short prefix is only
    accepted when every full revision it prefixes resolves to that same single target;
    prefixes matching two or more distinct targets are ambiguous and skipped.
    """
    matches: list[dict[str, Any]] = []
    for image in images:
        matched: dict[str, str] | None = None
        for raw_tag in image["tags"]:
            tag = raw_tag.strip().lower()
            if not _is_probable_sha(tag):
                continue
            if tag in revision_map:
                matched = revision_map[tag]
                break
            # Short-SHA: accept only if the prefix resolves to a single unique target.
            prefix_targets = {
                (meta["repo_url"], meta["provider"], meta["project_slug"])
                for rev, meta in revision_map.items()
                if len(tag) < len(rev) and rev.startswith(tag)
            }
            if len(prefix_targets) == 1:
                repo_url, provider, project_slug = next(iter(prefix_targets))
                matched = {
                    "repo_url": repo_url,
                    "provider": provider,
                    "project_slug": project_slug,
                }
                break
        if matched is None:
            continue
        matches.append(
            {
                "image_digest": image["digest"],
                "repo_url": matched["repo_url"],
                "provider": matched["provider"],
                "project_slug": matched["project_slug"],
                "match_method": "circleci_tag_revision",
                "confidence": CIRCLECI_TAG_REVISION_CONFIDENCE,
            }
        )
    return matches


def parse_registry_destinations(config_yaml: str) -> set[str]:
    """
    Extract the registry namespaces a CircleCI config pushes images to. Heuristic and
    conservative: scans compiled config text for `docker push <ref>` and
    `docker build ... -t <ref>` shell steps and reduces each reference to its namespace.
    Unparseable configs simply yield nothing and the image falls through to no match.
    """
    if not config_yaml:
        return set()
    namespaces: set[str] = set()
    for pattern in (_DOCKER_PUSH_RE, _DOCKER_BUILD_TAG_RE):
        for ref in pattern.findall(config_yaml):
            # Ignore shell/variable-only references that won't resolve to a real registry.
            if "$" in ref:
                continue
            namespace = _registry_namespace(ref)
            if namespace:
                namespaces.add(namespace)
    return namespaces


def build_config_bindings(
    runs: list[dict[str, Any]],
    fetch_config: Any,
) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """
    Build {registry_namespace -> repo_url} bindings from per-run configs, keeping a
    namespace only when exactly one repo pushes to it (singleton discipline).

    ACCEPTED LIMITATION: uniqueness here means "only one repo was observed pushing to this
    namespace across the runs we fetched", not "only one repo pushes to it". The /pipeline
    feed is a time-bounded, partial view (recently-built followed projects only; CircleCI
    API v2 has no list-projects endpoint), so a project outside the lookback window that
    pushes to the same namespace is invisible and the namespace can be mis-bound to the
    wrong repo. This is why config_binding is the lowest-confidence rung
    (CIRCLECI_CONFIG_BINDING_CONFIDENCE): consumers filter on confidence, and the specific
    tag_revision rung (which cannot mis-attribute) is preferred and applied first.

    :param runs: pipeline-feed runs (deduped to one per project by the caller)
    :param fetch_config: callable(pipeline_id) -> config YAML string or None
    :return: ({namespace -> repo_url}, {repo_url -> {"provider", "project_slug"}})
    """
    namespace_to_repos: dict[str, set[str]] = defaultdict(set)
    repo_meta: dict[str, dict[str, str]] = {}

    for run in runs:
        vcs = run.get("vcs") or {}
        raw_url = vcs.get("target_repository_url") or vcs.get("origin_repository_url")
        project_slug = run.get("project_slug")
        pipeline_id = run.get("id")
        if not raw_url or not project_slug or not pipeline_id:
            continue
        repo_url = normalize_vcs_url(raw_url)
        provider = _normalize_provider(vcs, repo_url)
        if provider is None:
            continue

        config_yaml = fetch_config(pipeline_id)
        namespaces = parse_registry_destinations(config_yaml or "")
        if not namespaces:
            continue
        repo_meta[repo_url] = {"provider": provider, "project_slug": project_slug}
        for namespace in namespaces:
            namespace_to_repos[namespace].add(repo_url)

    namespace_binding = {
        namespace: next(iter(repos))
        for namespace, repos in namespace_to_repos.items()
        if len(repos) == 1
    }
    return namespace_binding, repo_meta


def match_config_bindings(
    images: list[dict[str, Any]],
    namespace_binding: dict[str, str],
    repo_meta: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    """
    Match residual images to a repo when the image's registry namespace has a singleton
    config binding. Namespace-wide, low confidence (see build_config_bindings for the
    accepted mis-attribution limitation on a partial feed).
    """
    matches: list[dict[str, Any]] = []
    for image in images:
        namespace = _registry_namespace(image["uri"])
        if namespace is None:
            continue
        repo_url = namespace_binding.get(namespace)
        if repo_url is None:
            continue
        meta = repo_meta[repo_url]
        matches.append(
            {
                "image_digest": image["digest"],
                "repo_url": repo_url,
                "provider": meta["provider"],
                "project_slug": meta["project_slug"],
                "match_method": "circleci_config_binding",
                "confidence": CIRCLECI_CONFIG_BINDING_CONFIDENCE,
            }
        )
    return matches


def _get_pipeline_config(
    api_session: requests.Session,
    base_url: str,
    pipeline_id: str,
) -> str | None:
    """
    Fetch the compiled (fallback: source) config YAML for a pipeline run. Returns None on
    4xx (config not available / not accessible) so the run is skipped without aborting.
    """
    try:
        resp = api_session.get(
            f"{base_url}/pipeline/{pipeline_id}/config", timeout=_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError as exc:
        if exc.response is not None and 400 <= exc.response.status_code < 500:
            logger.debug("No config for pipeline %s: %s", pipeline_id, exc)
            return None
        raise
    return data.get("compiled") or data.get("source")


def _load_provider_routed_matchlinks(
    neo4j_session: neo4j.Session,
    matches: list[dict[str, Any]],
    org_id: str,
    update_tag: int,
) -> None:
    """
    Split match rows by provider and load PACKAGED_FROM edges via the matching target
    schema, plus a PACKAGED_BY edge to the building CircleCIProject for every matched
    image.
    """
    github_rows = [m for m in matches if m["provider"] == "github"]
    gitlab_rows = [m for m in matches if m["provider"] == "gitlab"]

    if github_rows:
        load_matchlinks(
            neo4j_session,
            CircleCIGitHubRepoPackagedFromMatchLink(),
            github_rows,
            lastupdated=update_tag,
            _sub_resource_label="CircleCIOrganization",
            _sub_resource_id=org_id,
        )
    if gitlab_rows:
        load_matchlinks(
            neo4j_session,
            CircleCIGitLabProjectPackagedFromMatchLink(),
            gitlab_rows,
            lastupdated=update_tag,
            _sub_resource_label="CircleCIOrganization",
            _sub_resource_id=org_id,
        )

    packaged_by_rows = [
        {
            "image_digest": m["image_digest"],
            "project_slug": m["project_slug"],
            "match_method": m["match_method"],
        }
        for m in matches
    ]
    if packaged_by_rows:
        load_matchlinks(
            neo4j_session,
            ImagePackagedByCircleCIProjectMatchLink(),
            packaged_by_rows,
            lastupdated=update_tag,
            _sub_resource_label="CircleCIOrganization",
            _sub_resource_id=org_id,
        )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_session: requests.Session,
    base_url: str,
    org_id: str,
    org_slug: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
    image_limit: int | None = None,
) -> None:
    """
    Produce CircleCI code-to-cloud fallback edges for a CircleCI organization.

    Two fallback rungs, appended below the SLSA-provenance / Dockerfile-analysis ladder for
    no-attestation / no-layer-history environments:
      1. circleci_tag_revision (medium): an ImageTag name equals (or is a 7+ char hex
         prefix of) a build revision SHA that resolves to a single repo. Resolves a
         specific image; a partial feed usually only causes misses, though a repo outside
         the window that shares the revision/prefix can still mis-attribute (rare).
      2. circleci_config_binding (low): a registry namespace parsed from the pipeline
         config binds to a repo. Namespace-wide and only applied to images rung 1 did not
         resolve. It relies on a time-bounded, partial /pipeline feed, so it can mis-bind a
         namespace shared by an unobserved project (accepted low-confidence tradeoff; see
         build_config_bindings).

    This is a MatchLink producer, not a node loader: pipeline runs and config YAML are
    consumed transiently and never persisted; only edges are written. Lazy: the /pipeline
    feed is fetched only when residual unmatched images exist.

    Runs after the GitHub/GitLab supply-chain syncs (CircleCI is ordered after them in
    cartography.sync), so their fresh PACKAGED_FROM edges gate the residual set here.
    """
    logger.info("Starting supply chain sync for CircleCI org %s", org_id)

    unmatched = get_unmatched_circleci_candidate_images(
        neo4j_session, org_id, update_tag, limit=image_limit
    )

    all_matches: list[dict[str, Any]] = []
    if unmatched:
        runs = get_pipeline_runs(api_session, base_url, org_slug)

        # Rung 1: tag == revision SHA.
        revision_map = build_revision_repo_map(runs)
        tag_matches = match_tag_revisions(unmatched, revision_map)
        all_matches.extend(tag_matches)

        # Rung 2: config-binding, only for images rung 1 did not resolve.
        matched_digests = {m["image_digest"] for m in tag_matches}
        residual = [img for img in unmatched if img["digest"] not in matched_digests]
        if residual:
            # One config per project is enough for a namespace binding; the feed is
            # newest-first, so the first run per slug is the most recent.
            runs_by_slug: dict[str, dict[str, Any]] = {}
            for run in runs:
                slug = run.get("project_slug")
                if slug and slug not in runs_by_slug:
                    runs_by_slug[slug] = run
            namespace_binding, repo_meta = build_config_bindings(
                list(runs_by_slug.values()),
                lambda pipeline_id: _get_pipeline_config(
                    api_session, base_url, pipeline_id
                ),
            )
            all_matches.extend(
                match_config_bindings(residual, namespace_binding, repo_meta)
            )

    if all_matches:
        logger.info(
            "Loading %d CircleCI fallback PACKAGED_FROM edge(s) for org %s",
            len(all_matches),
            org_id,
        )
        _load_provider_routed_matchlinks(neo4j_session, all_matches, org_id, update_tag)

    # No org-wide stale cleanup: the /pipeline feed is a partial, recency-bounded
    # enumeration (only the most recently-built projects, capped at _MAX_FEED_PAGES), not
    # a complete inventory. A GraphJob.from_matchlink cleanup keyed on update_tag would
    # delete every CircleCI edge whose build has aged out of that window, even though the
    # image and project still exist. This mirrors the projects module, which upserts but
    # never cleans up org-wide for the same reason. These edges are upsert-only and are
    # removed via node-level DETACH DELETE when the connected Image / CircleCIProject is
    # cleaned up by its own module.
    logger.info("Completed supply chain sync for CircleCI org %s", org_id)
