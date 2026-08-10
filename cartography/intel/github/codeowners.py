import hashlib
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

import neo4j
import requests

from cartography.client.core.tx import load
from cartography.client.core.tx import load_matchlinks
from cartography.graph.job import GraphJob
from cartography.intel.github.util import get_file_content
from cartography.intel.github.util import github_org_url
from cartography.models.github.codeowners import (
    DependencyGraphManifestToCodeOwnerRuleMatchLink,
)
from cartography.models.github.codeowners import GitHubCodeOwnerRuleSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)

CODEOWNERS_PATHS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")
CODEOWNERS_MAX_BYTES = 3 * 1024 * 1024
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class CodeOwnersFileFetchResult:
    source_path: str | None
    content: str | None
    cleanup_safe: bool


@dataclass(frozen=True)
class CodeOwnerTargetLookups:
    user_ids_by_login: dict[str, str]
    team_ids_by_org_slug: dict[tuple[str, str], str]


def _repo_parts_from_url(repo_url: str) -> tuple[str, str] | None:
    path_parts = [part for part in urlsplit(repo_url).path.split("/") if part]
    if len(path_parts) < 2:
        return None
    return path_parts[-2], path_parts[-1]


def _host_relative_url(org_url: str, path: str) -> str:
    parsed = urlsplit(org_url)
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _github_user_url(org_url: str, login: str) -> str:
    return _host_relative_url(org_url, f"/{quote(login, safe='')}")


def _github_team_url(org_url: str, org_login: str, team_slug: str) -> str:
    return _host_relative_url(
        org_url,
        f"/orgs/{quote(org_login, safe='')}/teams/{quote(team_slug, safe='')}",
    )


def normalize_repo_relative_path(
    path: str | None,
    repo_url: str | None = None,
    default_branch: str | None = None,
) -> str | None:
    if not path:
        return None

    normalized = path.strip().lstrip("/")
    if not normalized:
        return None

    repo_parts = _repo_parts_from_url(repo_url) if repo_url else None
    if not repo_parts:
        return normalized

    owner, repo = repo_parts
    path_parts = normalized.split("/")
    if len(path_parts) < 5:
        return normalized
    if path_parts[0] != owner or path_parts[1] != repo or path_parts[2] != "blob":
        return normalized

    remainder = path_parts[3:]
    branch_parts = default_branch.strip("/").split("/") if default_branch else []
    if branch_parts and remainder[: len(branch_parts)] == branch_parts:
        remainder = remainder[len(branch_parts) :]
    else:
        remainder = remainder[1:]
    return "/".join(remainder) or None


def _strip_inline_comment(line: str) -> str:
    for index, char in enumerate(line):
        if char == "#" and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line


