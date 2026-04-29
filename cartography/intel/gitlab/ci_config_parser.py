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
        r'|CI_MERGE_REQUEST_'
        r'|merge_requests?'
    ),
    "schedules": re.compile(
        r'CI_PIPELINE_SOURCE\s*==\s*["\']schedule["\']|schedules?'
    ),
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
    raw_include: str


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


def _parse_single_include(item: Any) -> ParsedCIInclude | None:
    """
    Parse a single `include:` entry. Accepts:
    - a bare string (treated as local)
    - a dict with one of: local / project / remote / template / component

    Anything else is ignored.
    """
    if isinstance(item, str):
        return ParsedCIInclude(
            include_type="local",
            location=item,
            ref=None,
            is_pinned=True,
            is_local=True,
            raw_include=item,
        )

    if not isinstance(item, dict):
        return None

    raw = str(item)
    for include_type in ("local", "project", "remote", "template", "component"):
        if include_type in item:
            location = item.get(include_type) or ""
            if isinstance(location, list):
                # `include: { local: [a, b] }` is also valid GitLab syntax;
                # we flatten by emitting one ParsedCIInclude per entry below.
                return None
            ref = item.get("ref") if include_type == "project" else None
            return ParsedCIInclude(
                include_type=include_type,
                location=str(location),
                ref=ref,
                is_pinned=_is_pinned(include_type, ref, str(location)),
                is_local=(include_type == "local"),
                raw_include=raw,
            )
    return None


def _extract_includes(includes_value: Any) -> list[ParsedCIInclude]:
    """Normalise the `include:` value into a flat list of ParsedCIInclude."""
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
                        raw_include=str(item),
                    )
                )
            continue
        parsed = _parse_single_include(item)
        if parsed is not None:
            result.append(parsed)
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
