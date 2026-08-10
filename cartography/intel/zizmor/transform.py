"""
Transform zizmor JSON v1 reports into rows loadable by ZizmorFindingSchema.

The format is documented at https://docs.zizmor.sh/usage/ and produced by
`zizmor --format=json-v1`. A few of its properties drive the code below:

- The document is a bare JSON array of findings, not an object. An empty result
  is `[]`.
- `determinations.severity`, `.confidence` and `.persona` are PascalCase while
  `fixes[].disposition` is lowercase. Everything is normalized to lowercase here.
- A finding has at least one location with `symbolic.kind == "Primary"`, and may
  have several: `undocumented-permissions`, for instance, emits one per
  undocumented permission key. Each primary location is a distinct problem, so
  each becomes its own node. Locations with kind `Hidden` exist only so zizmor
  can match `# zizmor: ignore` comments; they are dropped.
- `concrete.location` rows and columns are zero-based. They are converted to
  one-based to match the other finding types in the graph.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from dataclasses import field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ZizmorTransformResult:
    """
    Rows produced from one zizmor report, plus what could not be turned into one.

    `skipped` counts findings that were well-formed but not joinable to the
    graph. It is not a diagnostic: a caller that cleaned up stale findings after
    skipping some would delete findings that are still open.
    """

    rows: list[dict[str, Any]] = field(default_factory=list)
    skipped: int = 0


# Fields every finding must carry, and the type each must have. Presence alone is
# not enough: a null `ident` would otherwise be stringified into a synthetic
# "None" audit, which both invents a finding and changes the id of the real one,
# letting cleanup delete it.
_ZIZMOR_FINDING_REQUIRED_FIELDS: dict[str, type | tuple[type, ...]] = {
    "ident": str,
    "desc": str,
    "url": str,
    "determinations": dict,
    "locations": list,
}
_HIDDEN_LOCATION_KIND = "Hidden"
_PRIMARY_LOCATION_KIND = "Primary"
_WORKFLOW_ROOT_MARKER = ".github/"


def looks_like_zizmor_report(document: Any) -> bool:
    """
    Shape check for a zizmor JSON v1 report.

    Every finding is checked, not just the first. A report that is truncated or
    otherwise corrupt past its opening element must be rejected outright: if it
    were accepted, the entries the transform could not read would look like
    findings that no longer exist, and cleanup would delete them from the graph.
    An empty report is still a valid zizmor report.
    """
    if not isinstance(document, list):
        return False

    return all(_is_zizmor_finding(finding) for finding in document)


def _is_zizmor_finding(finding: Any) -> bool:
    if not isinstance(finding, dict):
        return False

    return all(
        isinstance(finding.get(name), expected_type)
        for name, expected_type in _ZIZMOR_FINDING_REQUIRED_FIELDS.items()
    )


def _normalize_workflow_path(key: Any) -> str | None:
    """
    Turn a zizmor input key into a repository-relative file path.

    `symbolic.key` is an externally tagged enum with three shapes:
    `{"Local": {"verbatim_path": ...}}`, `{"Remote": {"slug": ..., "path": ...}}`,
    and `{"Stdin": {}}`. Only the first two resolve to a path we can join on.
    """
    if not isinstance(key, dict):
        return None

    remote = key.get("Remote")
    if isinstance(remote, dict):
        # Remote paths are already relative to the repository root.
        path = remote.get("path")
        return path.strip() if isinstance(path, str) and path.strip() else None

    local = key.get("Local")
    if not isinstance(local, dict):
        # Stdin, or a future key variant we do not understand.
        return None

    verbatim_path = local.get("verbatim_path")
    if not isinstance(verbatim_path, str) or not verbatim_path.strip():
        return None

    path = verbatim_path.strip()
    # `verbatim_path` is whatever was passed on the command line, so it may be
    # absolute or prefixed with `./`. Cut at `.github/` to recover the path as
    # GitHubWorkflow.path stores it.
    marker_index = path.find(_WORKFLOW_ROOT_MARKER)
    if marker_index != -1:
        return path[marker_index:]

    while path.startswith("./"):
        path = path[2:]
    return path or None


def _format_route(symbolic: dict[str, Any]) -> str:
    """
    Flatten a yamlpath route into a dotted string, e.g. `jobs.greet.steps.0.run`.
    """
    route = symbolic.get("route")
    if not isinstance(route, dict):
        return ""

    components = route.get("route")
    if not isinstance(components, list):
        return ""

    parts: list[str] = []
    for component in components:
        if not isinstance(component, dict):
            continue
        if "Key" in component:
            parts.append(str(component["Key"]))
        elif "Index" in component:
            parts.append(str(component["Index"]))
    return ".".join(parts)


def _visible_locations(finding: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return the finding's locations, dropping zizmor's internal `Hidden` ones.
    """
    locations = finding.get("locations")
    if not isinstance(locations, list):
        return []

    visible: list[dict[str, Any]] = []
    for location in locations:
        if not isinstance(location, dict):
            continue
        symbolic = location.get("symbolic")
        if not isinstance(symbolic, dict):
            continue
        if symbolic.get("kind") == _HIDDEN_LOCATION_KIND:
            continue
        visible.append(location)
    return visible


