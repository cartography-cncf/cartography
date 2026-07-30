import logging
import re
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Iterator

import neo4j
import requests

from cartography.client.core.tx import load_matchlinks
from cartography.client.core.tx import run_write_query
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

# circleci_tag_revision runs below the SLSA-provenance / Dockerfile-analysis / package-owner
# ladder. Confidence is data (consumers filter at their own threshold) and is tunable:
# tag=SHA resolves a specific image (medium), sitting below the GHCR package_owner_repo
# rung (0.6).
CIRCLECI_TAG_REVISION_CONFIDENCE = 0.5

# The /pipeline feed is filtered to a recent lookback window. We do NOT early-stop on
# ordering: CircleCI does not document a global newest-first order across pages, so a
# single old item must not halt pagination before newer runs on later pages. Instead we
# fetch up to _MAX_FEED_PAGES and keep only runs within the window in memory. The page cap
# bounds per-sync cost; coverage within the window is therefore best-effort.
_FEED_LOOKBACK_DAYS = 30
_MAX_FEED_PAGES = 20

_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


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
    missing or unparseable created_at are treated as within the window (kept), so a bad
    timestamp never silently drops a run.
    """
    try:
        created = parse_iso(run.get("created_at"))
    except (ValueError, TypeError):
        return False
    if created is None:
        return False
    return created < cutoff


@timeit
def get_unmatched_circleci_candidate_images(
    neo4j_session: neo4j.Session,
    org_id: str,
    update_tag: int,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Query container images not yet matched to a code repository in this sync iteration,
    returning each image's digest and the full set of its tag names.

    Cross-provider gating is implicit: images that already received a PACKAGED_FROM this
    run (e.g. from the GitHub/GitLab provenance or Dockerfile rungs, which run earlier in
    the sync) are excluded. Images with only a stale PACKAGED_FROM from a prior iteration
    are included so they can be re-matched (or their stale edge cleaned) this run. The
    second clause skips images already claimed by a different CircleCI org.

    :param neo4j_session: Neo4j session
    :param org_id: CircleCI organization id used for scoping
    :param update_tag: The current sync update tag
    :param limit: Optional cap on the number of images returned
    :return: List of {"digest", "tags": [tag name, ...]} dicts
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
        WITH img, collect(DISTINCT t.name) AS tags
        RETURN img.digest AS digest, tags
    """
    if limit:
        query += f" LIMIT {limit}"

    result = neo4j_session.run(query, update_tag=update_tag, org_id=org_id)
    images = [
        {
            "digest": record["digest"],
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
    Fetch pipeline runs built within the lookback window from the /pipeline feed. We fetch
    up to _MAX_FEED_PAGES and filter to the window in memory rather than stopping paging on
    the first old run, because CircleCI does not document a global newest-first order
    across pages. These are high-volume ephemeral CI telemetry, consumed transiently in
    memory and never loaded as graph nodes.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    runs = paginated_get(
        api_session,
        f"{base_url}/pipeline",
        params={"org-slug": org_slug},
        max_pages=_MAX_FEED_PAGES,
    )
    return [run for run in runs if not _run_older_than(run, cutoff)]


def _iter_feed_targets(
    runs: list[dict[str, Any]],
) -> Iterator[tuple[str, str, str, str]]:
    """
    Yield (revision, repo_url, provider, project_slug) for each feed run that names a
    supported (github/gitlab) repo with a revision. Single source of truth for both the
    unique revision map and the feed-evidence set.
    """
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
        yield revision, repo_url, provider, project_slug


def build_revision_targets(
    runs: list[dict[str, Any]],
) -> dict[str, set[tuple[str, str, str]]]:
    """
    Build {revision_sha -> {(repo_url, provider, project_slug), ...}} from pipeline-feed
    runs, keeping ALL targets per revision (ambiguous revisions are not dropped here). The
    repo URL is normalized to the canonical HTTPS form used by GitHubRepository.id /
    GitLabProject.web_url.

    Ambiguity is resolved at match time against this full multimap, so a short prefix that
    collides with an ambiguous revision is correctly seen as ambiguous (see
    match_tag_revisions).
    """
    revision_targets: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for revision, repo_url, provider, project_slug in _iter_feed_targets(runs):
        revision_targets[revision].add((repo_url, provider, project_slug))
    return dict(revision_targets)


def _tag_target(
    tag: str,
    revision_targets: dict[str, set[tuple[str, str, str]]],
) -> tuple[str, str, str] | None:
    """
    Resolve a SHA-like tag to a single (repo_url, provider, project_slug) target, or None
    if it matches no revision or resolves to more than one distinct target. Considers every
    revision the tag equals or is a 7+ char prefix of, across the FULL feed (including
    ambiguous revisions), so the result never depends on which revisions happened to be
    unique or on Neo4j/dict ordering.
    """
    targets: set[tuple[str, str, str]] = set()
    for rev, rev_targets in revision_targets.items():
        if rev == tag or (len(tag) < len(rev) and rev.startswith(tag)):
            targets |= rev_targets
    if len(targets) == 1:
        return next(iter(targets))
    return None


def match_tag_revisions(
    images: list[dict[str, Any]],
    revision_targets: dict[str, set[tuple[str, str, str]]],
) -> list[dict[str, Any]]:
    """
    Match images whose tag name equals (or is a 7+ char hex prefix of) a build revision
    that resolves to a single repo. Produces at most one row per image digest.

    All of an image's SHA tags are resolved and their targets unioned: if the union is a
    single distinct target the image matches it, otherwise the image is ambiguous and
    skipped. This is order-independent and treats "multiple repositories" as ambiguous
    whether the collision comes from one tag, several tags, or a short-prefix collision
    with an ambiguous revision.
    """
    matches: list[dict[str, Any]] = []
    for image in images:
        targets: set[tuple[str, str, str]] = set()
        for raw_tag in image["tags"]:
            tag = raw_tag.strip().lower()
            if not _is_probable_sha(tag):
                continue
            target = _tag_target(tag, revision_targets)
            if target is not None:
                targets.add(target)
        if len(targets) != 1:
            continue
        repo_url, provider, project_slug = next(iter(targets))
        matches.append(
            {
                "image_digest": image["digest"],
                "repo_url": repo_url,
                "provider": provider,
                "project_slug": project_slug,
                "match_method": "circleci_tag_revision",
                "confidence": CIRCLECI_TAG_REVISION_CONFIDENCE,
            }
        )
    return matches


def images_with_feed_evidence(
    images: list[dict[str, Any]],
    feed_revisions: set[str],
) -> set[str]:
    """
    Digests of images whose SHA tag matches (exactly, or as a 7+ char prefix of) some
    revision in the current feed. These are images the feed carries fresh evidence about
    this run, whether or not that evidence produced a unique match. Used to scope stale-edge
    cleanup to re-evaluated images only.
    """
    evidenced: set[str] = set()
    for image in images:
        for raw_tag in image["tags"]:
            tag = raw_tag.strip().lower()
            if not _is_probable_sha(tag):
                continue
            if tag in feed_revisions or any(
                len(tag) < len(rev) and rev.startswith(tag) for rev in feed_revisions
            ):
                evidenced.add(image["digest"])
                break
    return evidenced


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
def get_circleci_edged_image_tags(
    neo4j_session: neo4j.Session,
    org_id: str,
) -> list[dict[str, Any]]:
    """
    Return {digest, tags} for every image that currently has a CircleCI-scoped
    PACKAGED_FROM / PACKAGED_BY edge for this org. This is the cleanup universe: it is
    independent of the residual (unmatched) set, so an image that got a fresh GitHub/GitLab
    PACKAGED_FROM this run (and was therefore excluded from the residual set) is still
    considered for stale-CircleCI-edge cleanup.
    """
    query = """
        MATCH (img:Image)-[r]->()
        WHERE type(r) IN ['PACKAGED_FROM', 'PACKAGED_BY']
          AND r._sub_resource_label = 'CircleCIOrganization'
          AND r._sub_resource_id = $org_id
        WITH DISTINCT img
        OPTIONAL MATCH (img)<-[:IMAGE]-(t:ImageTag)
        RETURN img.digest AS digest, collect(DISTINCT t.name) AS tags
    """
    result = neo4j_session.run(query, org_id=org_id)
    return [
        {
            "digest": record["digest"],
            "tags": [t for t in (record["tags"] or []) if t],
        }
        for record in result
    ]


def _cleanup_reevaluated_image_edges(
    neo4j_session: neo4j.Session,
    digests: set[str],
    org_id: str,
    update_tag: int,
) -> None:
    """
    Remove CircleCI-scoped PACKAGED_FROM / PACKAGED_BY edges that were NOT refreshed to the
    current update_tag, but only for images the feed re-evaluated this run (``digests`` =
    images with fresh feed evidence). This drops an edge when a later run makes the match
    ambiguous or points the image at a different repo, while the fresh match (if any) has
    already been upserted with the current update_tag and so survives.

    Bounded to re-evaluated images on purpose: an image with no fresh evidence (its build
    aged out of the lookback window) is left untouched, so we never delete a still-valid
    edge just because its build is no longer in the feed. This is why there is no org-wide
    cleanup (see sync()).
    """
    if not digests:
        return
    run_write_query(
        neo4j_session,
        """
        UNWIND $digests AS d
        MATCH (img:Image {digest: d})-[r]->()
        WHERE type(r) IN ['PACKAGED_FROM', 'PACKAGED_BY']
          AND r._sub_resource_label = 'CircleCIOrganization'
          AND r._sub_resource_id = $org_id
          AND r.lastupdated <> $update_tag
        DELETE r
        """,
        digests=list(digests),
        org_id=org_id,
        update_tag=update_tag,
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

    One fallback rung, appended below the SLSA-provenance / Dockerfile-analysis ladder for
    no-attestation / no-layer-history environments: circleci_tag_revision (medium), where
    an ImageTag name equals (or is a 7+ char hex prefix of) a build revision SHA that
    resolves to a single repo. It resolves a specific image; a partial feed usually only
    causes misses, though a repo outside the window that shares the revision/prefix can
    still mis-attribute (rare, reflected in the medium confidence).

    This is a MatchLink producer, not a node loader: pipeline runs are consumed transiently
    and never persisted; only edges are written. Lazy: the /pipeline feed is fetched only
    when residual unmatched images exist.

    Cleanup is targeted, not org-wide: only images the feed re-evaluated this run have their
    stale CircleCI edges removed (see _cleanup_reevaluated_image_edges). Images whose build
    has aged out of the feed keep their edges, so a partial feed never deletes still-valid
    ones (mirrors the projects module, which upserts but never cleans up org-wide).

    Runs after the GitHub/GitLab supply-chain syncs (CircleCI is ordered after them in
    cartography.sync), so their fresh PACKAGED_FROM edges gate the residual set here.
    """
    logger.info("Starting supply chain sync for CircleCI org %s", org_id)

    # Images to (re)match, and the wider universe of images with an existing CircleCI edge
    # (the cleanup scope, independent of the residual set so GitHub/GitLab-matched images
    # are still considered for stale-edge cleanup).
    unmatched = get_unmatched_circleci_candidate_images(
        neo4j_session, org_id, update_tag, limit=image_limit
    )
    edged = get_circleci_edged_image_tags(neo4j_session, org_id)

    all_matches: list[dict[str, Any]] = []
    evidenced_digests: set[str] = set()
    if unmatched or edged:
        runs = get_pipeline_runs(api_session, base_url, org_slug)
        revision_targets = build_revision_targets(runs)
        all_matches = match_tag_revisions(unmatched, revision_targets)
        # Cleanup scope: images with an existing CircleCI edge that the feed re-evaluated
        # this run (a SHA tag present in the feed), regardless of whether they were in the
        # residual set.
        evidenced_digests = images_with_feed_evidence(edged, set(revision_targets))

    if all_matches:
        logger.info(
            "Loading %d CircleCI fallback PACKAGED_FROM edge(s) for org %s",
            len(all_matches),
            org_id,
        )
        _load_provider_routed_matchlinks(neo4j_session, all_matches, org_id, update_tag)

    # Targeted cleanup AFTER loading fresh edges: drop stale CircleCI edges only for images
    # the feed re-evaluated this run (ambiguous now, or repointed to a different repo). The
    # fresh match, if any, was just upserted with update_tag and so survives.
    _cleanup_reevaluated_image_edges(
        neo4j_session, evidenced_digests, org_id, update_tag
    )

    logger.info("Completed supply chain sync for CircleCI org %s", org_id)