def _split_codeowners_line(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith(r"\#"):
        return []

    without_comment = _strip_inline_comment(line).strip()
    if not without_comment:
        return None

    tokens: list[str] = []
    token_chars: list[str] = []
    escaping = False
    for char in without_comment:
        if escaping:
            if char.isspace():
                token_chars.append(char)
            else:
                token_chars.extend(("\\", char))
            escaping = False
            continue

        if char == "\\":
            escaping = True
            continue

        if char.isspace():
            if token_chars:
                tokens.append("".join(token_chars))
                token_chars = []
            continue

        token_chars.append(char)

    if escaping:
        token_chars.append("\\")
    if token_chars:
        tokens.append("".join(token_chars))
    return tokens


def _is_unsupported_pattern(pattern: str) -> bool:
    return pattern.startswith("!") or "[" in pattern or "]" in pattern


def _normalize_owner_tokens(
    owner_tokens: list[str],
    org_url: str,
    owner_targets: CodeOwnerTargetLookups | None = None,
) -> dict[str, list[str]]:
    owner_logins: list[str] = []
    owner_team_slugs: list[str] = []
    owner_emails: list[str] = []
    unresolved_owners: list[str] = []
    user_ids: list[str] = []
    team_ids: list[str] = []

    for token in owner_tokens:
        if not token:
            continue
        if token.startswith("@"):
            owner = token[1:]
            if "/" in owner:
                owner_org, team_slug = owner.split("/", 1)
                if owner_org and team_slug:
                    normalized_slug = team_slug.lower()
                    owner_team_slugs.append(normalized_slug)
                    team_id = _github_team_url(org_url, owner_org, normalized_slug)
                    if owner_targets:
                        team_id = owner_targets.team_ids_by_org_slug.get(
                            (owner_org.lower(), normalized_slug),
                            team_id,
                        )
                    team_ids.append(team_id)
                else:
                    unresolved_owners.append(token)
            elif owner:
                normalized_login = owner.lower()
                owner_logins.append(normalized_login)
                user_id = _github_user_url(org_url, owner)
                if owner_targets:
                    user_id = owner_targets.user_ids_by_login.get(
                        normalized_login,
                        user_id,
                    )
                user_ids.append(user_id)
            else:
                unresolved_owners.append(token)
        elif EMAIL_RE.match(token):
            owner_emails.append(token)
        else:
            unresolved_owners.append(token)

    return {
        "owner_logins": sorted(set(owner_logins)),
        "owner_team_slugs": sorted(set(owner_team_slugs)),
        "owner_emails": sorted(set(owner_emails)),
        "unresolved_owners": sorted(set(unresolved_owners)),
        "user_ids": sorted(set(user_ids)),
        "team_ids": sorted(set(team_ids)),
    }


def _rule_id(
    repo_url: str,
    source_path: str,
    line_number: int,
    pattern: str,
    owners: list[str],
) -> str:
    digest = hashlib.sha256(
        f"{repo_url}|{source_path}|{line_number}|{pattern}|{' '.join(owners)}".encode()
    ).hexdigest()[:16]
    return f"{repo_url}#CODEOWNERS:{source_path}:{line_number}:{digest}"


def parse_codeowners_content(
    content: str,
    repo_url: str,
    repo_name: str | None,
    default_branch: str | None,
    source_path: str,
    org_url: str,
    owner_targets: CodeOwnerTargetLookups | None = None,
) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        tokens = _split_codeowners_line(line)
        if tokens is None:
            continue
        if not tokens:
            logger.debug(
                "Skipping invalid CODEOWNERS line %d in %s: %s",
                line_number,
                repo_url,
                line,
            )
            continue

        pattern = tokens[0]
        if _is_unsupported_pattern(pattern):
            logger.debug(
                "Skipping unsupported CODEOWNERS pattern on line %d in %s: %s",
                line_number,
                repo_url,
                pattern,
            )
            continue

        owners = tokens[1:]
        if not owners:
            logger.debug(
                "Skipping ownerless CODEOWNERS pattern on line %d in %s: %s",
                line_number,
                repo_url,
                pattern,
            )
            continue

        normalized_owners = _normalize_owner_tokens(owners, org_url, owner_targets)
        rules.append(
            {
                "id": _rule_id(repo_url, source_path, line_number, pattern, owners),
                "repo_url": repo_url,
                "repo_name": repo_name,
                "default_branch": default_branch,
                "source_path": source_path,
                "line_number": line_number,
                "pattern": pattern,
                "owners": owners,
                **normalized_owners,
            }
        )
    return rules


def build_codeowner_target_lookups(
    github_users: list[dict[str, Any]] | None,
    github_teams: list[dict[str, Any]] | None,
) -> CodeOwnerTargetLookups:
    user_ids_by_login: dict[str, str] = {}
    for user in github_users or []:
        login = user.get("login")
        url = user.get("url")
        if login and url:
            user_ids_by_login[login.lower()] = url

    team_ids_by_org_slug: dict[tuple[str, str], str] = {}
    for team in github_teams or []:
        org_login = team.get("org_login")
        slug = team.get("name") or team.get("slug")
        url = team.get("url")
        if org_login and slug and url:
            team_ids_by_org_slug[(org_login.lower(), slug.lower())] = url

    return CodeOwnerTargetLookups(
        user_ids_by_login=user_ids_by_login,
        team_ids_by_org_slug=team_ids_by_org_slug,
    )


def _glob_fragment_to_regex(pattern: str) -> str:
    parts: list[str] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                if i + 2 < len(pattern) and pattern[i + 2] == "/":
                    parts.append("(?:.*/)?")
                    i += 3
                else:
                    parts.append(".*")
                    i += 2
            else:
                parts.append("[^/]*")
                i += 1
        elif char == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(char))
            i += 1
    return "".join(parts)


