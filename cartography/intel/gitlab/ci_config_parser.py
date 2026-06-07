"""
GitLab CI/CD config (`.gitlab-ci.yml`) YAML parser.

Pure: no I/O. Extracts security-relevant info from a YAML pipeline definition:

- The list of `include:` references (local, project, remote, template, component)
  with a `is_pinned` flag set when an external include uses a 40-char SHA ref.
- Variable references (`$VAR`, `${VAR}`) detected anywhere in the raw YAML —
  excluding GitLab's own predefined variables (`CI_*`, `GITLAB_*`).
- Pipeline stages, job count, default image.
- Coarse trigger categories detected from `workflow:rules:`, `rules:`, `only:`,
  `except:` and `when:` (merge_requests, schedules, pushes, tag, manual,
  web, api).

The parser intentionally stays heuristic: extracting exact rule expressions is
out of scope. The goal is to surface signals (e.g. "this pipeline can be
triggered manually" or "this include is not pinned to a SHA") that downstream
queries can act on.
"""

import logging
import re
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# 40-char hex SHA — same definition as workflow_parser.py
SHA_PATTERN = re.compile(r"^[a-f0-9]{40}$")

# `$VAR` and `${VAR}` references. Captures the variable name only.
VARIABLE_PATTERN = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")

# Top-level keys that are not jobs (they're keywords in the GitLab CI schema).
# Used to compute job_count.
RESERVED_TOP_LEVEL_KEYS = {
    "stages",
    "variables",
    "default",
    "include",
    "workflow",
    "before_script",
    "after_script",
    "image",
    "services",
    "cache",
    "pages",
    "stages",
}

# Trigger keyword detection — heuristic, scanned over the raw YAML.
TRIGGER_PATTERNS = {
    "merge_requests": re.compile(
        r'CI_PIPELINE_SOURCE\s*==\s*["\']merge_request_event["\']'
        r"|CI_MERGE_REQUEST_"
        r"|merge_requests?"
    ),
    "schedules": re.compile(r'CI_PIPELINE_SOURCE\s*==\s*["\']schedule["\']|schedules?'),
    "tag": re.compile(r"CI_COMMIT_TAG|^\s*-?\s*tags\s*:?", re.MULTILINE),
    "manual": re.compile(r"^\s*when\s*:\s*manual", re.MULTILINE),
    "web": re.compile(r'CI_PIPELINE_SOURCE\s*==\s*["\']web["\']'),
    "api": re.compile(r'CI_PIPELINE_SOURCE\s*==\s*["\']api["\']'),
    "pushes": re.compile(
        r'CI_PIPELINE_SOURCE\s*==\s*["\']push["\']|^\s*-?\s*pushes?\s*:?',
        re.MULTILINE,
    ),
}


@dataclass
class ParsedCIInclude:
    """A single `include:` entry from the YAML."""

    include_type: str  # "local" | "project" | "remote" | "template" | "component"
    location: str
    ref: str | None
    is_pinned: bool
    is_local: bool


@dataclass
class ParsedCIConfig:
    """Result of parsing a `.gitlab-ci.yml` (raw or merged)."""

    is_valid: bool | None = None
    job_count: int = 0
    stages: list[str] = field(default_factory=list)
    trigger_rules: list[str] = field(default_factory=list)
    referenced_variable_keys: list[str] = field(default_factory=list)
    default_image: str | None = None
    has_includes: bool = False
    includes: list[ParsedCIInclude] = field(default_factory=list)


def _is_pinned(include_type: str, ref: str | None, location: str) -> bool:
    """
    Pinning rule:
    - local: always considered pinned (internal to the repo)
    - project: pinned iff `ref` is a 40-char SHA
    - remote: pinned iff the URL contains a 40-char SHA in its path
    - template, component: never pinned (they resolve to a moving target)
    """
    if include_type == "local":
        return True
    if include_type == "project":
        return bool(ref and SHA_PATTERN.match(ref))
    if include_type == "remote":
        return bool(re.search(r"/[a-f0-9]{40}/", location))
    return False


