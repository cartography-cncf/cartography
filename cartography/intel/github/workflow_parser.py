"""
GitHub Workflow YAML parser for extracting security-relevant information.

Parses workflow files to extract:
- Actions used and their versions (pinned vs unpinned)
- Secret references
- Permissions
- Reusable workflow calls
- Environment variables
"""

import logging
import re
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Tokenize only inside ${{ ... }}. Consume quoted literals as units so their
# contents (including }} and secrets.NAME) cannot become references. Keep
# double-quoted bracket selectors only for compatibility with existing inventory;
# GitHub rejects double-quoted strings in expressions.
EXPRESSION_TOKEN_PATTERN = re.compile(
    r"(?P<start>\$\{\{)|(?P<end>\}\})"
    r"|(?<![\w.-])secrets(?:"
    r"\.(?P<dot>[A-Za-z_][A-Za-z0-9_]*)"
    r"|\[\s*(?P<quote>['\"])(?P<bracket>[A-Za-z_][A-Za-z0-9_]*)(?P=quote)\s*\])"
    r"|'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\""
)

# SHA commit pattern (40 hex characters)
SHA_PATTERN = re.compile(r"^[a-f0-9]{40}$")


@dataclass
class ParsedAction:
    """Represents a parsed GitHub Action reference."""

    owner: str
    name: str
    version: str
    is_pinned: bool
    is_local: bool
    full_name: str
    raw_uses: str


@dataclass
class ParsedWorkflow:
    """Represents parsed workflow content."""

    actions: list[ParsedAction] = field(default_factory=list)
    secret_refs: list[str] = field(default_factory=list)
    permissions: dict[str, str] = field(default_factory=dict)
    trigger_events: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    reusable_workflow_calls: list[str] = field(default_factory=list)
    job_count: int = 0


def parse_action_reference(uses: str | None) -> ParsedAction | None:
    """
    Parse a GitHub Action 'uses' reference.

    Examples:
    - actions/checkout@v4
    - actions/checkout@a5ac7e51b41094c92402da3b24376905380afc29
    - docker://alpine:3.8
    - ./.github/actions/my-action
    - octo-org/this-repo/.github/workflows/workflow.yml@v1

    :param uses: The 'uses' string from a workflow step or job
    :return: ParsedAction or None if parsing fails
    """
    if not uses:
        return None

    uses = uses.strip()

    # Local action (starts with ./)
    if uses.startswith("./"):
        return ParsedAction(
            owner="",
            name=uses,
            version="",
            is_pinned=False,
            is_local=True,
            full_name=uses,
            raw_uses=uses,
        )

    # Docker action (starts with docker://)
    if uses.startswith("docker://"):
        image = uses[9:]  # Remove docker:// prefix
        return ParsedAction(
            owner="docker",
            name=image,
            version="",
            is_pinned=False,
            is_local=False,
            full_name=uses,
            raw_uses=uses,
        )

    # Standard action or reusable workflow: owner/repo@version or owner/repo/path@version
    if "@" in uses:
        ref_part, version = uses.rsplit("@", 1)
    else:
        ref_part = uses
        version = ""

    # Check if pinned to a SHA
    is_pinned = bool(SHA_PATTERN.match(version))

    # Parse owner/repo (possibly with path for reusable workflows)
    parts = ref_part.split("/")
    if len(parts) >= 2:
        owner = parts[0]
        name = "/".join(parts[1:])  # Handles owner/repo/path cases
    else:
        owner = ""
        name = ref_part

    return ParsedAction(
        owner=owner,
        name=name,
        version=version,
        is_pinned=is_pinned,
        is_local=False,
        full_name=f"{owner}/{name}" if owner else name,
        raw_uses=uses,
    )


def extract_secrets_from_string(content: str) -> set[str]:
    """Extract static secret references, including those in compound expressions.

    Quoted expression literals are skipped; this inventories references without
    evaluating branches, functions, or dynamic secret names.
    """
    result: set[str] = set()
    position = 0
    while (start := content.find("${{", position)) != -1:
        expression_start = start + 3
        references: set[str] = set()
        for token in EXPRESSION_TOKEN_PATTERN.finditer(content, expression_start):
            if token.group("start"):
                # Discard the incomplete expression and retry from the new opener.
                position = token.start()
                break
            if token.group("end"):
                result.update(references)
                position = token.end()
                break
            name = token.group("dot") or token.group("bracket")
            if name:
                # The lookbehind handles adjacent dots; also reject spaced members
                # such as inputs . secrets.NAME without copying the whole prefix.
                previous = token.start() - 1
                while previous >= expression_start and content[previous].isspace():
                    previous -= 1
                if previous < expression_start or content[previous] != ".":
                    references.add(name)
        else:
            # An incomplete expression cannot establish a reference.
            break
    return result


ALL_PERMISSION_SCOPES = [
    "actions",
    "contents",
    "packages",
    "pull_requests",
    "issues",
    "deployments",
    "statuses",
    "checks",
    "id_token",
    "security_events",
]