def codeowners_pattern_matches(pattern: str, path: str) -> bool:
    normalized_path = path.strip().lstrip("/")
    if not normalized_path:
        return False

    anchored = pattern.startswith("/")
    directory_pattern = pattern.endswith("/")
    normalized_pattern = pattern.strip().lstrip("/")
    if directory_pattern:
        normalized_pattern = normalized_pattern.rstrip("/")
    if not normalized_pattern:
        return False

    has_slash = "/" in normalized_pattern
    regex_fragment = _glob_fragment_to_regex(normalized_pattern)
    if directory_pattern:
        if has_slash or anchored:
            regex = f"^{regex_fragment}(/.*)?$"
        else:
            regex = f"(^|.*/){regex_fragment}(/.*)?$"
    elif has_slash or anchored:
        regex = f"^{regex_fragment}$"
    else:
        regex = f"(^|.*/){regex_fragment}$"

    return re.match(regex, normalized_path) is not None


def match_codeowner_rule_for_path(
    rules: list[dict[str, Any]],
    path: str | None,
) -> dict[str, Any] | None:
    if not path:
        return None
    matched_rule: dict[str, Any] | None = None
    for rule in rules:
        if codeowners_pattern_matches(rule["pattern"], path):
            matched_rule = rule
    return matched_rule


def get_effective_codeowners_file(
    token: str,
    api_url: str,
    repo_url: str,
    default_branch: str | None,
) -> CodeOwnersFileFetchResult:
    repo_parts = _repo_parts_from_url(repo_url)
    if not repo_parts:
        logger.warning(
            "Cannot parse GitHub repository URL %s for CODEOWNERS.", repo_url
        )
        return CodeOwnersFileFetchResult(None, None, cleanup_safe=False)

    owner, repo = repo_parts
    ref = default_branch or "HEAD"
    for path in CODEOWNERS_PATHS:
        try:
            content = get_file_content(
                token,
                owner,
                repo,
                path,
                ref=ref,
                base_url=api_url,
            )
        except requests.exceptions.HTTPError as err:
            status = err.response.status_code if err.response is not None else None
            logger.warning(
                "Skipping CODEOWNERS cleanup for repo %s because %s returned HTTP %s.",
                repo_url,
                path,
                status,
            )
            return CodeOwnersFileFetchResult(None, None, cleanup_safe=False)
        except requests.exceptions.RequestException:
            logger.warning(
                "Skipping CODEOWNERS cleanup for repo %s because fetching %s failed.",
                repo_url,
                path,
                exc_info=True,
            )
            return CodeOwnersFileFetchResult(None, None, cleanup_safe=False)

        if content is None:
            continue
        if len(content.encode("utf-8")) > CODEOWNERS_MAX_BYTES:
            logger.info(
                "Ignoring CODEOWNERS file %s in %s because it is over GitHub's 3 MB limit.",
                path,
                repo_url,
            )
            return CodeOwnersFileFetchResult(path, None, cleanup_safe=True)
        return CodeOwnersFileFetchResult(path, content, cleanup_safe=True)

    return CodeOwnersFileFetchResult(None, None, cleanup_safe=True)


def transform_repositories_for_codeowners(
    repositories: list[dict[str, Any]],
    owner_org_id: str,
) -> list[dict[str, Any]]:
    repos = [
        {
            "repo_url": repo["id"],
            "repo_name": repo.get("name"),
            "default_branch": repo.get("defaultbranch"),
        }
        for repo in repositories
        if repo.get("id") and repo.get("owner_org_id") == owner_org_id
    ]
    return sorted(repos, key=lambda repo: repo["repo_url"])


def build_manifest_codeowner_matches(
    rules: list[dict[str, Any]],
    manifests: list[dict[str, Any]],
    default_branches_by_repo_url: dict[str, str | None] | None = None,
) -> list[dict[str, Any]]:
    default_branches_by_repo_url = default_branches_by_repo_url or {}
    rules_by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rule in rules:
        rules_by_repo[rule["repo_url"]].append(rule)

    matches: list[dict[str, Any]] = []
    for manifest in manifests:
        repo_url = manifest["repo_url"]
        repo_rules = rules_by_repo.get(repo_url)
        if not repo_rules:
            continue
        matched_path = manifest.get(
            "repo_relative_path"
        ) or normalize_repo_relative_path(
            manifest.get("blob_path"),
            repo_url,
            manifest.get("default_branch")
            or default_branches_by_repo_url.get(repo_url),
        )
        matched_rule = match_codeowner_rule_for_path(repo_rules, matched_path)
        if matched_rule is None:
            continue
        matches.append(
            {
                "manifest_id": manifest.get("manifest_id") or manifest["id"],
                "rule_id": matched_rule["id"],
                "matched_path": matched_path,
                "match_pattern": matched_rule["pattern"],
            }
        )
    return matches