def _classify_bare_string(item: str) -> ParsedCIInclude:
    """
    A bare string include can be either a local path (legacy syntax) or a
    full URL. Detect URLs by scheme and classify them as ``remote``; a
    remote include without a SHA in its path is unpinned.
    """
    if item.startswith(("http://", "https://")):
        return ParsedCIInclude(
            include_type="remote",
            location=item,
            ref=None,
            is_pinned=_is_pinned("remote", None, item),
            is_local=False,
        )
    return ParsedCIInclude(
        include_type="local",
        location=item,
        ref=None,
        is_pinned=True,
        is_local=True,
    )


def _parse_single_include(item: Any) -> list[ParsedCIInclude]:
    """
    Parse a single ``include:`` entry. Accepts:

    - a bare string (URL → remote, otherwise local)
    - a dict with one of: ``local`` / ``project`` / ``remote`` / ``template``
      / ``component``

    Returns a list because a single ``project:`` entry with a ``file:`` list
    of paths expands into one record per file.
    """
    if isinstance(item, str):
        return [_classify_bare_string(item)]

    if not isinstance(item, dict):
        return []

    for include_type in ("local", "project", "remote", "template", "component"):
        if include_type not in item:
            continue
        primary = item.get(include_type) or ""
        if isinstance(primary, list):
            # `include: { local: [a, b] }` is handled separately by
            # `_extract_includes`. For other types it is unsupported.
            return []

        # `include:project` carries an additional `file:` field which is the
        # actual path within the referenced project. The `project` value is
        # the project path (e.g. `my-org/shared-ci`), not the file path —
        # we want both in `location` so consumers can identify the include.
        if include_type == "project":
            ref = item.get("ref")
            files = item.get("file")
            file_list = files if isinstance(files, list) else [files] if files else [""]
            results: list[ParsedCIInclude] = []
            for file_path in file_list:
                location = f"{primary}:{file_path}" if file_path else str(primary)
                results.append(
                    ParsedCIInclude(
                        include_type=include_type,
                        location=location,
                        ref=ref,
                        is_pinned=_is_pinned(include_type, ref, location),
                        is_local=False,
                    )
                )
            return results

        return [
            ParsedCIInclude(
                include_type=include_type,
                location=str(primary),
                ref=None,
                is_pinned=_is_pinned(include_type, None, str(primary)),
                is_local=(include_type == "local"),
            )
        ]
    return []


def _extract_includes(includes_value: Any) -> list[ParsedCIInclude]:
    """Normalise the ``include:`` value into a flat list of ParsedCIInclude."""
    if includes_value is None:
        return []

    items = includes_value if isinstance(includes_value, list) else [includes_value]
    result: list[ParsedCIInclude] = []
    for item in items:
        # `include: { local: [a, b] }` — expand the list into multiple includes.
        if (
            isinstance(item, dict)
            and "local" in item
            and isinstance(item["local"], list)
        ):
            for path in item["local"]:
                result.append(
                    ParsedCIInclude(
                        include_type="local",
                        location=str(path),
                        ref=None,
                        is_pinned=True,
                        is_local=True,
                    )
                )
            continue
        result.extend(_parse_single_include(item))
    return result


def _is_predefined_gitlab_variable(name: str) -> bool:
    """GitLab predefined variables come from the runner environment, not CI vars."""
    return name.startswith("CI_") or name.startswith("GITLAB_") or name == "CI"


def _extract_referenced_variables(content: str) -> list[str]:
    """All `$VAR` / `${VAR}` references in the raw YAML, minus GitLab predefineds."""
    seen: set[str] = set()
    for match in VARIABLE_PATTERN.findall(content):
        if not _is_predefined_gitlab_variable(match):
            seen.add(match)
    return sorted(seen)


def _extract_trigger_rules(content: str) -> list[str]:
    """Heuristic trigger detection over the raw YAML."""
    triggers: list[str] = []
    for trigger_name, pattern in TRIGGER_PATTERNS.items():
        if pattern.search(content):
            triggers.append(trigger_name)
    return sorted(triggers)


