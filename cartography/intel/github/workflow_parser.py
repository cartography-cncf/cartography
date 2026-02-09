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

# Regex pattern to match secret references: ${{ secrets.SECRET_NAME }}
SECRET_PATTERN = re.compile(r"\$\{\{\s*secrets\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

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
    """
    Extract all secret references from a string.

    :param content: String that may contain ${{ secrets.NAME }} references
    :return: Set of secret names found
    """
    return set(SECRET_PATTERN.findall(content))


def extract_secrets_from_value(value: Any, found_secrets: set[str]) -> None:
    """
    Recursively extract secret references from a YAML value.

    :param value: Any YAML value (string, dict, list, etc.)
    :param found_secrets: Set to accumulate found secret names
    """
    if isinstance(value, str):
        found_secrets.update(extract_secrets_from_string(value))
    elif isinstance(value, dict):
        for v in value.values():
            extract_secrets_from_value(v, found_secrets)
    elif isinstance(value, list):
        for item in value:
            extract_secrets_from_value(item, found_secrets)


def parse_permissions(permissions: Any) -> dict[str, str]:
    """
    Parse workflow permissions block.

    Handles both string format (read-all, write-all) and dict format.

    :param permissions: The permissions value from the workflow
    :return: Dictionary of permission_name -> access_level
    """
    if permissions is None:
        return {}

    if isinstance(permissions, str):
        # Global permission level: read-all, write-all, {}
        return {"_global": permissions}

    if isinstance(permissions, dict):
        # Convert keys to use underscores for consistency
        return {k.replace("-", "_"): str(v) for k, v in permissions.items()}

    return {}


def parse_workflow_yaml(content: str) -> ParsedWorkflow | None:
    """
    Parse a GitHub Actions workflow YAML file.

    :param content: The raw YAML content of the workflow file
    :return: ParsedWorkflow object or None if parsing fails
    """
    try:
        workflow = yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.warning(f"Failed to parse workflow YAML: {e}")
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

    # Extract top-level permissions
    result.permissions = parse_permissions(workflow.get("permissions"))

    # Extract top-level env vars
    env = workflow.get("env", {})
    if isinstance(env, dict):
        result.env_vars = list(env.keys())

    # Extract secrets from top-level env
    all_secrets: set[str] = set()
    extract_secrets_from_value(env, all_secrets)

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

            # Extract secrets from job-level with block
            job_with = job.get("with", {})
            extract_secrets_from_value(job_with, all_secrets)

            # Extract secrets from job-level secrets block (for reusable workflows)
            job_secrets = job.get("secrets", {})
            if isinstance(job_secrets, str) and job_secrets == "inherit":
                pass  # inherit doesn't expose specific secrets
            elif isinstance(job_secrets, dict):
                extract_secrets_from_value(job_secrets, all_secrets)

            # Extract secrets from job-level env
            job_env = job.get("env", {})
            extract_secrets_from_value(job_env, all_secrets)

            # Merge job-level permissions (not stored separately, just for completeness)
            job_permissions = parse_permissions(job.get("permissions"))
            if job_permissions and not result.permissions:
                result.permissions = job_permissions

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

                    # Extract secrets from step env
                    step_env = step.get("env", {})
                    extract_secrets_from_value(step_env, all_secrets)

                    # Extract secrets from step with
                    step_with = step.get("with", {})
                    extract_secrets_from_value(step_with, all_secrets)

                    # Extract secrets from run commands
                    run = step.get("run")
                    if run:
                        extract_secrets_from_value(run, all_secrets)

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