@timeit
def load_codeowner_rules(
    neo4j_session: neo4j.Session,
    rules: list[dict[str, Any]],
    update_tag: int,
    owner_org_id: str,
) -> None:
    if not rules:
        return
    load(
        neo4j_session,
        GitHubCodeOwnerRuleSchema(),
        rules,
        lastupdated=update_tag,
        owner_org_id=owner_org_id,
    )


@timeit
def load_manifest_matches(
    neo4j_session: neo4j.Session,
    matches: list[dict[str, Any]],
    update_tag: int,
    owner_org_id: str,
) -> None:
    if not matches:
        return
    load_matchlinks(
        neo4j_session,
        DependencyGraphManifestToCodeOwnerRuleMatchLink(),
        matches,
        lastupdated=update_tag,
        _sub_resource_label="GitHubOrganization",
        _sub_resource_id=owner_org_id,
    )


@timeit
def cleanup_manifest_matches(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    owner_org_id: str,
) -> None:
    GraphJob.from_matchlink(
        DependencyGraphManifestToCodeOwnerRuleMatchLink(),
        "GitHubOrganization",
        owner_org_id,
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)


@timeit
def cleanup_codeowner_rules(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    owner_org_id: str,
) -> None:
    cleanup_params = {**common_job_parameters, "owner_org_id": owner_org_id}
    GraphJob.from_node_schema(GitHubCodeOwnerRuleSchema(), cleanup_params).run(
        neo4j_session
    )


@timeit
def sync(
    neo4j_session: neo4j.Session,
    common_job_parameters: dict[str, Any],
    github_api_key: str,
    github_url: str,
    organization: str,
    repositories: list[dict[str, Any]],
    dependency_manifests: list[dict[str, Any]],
    *,
    dependency_manifests_cleanup_safe: bool = True,
    github_users: list[dict[str, Any]] | None = None,
    github_teams: list[dict[str, Any]] | None = None,
) -> None:
    update_tag = common_job_parameters["UPDATE_TAG"]
    owner_org_id = github_org_url(github_url, organization)
    repos = transform_repositories_for_codeowners(repositories, owner_org_id)
    logger.info(
        "Syncing GitHub CODEOWNERS for %d repositories in org %s.",
        len(repos),
        organization,
    )

    all_rules: list[dict[str, Any]] = []
    cleanup_safe = True
    owner_targets = build_codeowner_target_lookups(github_users, github_teams)
    for repo in repos:
        fetch_result = get_effective_codeowners_file(
            github_api_key,
            github_url,
            repo["repo_url"],
            repo.get("default_branch"),
        )
        if not fetch_result.cleanup_safe:
            cleanup_safe = False
            continue
        if fetch_result.content is None or fetch_result.source_path is None:
            continue

        all_rules.extend(
            parse_codeowners_content(
                fetch_result.content,
                repo["repo_url"],
                repo.get("repo_name"),
                repo.get("default_branch"),
                fetch_result.source_path,
                owner_org_id,
                owner_targets,
            )
        )

    load_codeowner_rules(neo4j_session, all_rules, update_tag, owner_org_id)

    default_branches_by_repo_url = {
        repo["repo_url"]: repo.get("default_branch") for repo in repos
    }
    manifest_matches = build_manifest_codeowner_matches(
        all_rules,
        dependency_manifests,
        default_branches_by_repo_url,
    )
    load_manifest_matches(neo4j_session, manifest_matches, update_tag, owner_org_id)

    if cleanup_safe:
        if dependency_manifests_cleanup_safe:
            cleanup_manifest_matches(neo4j_session, common_job_parameters, owner_org_id)
        else:
            logger.warning(
                "Skipping GitHub CODEOWNERS manifest match cleanup for org %s because "
                "GitHub returned incomplete dependency manifest data.",
                organization,
            )
        cleanup_codeowner_rules(neo4j_session, common_job_parameters, owner_org_id)
    else:
        logger.warning(
            "Skipping GitHub CODEOWNERS cleanup for org %s because at least one repo fetch failed.",
            organization,
        )