def parse_permissions(permissions: Any) -> dict[str, str]:
    """
    Parse workflow permissions block.

    Handles both string format (read-all, write-all) and dict format.
    Global permissions (read-all, write-all) are expanded to all scopes.

    :param permissions: The permissions value from the workflow
    :return: Dictionary of permission_name -> access_level
    """
    if permissions is None:
        return {}

    if isinstance(permissions, str):
        # Global permission level: expand to all scopes
        # e.g., "read-all" -> {"actions": "read", "contents": "read", ...}
        level = permissions.replace("-all", "")
        return {scope: level for scope in ALL_PERMISSION_SCOPES}

    if isinstance(permissions, dict):
        # Convert keys to use underscores for consistency
        return {k.replace("-", "_"): str(v) for k, v in permissions.items()}

    return {}


def _declared_permissions(permissions: Any) -> dict[str, str] | None:
    """Normalize an explicit block; None means its defaults are unknown."""
    if not isinstance(permissions, dict) and permissions not in (
        "read-all",
        "write-all",
    ):
        return None
    if isinstance(permissions, dict) and any(
        not isinstance(scope, str) for scope in permissions
    ):
        return None
    parsed = parse_permissions(permissions)
    if any(level not in ("none", "read", "write") for level in parsed.values()):
        return None
    # An explicit mapping replaces defaults, including scopes it omits.
    return {scope: parsed.get(scope, "none") for scope in ALL_PERMISSION_SCOPES}


def summarize_workflow_permissions(workflow: dict[str, Any]) -> dict[str, str]:
    """Summarize YAML job declarations without inferring runtime token access.

    Known writes survive unknown defaults. Otherwise an unknown job prevents
    a read/none conclusion. Missing scopes in the result represent uncertainty.
    """
    defaults = _declared_permissions(workflow.get("permissions"))
    jobs = workflow.get("jobs", {})
    declarations = []
    if isinstance(jobs, dict):
        for job in jobs.values():
            if isinstance(job, dict):
                declarations.append(
                    _declared_permissions(job["permissions"])
                    if "permissions" in job
                    else defaults
                )
    if not declarations:
        # Retain explicit workflow declarations even when no valid jobs exist.
        return defaults or {}
    summary = {}
    for scope in ALL_PERMISSION_SCOPES:
        levels = [job[scope] if job is not None else None for job in declarations]
        if "write" in levels:
            summary[scope] = "write"
        elif None not in levels:
            summary[scope] = "read" if "read" in levels else "none"
    return summary


def parse_workflow_yaml(content: str) -> ParsedWorkflow | None:
    """
    Parse a GitHub Actions workflow YAML file.

    :param content: The raw YAML content of the workflow file
    :return: ParsedWorkflow object or None if parsing fails
    """
    try:
        workflow = yaml.safe_load(content)
    except yaml.YAMLError:
        logger.warning("Failed to parse workflow YAML")
        return None

    if not isinstance(workflow, dict):
        logger.warning("Workflow YAML is not a dictionary")
        return None

    result = ParsedWorkflow()

    # Extract trigger events
    # Note: YAML parses 'on' as True (boolean), so we need to check both keys
    on_triggers = workflow.get("on") or workflow.get(True, {})
    if isinstance(on_triggers, str):
        result.trigger_events = [on_triggers]
    elif isinstance(on_triggers, list):
        result.trigger_events = on_triggers
    elif isinstance(on_triggers, dict):
        result.trigger_events = list(on_triggers.keys())

    # Resolve job overrides before summarizing declared permissions.
    result.permissions = summarize_workflow_permissions(workflow)

    # Extract top-level env vars
    env = workflow.get("env", {})
    if isinstance(env, dict):
        result.env_vars = list(env.keys())

    # Extract all secret references from the raw YAML content.
    # Using regex on the raw string is simpler and more complete than structured
    # traversal, catching secrets in env, with, run, if, outputs, strategy, etc.
    all_secrets = extract_secrets_from_string(content)

    # Process jobs
    jobs = workflow.get("jobs", {})
    if isinstance(jobs, dict):
        result.job_count = len(jobs)

        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue

            # Check for reusable workflow calls
            uses = job.get("uses")
            if uses:
                action = parse_action_reference(uses)
                if action:
                    # Reusable workflow call
                    if (
                        ".github/workflows/" in uses
                        or uses.endswith(".yml")
                        or uses.endswith(".yaml")
                    ):
                        result.reusable_workflow_calls.append(uses)
                    result.actions.append(action)

            # Process steps
            steps = job.get("steps", [])
            if isinstance(steps, list):
                for step in steps:
                    if not isinstance(step, dict):
                        continue

                    # Extract action references
                    step_uses = step.get("uses")
                    if step_uses:
                        action = parse_action_reference(step_uses)
                        if action:
                            result.actions.append(action)

    result.secret_refs = sorted(all_secrets)

    return result


def deduplicate_actions(actions: list[ParsedAction]) -> list[ParsedAction]:
    """
    Deduplicate actions by their raw_uses value.

    :param actions: List of parsed actions
    :return: Deduplicated list
    """
    seen: set[str] = set()
    unique: list[ParsedAction] = []
    for action in actions:
        if action.raw_uses not in seen:
            seen.add(action.raw_uses)
            unique.append(action)
    return unique