def _primary_locations(locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Return the locations that carry the finding's actual problem.

    Several audits report more than one primary location, each of which is a
    separate problem the reader has to fix. `undocumented-permissions` emits one
    per undocumented permission key, for example.
    """
    primaries = [
        location
        for location in locations
        if location["symbolic"].get("kind") == _PRIMARY_LOCATION_KIND
    ]
    if primaries:
        return primaries
    # Defensive: zizmor always emits a primary location, but fall back to the
    # first visible one rather than dropping the finding.
    return locations[:1]


def _extract_uses_reference(locations: list[dict[str, Any]]) -> str | None:
    """
    Recover the raw `uses` reference a finding points at, if any.

    Rather than keying off a hardcoded list of audit idents, this looks for a
    location whose YAML route ends at a `uses` key. That covers unpinned-uses,
    impostor-commit, known-vulnerable-actions, stale-action-refs, ref-confusion,
    typosquat-uses, forbidden-uses, archived-uses and superfluous-actions without
    needing to track zizmor's audit registry.
    """
    for location in locations:
        if not _format_route(location["symbolic"]).endswith(".uses"):
            continue

        concrete = location.get("concrete")
        if not isinstance(concrete, dict):
            continue
        feature = concrete.get("feature")
        if not isinstance(feature, str):
            continue

        candidate = feature.strip()
        if candidate.startswith("uses:"):
            candidate = candidate[len("uses:") :].strip()
        # A KeyOnly location's feature is the bare key, which carries no value.
        if not candidate or candidate == "uses":
            continue
        return candidate.strip("\"'")
    return None


def _build_action_id(owner: str, repo: str, raw_uses: str) -> str:
    """
    Rebuild the GitHubAction id that the GitHub module assigns.

    See `transform_actions` in cartography/intel/github/actions.py: local actions
    are namespaced by repository because they are repo-specific, everything else
    is namespaced by organization.
    """
    if raw_uses.startswith("./"):
        return f"{owner}/{repo}:{raw_uses}"
    return f"{owner}:{raw_uses}"


def _build_zizmor_finding_id(
    audit_id: str,
    repository_url: str,
    file_path: str,
    route: str,
    feature_kind: Any,
) -> str:
    """
    Build a stable synthetic ID, since zizmor JSON v1 has no finding identifier.

    The YAML route is preferred over line numbers because it survives unrelated
    edits to the file. `feature_kind` carries the sub-feature offset and fragment,
    which distinguishes two findings of the same audit within one block.
    """
    raw_id = "|".join(
        [
            audit_id,
            repository_url,
            file_path,
            route,
            json.dumps(feature_kind, sort_keys=True),
        ],
    )
    digest = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()
    return f"zizmor-{digest}"


def _lower(value: Any) -> str | None:
    return value.lower() if isinstance(value, str) else None


def _to_one_based(value: Any) -> int | None:
    return value + 1 if isinstance(value, int) and not isinstance(value, bool) else None


def transform_zizmor_report(
    document: list[dict[str, Any]],
    repo_context: dict[str, str],
) -> ZizmorTransformResult:
    """
    Transform a zizmor JSON v1 report into rows loadable by ZizmorFindingSchema.

    A malformed finding raises rather than being skipped: the report cannot be
    trusted to describe the repository's current state, and treating it as
    complete would make cleanup delete findings that are in fact still open.

    Findings that are well-formed but cannot be joined to the graph, such as one
    read from stdin, are skipped and counted in `skipped`. The caller must treat
    a report with skipped findings as incompletely observed for the same reason.
    """
    if not isinstance(document, list):
        raise ValueError("Zizmor report must be a top-level list of findings.")

    transformed: list[dict[str, Any]] = []
    skipped = 0

    for finding in document:
        if not _is_zizmor_finding(finding):
            raise ValueError(
                "Zizmor report contains an entry that is not a finding: "
                f"{str(finding)[:200]}"
            )

        locations = _visible_locations(finding)
        primaries = _primary_locations(locations)
        if not primaries:
            logger.warning(
                "Skipping zizmor %s finding with no usable location.",
                finding.get("ident"),
            )
            skipped += 1
            continue
        related = [location for location in locations if location not in primaries]

        # Types of the required fields are guaranteed by _is_zizmor_finding above.
        audit_id = finding["ident"]
        determinations = finding["determinations"]
        # `fixes` is optional: zizmor omits it for audits that cannot autofix.
        fixes = finding.get("fixes")
        fixes = fixes if isinstance(fixes, list) else []

        for primary in primaries:
            symbolic = primary["symbolic"]
            file_path = _normalize_workflow_path(symbolic.get("key"))
            if file_path is None:
                # Stdin input, or a path we cannot make repository-relative.
                logger.warning(
                    "Skipping zizmor %s finding with no joinable file path.",
                    audit_id,
                )
                skipped += 1
                continue

            route = _format_route(symbolic)
            concrete = primary.get("concrete") or {}
            location = concrete.get("location") or {}
            start_point = location.get("start_point") or {}
            end_point = location.get("end_point") or {}

            raw_uses = _extract_uses_reference([primary, *related])

            row: dict[str, Any] = {
                "id": _build_zizmor_finding_id(
                    audit_id,
                    repo_context["repositoryUrl"],
                    file_path,
                    route,
                    symbolic.get("feature_kind"),
                ),
                "audit_id": audit_id,
                "description": finding["desc"],
                "url": finding["url"],
                "severity": _lower(determinations.get("severity")),
                "confidence": _lower(determinations.get("confidence")),
                "persona": _lower(determinations.get("persona")),
                "ignored": bool(finding.get("ignored", False)),
                "file_path": file_path,
                "yaml_route": route,
                "uses_reference": raw_uses,
                "action_id": (
                    _build_action_id(
                        repo_context["owner"],
                        repo_context["repo"],
                        raw_uses,
                    )
                    if raw_uses
                    else None
                ),
                "annotation": symbolic.get("annotation"),
                "snippet": concrete.get("feature"),
                # zizmor emits zero-based rows and columns.
                "start_line": _to_one_based(start_point.get("row")),
                "start_col": _to_one_based(start_point.get("column")),
                "end_line": _to_one_based(end_point.get("row")),
                "end_col": _to_one_based(end_point.get("column")),
                "fix_titles": [
                    fix["title"]
                    for fix in fixes
                    if isinstance(fix, dict) and isinstance(fix.get("title"), str)
                ],
                "fix_dispositions": [
                    fix["disposition"]
                    for fix in fixes
                    if isinstance(fix, dict) and isinstance(fix.get("disposition"), str)
                ],
            }
            row.update(repo_context)

            transformed.append(row)

    return ZizmorTransformResult(rows=transformed, skipped=skipped)