def _count_jobs(config: dict[str, Any]) -> int:
    """A job is any top-level key that isn't a reserved keyword and maps to a dict."""
    return sum(
        1
        for key, value in config.items()
        if key not in RESERVED_TOP_LEVEL_KEYS
        and not (isinstance(key, str) and key.startswith("."))
        and isinstance(value, dict)
    )


def _extract_default_image(config: dict[str, Any]) -> str | None:
    """`image` can sit at the top level or inside `default:`."""
    default = config.get("default")
    if isinstance(default, dict):
        image = default.get("image")
        if isinstance(image, dict):
            return image.get("name")
        if isinstance(image, str):
            return image

    image = config.get("image")
    if isinstance(image, dict):
        return image.get("name")
    if isinstance(image, str):
        return image
    return None


def parse_lint_includes(
    lint_includes: list[dict[str, Any]] | None,
) -> list[ParsedCIInclude]:
    """
    Convert GitLab's ``/ci/lint`` ``includes`` array (each entry has shape
    ``{type, location, blob, raw, extra, context_project, context_sha}``)
    into our ``ParsedCIInclude`` records.

    The merged_yaml returned alongside has the included content inlined
    as jobs, so its ``include:`` block is gone — without this helper the
    YAML parser alone would emit zero GitLabCIInclude nodes on the lint
    path. ``ref`` for ``project`` includes is taken from ``extra.ref``
    when present, falling back to ``context_sha`` (the resolved commit
    that GitLab fetched).

    GitLab's lint response uses ``type: "file"`` for project includes
    (with ``extra.project`` set). We normalise those back to the YAML
    parser's shape (``include_type="project"``, ``location="<project>:<file>"``)
    so downstream nodes are consistent across the two fetch paths.
    """
    if not lint_includes:
        return []
    results: list[ParsedCIInclude] = []
    for entry in lint_includes:
        if not isinstance(entry, dict):
            continue
        include_type = entry.get("type") or ""
        location = entry.get("location") or entry.get("raw") or ""
        if not include_type or not location:
            continue
        extra = entry.get("extra") if isinstance(entry.get("extra"), dict) else {}
        extra = extra or {}
        ref = extra.get("ref") or entry.get("context_sha")

        # Normalise file-with-project to the same shape as the YAML parser.
        project = extra.get("project")
        if include_type == "file" and project:
            include_type = "project"
            location = f"{project}:{location}"

        results.append(
            ParsedCIInclude(
                include_type=include_type,
                location=str(location),
                ref=str(ref) if ref else None,
                is_pinned=_is_pinned(
                    include_type, str(ref) if ref else None, str(location)
                ),
                is_local=(include_type == "local"),
            )
        )
    return results


def parse_ci_config(content: str, is_valid: bool | None = None) -> ParsedCIConfig:
    """
    Parse a GitLab CI YAML document. Returns an empty `ParsedCIConfig` on
    YAML parse error rather than raising — caller can treat absence of jobs
    as "could not parse".
    """
    result = ParsedCIConfig(is_valid=is_valid)

    try:
        config = yaml.safe_load(content)
    except yaml.YAMLError:
        logger.warning("Failed to parse GitLab CI YAML")
        return result

    if not isinstance(config, dict):
        return result

    # Includes
    result.includes = _extract_includes(config.get("include"))
    result.has_includes = len(result.includes) > 0

    # Stages
    stages = config.get("stages")
    if isinstance(stages, list):
        result.stages = [str(s) for s in stages]

    # Job count
    result.job_count = _count_jobs(config)

    # Default image
    result.default_image = _extract_default_image(config)

    # Variable references — scan raw content (catches refs inside scripts / rules / etc.)
    result.referenced_variable_keys = _extract_referenced_variables(content)

    # Trigger rules
    result.trigger_rules = _extract_trigger_rules(content)

    return result
