import json
import logging
import re
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import no_type_check

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator

logger = logging.getLogger(__name__)

_RETURN_KEYWORD_RE = re.compile(r"(?i)\bRETURN\b")
# Clauses that follow the projection and produce no output columns.
_TRAILING_CLAUSE_RE = re.compile(r"(?is)\b(?:ORDER\s+BY|SKIP|LIMIT)\b")
_LEADING_DISTINCT_RE = re.compile(r"(?is)^\s*DISTINCT\b")
# `<expr> AS alias`, only when the alias ends the projection item.
_ITEM_ALIAS_RE = re.compile(r"(?is)\bAS\s+(\w+)\s*$")
_BARE_IDENTIFIER_RE = re.compile(r"^\w+$")
# `foo.bar` / `foo .bar`: which variables an expression reads properties from.
_PROPERTY_OWNER_RE = re.compile(r"\b(\w+)\s*\.")

# Fields the `Finding` base model owns. A fact query must not alias them: both
# are populated by `Rule.parse_results` and a query column of the same name
# would silently overwrite the framework-supplied value.
RESERVED_FINDING_FIELDS = frozenset({"source", "extra"})


def _depths(text: str) -> list[int]:
    """Bracket nesting depth at each character of `text`."""
    depths, depth = [], 0
    for char in text:
        if char in ")]}":
            depth -= 1
        depths.append(depth)
        if char in "([{":
            depth += 1
    return depths


def _final_return_projection(cypher_query: str) -> str:
    """Return the projection body of the query's last `RETURN`.

    Everything before that `RETURN` is intermediate query state: a `WITH x AS y`
    binding is not an output column, so it must not count as one.
    """
    query_depths = _depths(cypher_query)
    # The projection is the last top-level RETURN: one nested inside a `CALL { ...
    # RETURN ... }` subquery sits at a deeper bracket level and is not it.
    starts = [
        match.end()
        for match in _RETURN_KEYWORD_RE.finditer(cypher_query)
        if query_depths[match.start()] == 0
    ]
    if not starts:
        return ""
    projection = cypher_query[starts[-1] :]
    depths = _depths(projection)
    for trailing in _TRAILING_CLAUSE_RE.finditer(projection):
        # Only a top-level ORDER BY / SKIP / LIMIT ends the projection; the same
        # keyword inside a subquery or list expression does not.
        if depths[trailing.start()] == 0:
            projection = projection[: trailing.start()]
            break
    return _LEADING_DISTINCT_RE.sub("", projection)


def _projection_items(cypher_query: str) -> list[str]:
    """Split the final projection on its top-level commas.

    Depth-aware because items legitimately contain commas: `coalesce(a, b)`,
    `[x IN xs WHERE ...]`, `CASE WHEN ... END`.
    """
    projection = _final_return_projection(cypher_query)
    depths = _depths(projection)
    items, start = [], 0
    for index, char in enumerate(projection):
        if char == "," and depths[index] == 0:
            items.append(projection[start:index])
            start = index + 1
    items.append(projection[start:])
    return [item.strip() for item in items if item.strip()]


def returned_aliases(cypher_query: str) -> set[str]:
    """Return the output column names of a fact query's final `RETURN`.

    A column is named by its `AS <alias>`, or by the variable itself when the
    item is a bare identifier carried over from an earlier `WITH`. Items that
    are neither (e.g. a bare `n.prop`) get a Cypher-generated column name that
    can never be a Python field name, so they are ignored.
    """
    names = set()
    for item in _projection_items(cypher_query):
        alias = _ITEM_ALIAS_RE.search(item)
        if alias:
            names.add(alias.group(1))
        elif _BARE_IDENTIFIER_RE.match(item):
            names.add(item)
    return names


def _variables_bound_to_label(cypher_query: str, label: str) -> set[str]:
    """Variables the query binds to `label`, inline or as a predicate.

    Covers `(v:Label)`, `(v:Label {...})` and `WHERE v:Label`.
    """
    return set(re.findall(rf"\b(\w+)\s*:\s*{re.escape(label)}\b", cypher_query))


def _expression_for_alias(cypher_query: str, alias: str) -> str | None:
    """The projection expression the final `RETURN` exposes as `alias`."""
    for item in _projection_items(cypher_query):
        match = _ITEM_ALIAS_RE.search(item)
        if match and match.group(1) == alias:
            return item[: match.start()].strip()
        if not match and item == alias:
            return item
    return None


# ---------------------------------------------------------------------------
# Fan-out analysis: can `identity_fields` key the rows the query returns?
#
# `identity_fields` is a promise that two rows of the same fact never share an
# identity. The shape that breaks it is a query that fans out over a to-many hop
# while the identity omits the fan-out column, so one asset yields several
# findings with one identity and a consumer reconciling across syncs cannot tell
# them apart. The helpers below find that shape statically; the cardinality of
# each relationship is *injected* by the caller, so this module stays free of
# per-module assertions about the graph.
#
# Known blind spots, all of them under-reporting rather than false alarms:
# cartesian-product fan-out (two patterns joined by a property equality rather
# than a relationship), a top-level `UNION`, variables returned out of a
# `CALL { ... }` subquery, and `UNWIND` over a list expression.
#
# The analysis is also about variables, not values. A variable counts as pinned
# once an identity field is read off it, which assumes that column keys the node.
# Where it does not, several distinct nodes still collapse to one identity and
# this cannot see it: a `Dependency` is keyed on its requirement string, so one
# repo can hold two nodes for one version ('6.2.1' and '= 6.2.1') that share the
# identity but differ in a displayed column.
# ---------------------------------------------------------------------------

# Functions that collapse many rows into one value. `size()` is deliberately
# absent: it measures a list, it does not aggregate rows.
_AGGREGATE_FUNCTIONS = frozenset(
    {
        "collect",
        "count",
        "sum",
        "avg",
        "min",
        "max",
        "stdev",
        "stdevp",
        "percentilecont",
        "percentiledisc",
    }
)
_AGGREGATE_CALL_RE = re.compile(
    rf"(?i)\b({'|'.join(sorted(_AGGREGATE_FUNCTIONS))})\s*\("
)
_CLAUSE_KEYWORD_RE = re.compile(
    r"(?is)\b(OPTIONAL\s+MATCH|MATCH|WHERE|WITH|RETURN|UNWIND|CALL|UNION"
    r"|ORDER\s+BY|SKIP|LIMIT)\b"
)
_PATH_ASSIGNMENT_RE = re.compile(r"^\s*\w+\s*=")
_NODE_VARIABLE_RE = re.compile(r"^\s*(\w+)")
_LABEL_RE = re.compile(r"[:|]\s*(\w+)")
# An identifier that is not a property name (`n.prop`) and not an alias keyword.
_IDENTIFIER_RE = re.compile(r"(?<![\w.])[A-Za-z_]\w*")
_ANONYMOUS_PREFIX = "__anon"


@dataclass(frozen=True)
class FanoutRisk:
    """A query variable that multiplies rows without being pinned by the identity."""

    variable: str
    condition: str
    """``"projected"``: the variable contributes an un-aggregated output column that no
    identity field pins, so its rows differ in a column the identity ignores.
    ``"invisible"``: the variable contributes nothing to the projection, so it only
    duplicates rows."""
    detail: str
    """Human-readable explanation, meant for a test failure message."""


@dataclass(frozen=True)
class _Hop:
    """One relationship step of a Cypher pattern, as written."""

    left: str
    right: str
    direction: str
    """``"->"``, ``"<-"`` or ``"--"``."""
    rel_labels: frozenset[str]
    variable_length: bool


def _sanitize_cypher(cypher_query: str) -> str:
    """Mask comments and string-literal bodies, preserving every character position.

    Length-preserving so indices and bracket depths computed here stay valid against
    the original query. Necessary because a `//` inside a string literal
    (`'https://mail.google.com/'`) would otherwise swallow the rest of the line and
    unbalance the query.
    """
    result = list(cypher_query)
    index, length = 0, len(cypher_query)
    while index < length:
        char = cypher_query[index]
        if char == "/" and cypher_query.startswith("//", index):
            while index < length and cypher_query[index] != "\n":
                result[index] = " "
                index += 1
        elif char in "'\"`":
            quote = char
            index += 1
            while index < length and cypher_query[index] != quote:
                if cypher_query[index] == "\\" and index + 1 < length:
                    result[index] = "x"
                    index += 1
                result[index] = "x"
                index += 1
            index += 1
        else:
            index += 1
    return "".join(result)


def _split_top_level(text: str, separator: str = ",") -> list[str]:
    """Split `text` on `separator` occurrences that sit outside every bracket."""
    depths = _depths(text)
    parts, start = [], 0
    for index, char in enumerate(text):
        if char == separator and depths[index] == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return [part.strip() for part in parts if part.strip()]


def _split_on_top_level_keyword(text: str, keyword: str) -> list[str]:
    """Split `text` on occurrences of `keyword` that sit outside every bracket."""
    depths = _depths(text)
    pattern = re.compile(rf"(?i)\b{re.escape(keyword)}\b")
    parts, start = [], 0
    for match in pattern.finditer(text):
        if depths[match.start()] == 0:
            parts.append(text[start : match.start()])
            start = match.end()
    parts.append(text[start:])
    return [part for part in parts if part.strip()]


def _top_level_clauses(sanitized_query: str) -> list[tuple[str, str]]:
    """`(KEYWORD, body)` for every clause at bracket depth 0.

    A `CALL { ... }` body sits at a deeper level, so its clauses are not returned:
    variables bound only inside a subquery cannot multiply the outer rows.
    """
    depths = _depths(sanitized_query)
    starts = [
        match
        for match in _CLAUSE_KEYWORD_RE.finditer(sanitized_query)
        if depths[match.start()] == 0
    ]
    clauses = []
    for position, match in enumerate(starts):
        end = starts[position + 1].start() if position + 1 < len(starts) else None
        keyword = " ".join(match.group(1).upper().split())
        clauses.append((keyword, sanitized_query[match.end() : end]))
    return clauses


def _parse_node(interior: str, anonymous_count: int) -> tuple[str, set[str]]:
    """`(variable, labels)` of one node pattern, naming anonymous nodes so a path
    can be chained through them."""
    before_properties = interior.split("{", 1)[0]
    labels = set(_LABEL_RE.findall(before_properties))
    name_match = _NODE_VARIABLE_RE.match(before_properties)
    if name_match and not before_properties.lstrip().startswith(":"):
        return name_match.group(1), labels
    return f"{_ANONYMOUS_PREFIX}{anonymous_count}", labels


def _parse_connector(text: str) -> tuple[str, frozenset[str], bool]:
    """`(direction, relationship labels, is variable length)` of a pattern connector."""
    stripped = text.strip()
    if stripped.endswith(">"):
        direction = "->"
    elif stripped.startswith("<"):
        direction = "<-"
    else:
        direction = "--"
    bracket = (
        stripped[stripped.find("[") + 1 : stripped.rfind("]")]
        if "[" in stripped
        else ""
    )
    before_properties = bracket.split("{", 1)[0]
    return (
        direction,
        frozenset(_LABEL_RE.findall(before_properties)),
        "*" in before_properties,
    )


def _pattern_hops(
    pattern: str, anonymous_count: int
) -> tuple[dict[str, set[str]], list[_Hop], int]:
    """Parse a MATCH pattern into its variables, its hops, and the anon counter."""
    variables: dict[str, set[str]] = {}
    hops: list[_Hop] = []
    for sub_pattern in _split_top_level(pattern):
        sub_pattern = _PATH_ASSIGNMENT_RE.sub("", sub_pattern, count=1)
        nodes: list[str] = []
        connectors: list[str] = []
        paren_depth = bracket_depth = brace_depth = 0
        node_start = last_end = 0
        for index, char in enumerate(sub_pattern):
            if char == "[":
                bracket_depth += 1
            elif char == "]":
                bracket_depth -= 1
            elif char == "{":
                brace_depth += 1
            elif char == "}":
                brace_depth -= 1
            elif char == "(" and bracket_depth == 0 and brace_depth == 0:
                if paren_depth == 0:
                    node_start = index
                    connectors.append(sub_pattern[last_end:index])
                paren_depth += 1
            elif char == ")" and bracket_depth == 0 and brace_depth == 0:
                paren_depth -= 1
                if paren_depth == 0:
                    name, labels = _parse_node(
                        sub_pattern[node_start + 1 : index], anonymous_count
                    )
                    if name.startswith(_ANONYMOUS_PREFIX):
                        anonymous_count += 1
                    nodes.append(name)
                    variables.setdefault(name, set()).update(labels)
                    last_end = index + 1
        for position in range(1, len(nodes)):
            direction, rel_labels, variable_length = _parse_connector(
                connectors[position]
            )
            hops.append(
                _Hop(
                    left=nodes[position - 1],
                    right=nodes[position],
                    direction=direction,
                    rel_labels=rel_labels,
                    variable_length=variable_length,
                )
            )
    return variables, hops, anonymous_count


def _alias_expressions(clauses: list[tuple[str, str]]) -> dict[str, str]:
    """`alias -> source expression` for every `... AS alias` the query binds."""
    expressions: dict[str, str] = {}
    for keyword, body in clauses:
        if keyword in ("WITH", "RETURN"):
            items = _split_top_level(_LEADING_DISTINCT_RE.sub("", body))
        elif keyword == "UNWIND":
            items = [body]
        else:
            continue
        for item in items:
            match = _ITEM_ALIAS_RE.search(item)
            if not match:
                continue
            alias, source = match.group(1), item[: match.start()].strip()
            # `x AS x` re-binds a column to itself. Recording it would erase the
            # earlier definition that says what `x` actually reads.
            if source != alias:
                expressions[alias] = source
    return expressions


def _expand_aliases(
    expression: str,
    alias_expressions: dict[str, str],
    _seen: frozenset[str] = frozenset(),
) -> str:
    """Substitute aliases back to their source expressions.

    So `RETURN ip AS external_ip` after `WITH access.public_ip AS ip` still resolves to
    a read off `access`. An alias already expanded on the current path is left alone, so
    a rebinding such as `WITH head(collect(user_label)) AS user` terminates.
    """

    def replace(match: re.Match) -> str:
        name = match.group(0)
        source = alias_expressions.get(name)
        if source is None or name in _seen or source.strip() == name:
            return name
        return f"({_expand_aliases(source, alias_expressions, _seen | {name})})"

    return _IDENTIFIER_RE.sub(replace, expression)


def _aggregate_spans(expression: str) -> list[tuple[int, int]]:
    """Character ranges of `expression` covered by an aggregating function call."""
    spans = []
    for match in _AGGREGATE_CALL_RE.finditer(expression):
        depth = 0
        for index in range(match.end() - 1, len(expression)):
            if expression[index] == "(":
                depth += 1
            elif expression[index] == ")":
                depth -= 1
                if depth == 0:
                    spans.append((match.start(), index + 1))
                    break
    return spans


def _variable_usage(expression: str, variable: str) -> tuple[bool, bool]:
    """`(collapsed by an aggregate, read outside every aggregate)`.

    Collapsed covers both `count(sg)` and `collect(sg.name)`: either way the variable's
    rows fold into a single value. Read-outside means the expression exposes one of the
    variable's properties as its own value, which is what makes a fan-out visible in the
    output. A bare carry-through (`WITH a, b, c`) is neither: it moves the variable along
    without folding it or reading anything off it.
    """
    spans = _aggregate_spans(expression)
    collapsed = read_outside = False
    for match in re.finditer(rf"(?<![\w.])({re.escape(variable)})\s*(\.?)", expression):
        if any(start <= match.start() < end for start, end in spans):
            collapsed = True
        elif match.group(2):
            read_outside = True
    return collapsed, read_outside


def _anti_joined_variables(clauses: list[tuple[str, str]]) -> set[str]:
    """Variables an `OPTIONAL MATCH ... WHERE <var> IS NULL` anti-join pins to null.

    The idiom keeps only the rows where the optional pattern found nothing, so the
    variable is null in every surviving row and cannot multiply them. Only conjunctive
    top-level predicates count: under an `OR` the variable may still be bound.
    """
    pinned = set()
    for keyword, body in clauses:
        if keyword != "WHERE":
            continue
        depths = _depths(body)
        if any(
            depths[match.start()] == 0 for match in re.finditer(r"(?i)\bOR\b", body)
        ):
            continue
        for conjunct in _split_on_top_level_keyword(body, "AND"):
            match = re.match(r"(?is)^(\w+)\s+IS\s+NULL$", conjunct.strip())
            if match:
                pinned.add(match.group(1))
    return pinned


def _hop_is_to_one(
    hop: _Hop,
    source: str,
    variables: dict[str, set[str]],
    to_one_incoming: frozenset[tuple[str, str]],
    to_one_outgoing: frozenset[tuple[str, str]],
) -> bool:
    """Does traversing `hop` away from `source` reach at most one node?

    Both tables are keyed on `(relationship label, label of the arrow target)`, never on
    the label alone: `CONTAINS` and `OWNS` are each used for a to-one edge in one module
    and a to-many edge in another.
    """
    if hop.variable_length or hop.direction == "--":
        return False
    target_is_right = hop.direction == "->"
    arrow_target = hop.right if target_is_right else hop.left
    moving_with_arrow = source == (hop.left if target_is_right else hop.right)
    table = to_one_outgoing if moving_with_arrow else to_one_incoming
    labels = variables.get(arrow_target, set())
    for rel_label in hop.rel_labels or {""}:
        if (rel_label, "*") in table:
            return True
        if any((rel_label, label) in table for label in labels):
            return True
    return False


def fanout_risks(
    cypher_query: str,
    asset_label: str,
    identity_fields: tuple[str, ...],
    *,
    to_one_incoming: frozenset[tuple[str, str]],
    to_one_outgoing: frozenset[tuple[str, str]],
) -> list[FanoutRisk]:
    """Variables whose row fan-out `identity_fields` does not account for.

    Multiplicity is measured relative to the identity, not to the anchor: a variable is
    pinned when it holds the anchor, when an identity field is read off it, or when it is
    reachable from a pinned variable through hops that yield at most one node. Anything
    else connected to that set multiplies rows, and is reported unless the query collapses
    it (an aggregate) or hides it (no output column, plus `RETURN DISTINCT`).
    """
    sanitized = _sanitize_cypher(cypher_query)
    clauses = _top_level_clauses(sanitized)

    variables: dict[str, set[str]] = {}
    hops: list[_Hop] = []
    anonymous_count = 0
    for keyword, body in clauses:
        if keyword not in ("MATCH", "OPTIONAL MATCH"):
            continue
        pattern_variables, pattern_hops, anonymous_count = _pattern_hops(
            body, anonymous_count
        )
        for name, labels in pattern_variables.items():
            variables.setdefault(name, set()).update(labels)
        hops.extend(pattern_hops)

    alias_expressions = _alias_expressions(clauses)
    pinned = {name for name, labels in variables.items() if asset_label in labels}
    for identity_field in identity_fields:
        expanded = _expand_aliases(
            alias_expressions.get(identity_field, identity_field), alias_expressions
        )
        pinned |= {name for name in variables if any(_variable_usage(expanded, name))}
    if not pinned:
        # No anchor and no identity read off a matched variable: there is no reference
        # point to measure fan-out against.
        return []
    pinned |= _anti_joined_variables(clauses) & set(variables)

    # Grow the pinned set through to-one hops, and separately track everything the
    # pattern connects to it. A variable joined only by a property equality is neither,
    # and is left alone rather than reported as a guess.
    connected = set(pinned)
    changed = True
    while changed:
        changed = False
        for hop in hops:
            for source, other in ((hop.left, hop.right), (hop.right, hop.left)):
                if source not in connected or other in pinned:
                    continue
                if other not in connected:
                    connected.add(other)
                    changed = True
                if source in pinned and _hop_is_to_one(
                    hop, source, variables, to_one_incoming, to_one_outgoing
                ):
                    pinned.add(other)
                    changed = True

    # Tested on the raw clause body: `_final_return_projection` has already stripped
    # the keyword by the time it returns.
    return_bodies = [body for keyword, body in clauses if keyword == "RETURN"]
    returns_distinct = bool(
        return_bodies and _LEADING_DISTINCT_RE.match(return_bodies[-1])
    )
    raw_projection = _projection_items(sanitized)
    # An aggregate in the final projection makes Cypher group by the remaining
    # expressions, which folds away every variable that contributes none of them, just
    # as DISTINCT would. Checked before alias expansion on purpose: expansion pulls in
    # aggregates from earlier `WITH` clauses, which group at that point, not here.
    projection_aggregates = any(_aggregate_spans(item) for item in raw_projection)
    projected = [_expand_aliases(item, alias_expressions) for item in raw_projection]
    carried = [
        _expand_aliases(item, alias_expressions)
        for keyword, body in clauses
        if keyword in ("WITH", "RETURN")
        for item in _split_top_level(_LEADING_DISTINCT_RE.sub("", body))
    ]

    risks = []
    for variable in sorted(connected - pinned):
        if variable.startswith(_ANONYMOUS_PREFIX):
            continue
        if any(_variable_usage(item, variable)[1] for item in projected):
            risks.append(
                FanoutRisk(
                    variable=variable,
                    condition="projected",
                    detail=(
                        f"'{variable}' multiplies rows and contributes an un-aggregated "
                        f"output column, but no identity field is read off it"
                    ),
                )
            )
        elif not any(_variable_usage(item, variable)[0] for item in carried):
            if not returns_distinct and not projection_aggregates:
                risks.append(
                    FanoutRisk(
                        variable=variable,
                        condition="invisible",
                        detail=(
                            f"'{variable}' multiplies rows without contributing any "
                            f"output column, so identical rows repeat"
                        ),
                    )
                )
    return risks


class Module(str, Enum):
    """Services that can be monitored"""

    AIBOM = "AIBOM"
    """AI BOM inventory mapped onto container images"""

    AIRBYTE = "Airbyte"
    """Airbyte data integration"""

    ANTHROPIC = "Anthropic"
    """Anthropic AI"""

    AWS = "AWS"
    """Amazon Web Services"""

    AZURE = "Azure"
    """Microsoft Azure"""

    BIGFIX = "BigFix"
    """BigFix patch management"""

    CLOUDFLARE = "Cloudflare"
    """Cloudflare services"""

    CROWDSTRIKE = "CrowdStrike"
    """CrowdStrike endpoint security"""

    DATABRICKS = "Databricks"
    """Databricks lakehouse platform"""

    DIGITALOCEAN = "DigitalOcean"
    """DigitalOcean cloud services"""

    DUO = "Duo"
    """Duo authentication"""

    MICROSOFT = "microsoft"
    """Microsoft Entra identity and access management"""

    GCP = "GCP"
    """Google Cloud Platform"""

    GITHUB = "GitHub"
    """GitHub source code management"""

    GITLAB = "GitLab"
    """GitLab source code management"""

    GOOGLEWORKSPACE = "googleworkspace"
    """Google Workspace identity and access management"""

    JAMF = "Jamf"
    """Jamf endpoint security"""

    JUMPCLOUD = "JumpCloud"
    """JumpCloud identity and device management"""

    KANDJI = "Kandji"
    """Kandji endpoint security"""

    KEYCLOAK = "Keycloak"
    """Keycloak identity and access management"""

    KUBERNETES = "Kubernetes"
    """Kubernetes cluster security"""

    LASTPASS = "LastPass"
    """LastPass password manager"""

    OCI = "OCI"
    """Oracle Cloud Infrastructure"""

    OKTA = "Okta"
    """Okta identity and access management"""

    OPENAI = "OpenAI"
    """OpenAI"""

    PAGERDUTY = "PagerDuty"
    """PagerDuty incident response"""

    RAILWAY = "Railway"
    """Railway platform-as-a-service"""

    SCALEWAY = "Scaleway"
    """Scaleway cloud services"""

    SUPABASE = "Supabase"
    """Supabase backend-as-a-service"""

    SEMGREP = "Semgrep"
    """Semgrep code security"""

    SENTINELONE = "SentinelOne"
    """SentinelOne endpoint security"""

    SNIPEIT = "snipeit"
    """Snipe-IT asset management"""

    SPACELIFT = "SpaceLift"
    """SpaceLift infrastructure as code"""

    TAILSCALE = "TailScale"
    """TailScale VPN"""

    TRIVY = "Trivy"
    """Trivy vulnerability scanner"""

    SUBIMAGE = "SubImage"
    """SubImage platform"""

    CROSS_CLOUD = "Cross-Cloud"
    """Multi-cloud or provider-agnostic rules"""


class Maturity(str, Enum):
    """Maturity levels for Facts."""

    EXPERIMENTAL = "EXPERIMENTAL"
    """Experimental: Initial version, may be unstable or incomplete."""

    STABLE = "STABLE"
    """Stable: Well-tested and reliable for production use."""


MODULE_TO_CARTOGRAPHY_INTEL = {
    Module.AIBOM: "aibom",
    Module.AIRBYTE: "airbyte",
    Module.ANTHROPIC: "anthropic",
    Module.AWS: "aws",
    Module.AZURE: "azure",
    Module.BIGFIX: "bigfix",
    Module.CLOUDFLARE: "cloudflare",
    Module.CROWDSTRIKE: "crowdstrike",
    Module.DATABRICKS: "databricks",
    Module.DIGITALOCEAN: "digitalocean",
    Module.DUO: "duo",
    Module.MICROSOFT: "microsoft",
    Module.GCP: "gcp",
    Module.GITHUB: "github",
    Module.GITLAB: "gitlab",
    Module.GOOGLEWORKSPACE: "googleworkspace",
    Module.JAMF: "jamf",
    Module.JUMPCLOUD: "jumpcloud",
    Module.KANDJI: "kandji",
    Module.KEYCLOAK: "keycloak",
    Module.KUBERNETES: "kubernetes",
    Module.LASTPASS: "lastpass",
    Module.OCI: "oci",
    Module.OKTA: "okta",
    Module.OPENAI: "openai",
    Module.PAGERDUTY: "pagerduty",
    Module.RAILWAY: "railway",
    Module.SCALEWAY: "scaleway",
    Module.SUPABASE: "supabase",
    Module.SEMGREP: "semgrep",
    Module.SENTINELONE: "sentinelone",
    Module.SNIPEIT: "snipeit",
    Module.SPACELIFT: "spacelift",
    Module.TAILSCALE: "tailscale",
    Module.TRIVY: "trivy",
    Module.SUBIMAGE: "subimage",
}


@dataclass(frozen=True)
class Framework:
    """
    A reference to a compliance framework requirement/control mapping.

    A rule can map to many framework controls, and many rules can map to the same
    framework control. The mapped control title is external framework metadata,
    not the rule display name.

    Matching fields are case-insensitive and normalized to lowercase on creation.
    The optional control_title preserves display casing because it is user-facing
    copy.

    Attributes:
        name: Full name of the framework (e.g., "cis aws foundations benchmark").
        short_name: Abbreviated name for filtering (e.g., "cis").
        requirement: The specific requirement/control id (e.g., "5.1.8", "8.2", "govern 5").
        scope: Optional platform or domain the framework applies to (e.g., "aws", "gcp").
        revision: Optional version/revision of the framework (e.g., "5.0").
        control_title: Optional external control or requirement title for this framework mapping.
    """

    name: str
    short_name: str
    requirement: str
    scope: str | None = None
    revision: str | None = None
    control_title: str | None = None

    def __post_init__(self) -> None:
        # Normalize matching fields to lowercase for case-insensitive comparison.
        # Keep control_title casing intact because it is display copy, not a filter key.
        object.__setattr__(self, "name", self.name.lower())
        object.__setattr__(self, "short_name", self.short_name.lower())
        object.__setattr__(self, "requirement", self.requirement.lower())
        if self.scope is not None:
            object.__setattr__(self, "scope", self.scope.lower())
        if self.revision is not None:
            object.__setattr__(self, "revision", self.revision.lower())

    def matches(
        self,
        short_name: str | None = None,
        scope: str | None = None,
        revision: str | None = None,
    ) -> bool:
        """
        Check if this framework matches the given filter criteria.

        Args:
            short_name: Filter by short name (case-insensitive).
            scope: Filter by scope (case-insensitive).
            revision: Filter by revision (case-insensitive).

        Returns:
            True if all provided criteria match, False otherwise.
        """
        if short_name and self.short_name != short_name.lower():
            return False
        if scope:
            if self.scope is None or self.scope != scope.lower():
                return False
        if revision:
            if self.revision is None or self.revision != revision.lower():
                return False
        return True


@dataclass(frozen=True)
class RuleReference:
    """A reference document for a Rule."""

    text: str
    url: str


@dataclass(frozen=True)
class Fact:
    """A Fact gathers information about the environment using a Cypher query."""

    id: str
    """A descriptive identifier for the Fact. By convention, should be lowercase and use underscores like `rule-name-module`."""
    name: str
    """A descriptive name for the Fact."""
    description: str
    """More details about the Fact. Information on details that we're querying for."""
    module: Module
    """The Module that the Fact is associated with e.g. AWS, Azure, GCP, etc."""
    maturity: Maturity
    """The maturity level of the Fact query."""
    # TODO can we lint the queries. full-on integ tests here are overkill though.
    cypher_query: str
    """The Cypher query to gather information about the environment. Returns data field by field e.g. `RETURN node.prop1, node.prop2`."""
    cypher_visual_query: str
    """
    Same as `cypher_query`, returns it in a visual format for the web interface with `.. RETURN *`.
    Often includes additional relationships to help give context.
    """
    cypher_count_query: str
    """
    A query that returns the total count of assets of the type being evaluated by this Fact.
    This count includes all assets regardless of whether they match the Fact criteria.
    Should return a single value with `RETURN COUNT(...) AS count`.
    """
    identity_fields: tuple[str, ...]
    """Output-model field(s) forming the stable logical identity of a finding across syncs; must exist on the output model and be returned by ``cypher_query``, and are distinct from volatile display fields and from ``asset_id_field`` (which only drives the compliance failing-count). Required with no default: a Fact that omits it fails to construct, forcing every rule to declare a stable identity explicitly."""
    asset_label: str
    """
    The Neo4j node label of the single asset this Fact is about (e.g. ``KubernetesPod``,
    ``AWSEC2Instance``). Together with the value of ``asset_id_field`` it forms an indexable
    ``(label, id)`` anchor on the affected node, letting consumers locate that node in the
    graph without inferring the label from a field name. Required with no default: a Fact
    that omits it fails to construct. ``cypher_query`` must bind a variable to this label
    and project ``asset_id_field`` off that same variable, so the label and the id cannot
    describe two different nodes.
    """
    asset_id_field: str | None = None
    """
    The output-model field whose value is the ``.id`` of the ``asset_label`` node, i.e. the
    id half of the ``(label, id)`` anchor. Also drives the compliance failing-count: when set,
    the failing count is the number of distinct values of this field rather than the total
    number of finding rows. This matters when a single asset can produce multiple finding
    rows (e.g., one security group with multiple violating rules). Must be returned by the
    final ``RETURN`` of ``cypher_query`` via ``... AS <name>``, reading a property off the
    variable bound to ``asset_label`` (an alias produced only by an intermediate ``WITH``
    is query state, not an output column, and does not satisfy this).
    """

    def __post_init__(self) -> None:
        if not self.identity_fields:
            raise ValueError(
                f"Fact '{self.id}' must declare a non-empty identity_fields tuple."
            )
        if not self.asset_label:
            raise ValueError(f"Fact '{self.id}' must declare a non-empty asset_label.")
        if not self.asset_id_field:
            raise ValueError(
                f"Fact '{self.id}' must declare asset_id_field: it is the id half of "
                f"the (asset_label, id) anchor."
            )
        aliases = returned_aliases(self.cypher_query)
        if self.asset_id_field not in aliases:
            raise ValueError(
                f"Fact '{self.id}' asset_id_field '{self.asset_id_field}' is not returned "
                f"by its cypher_query (expected a '... AS {self.asset_id_field}' alias)."
            )
        missing_identity = tuple(
            name for name in self.identity_fields if name not in aliases
        )
        if missing_identity:
            raise ValueError(
                f"Fact '{self.id}' declares identity_fields {sorted(missing_identity)} "
                f"that its cypher_query does not return (expected a '... AS <name>' alias "
                f"in the final RETURN for each). An identity a consumer cannot read is "
                f"not an identity."
            )
        # The anchor is only meaningful if the label and the id describe the same
        # node, so require a variable bound to asset_label and require the
        # asset_id_field expression to read a property off that same variable.
        asset_vars = _variables_bound_to_label(self.cypher_query, self.asset_label)
        if not asset_vars:
            raise ValueError(
                f"Fact '{self.id}' declares asset_label '{self.asset_label}' but its "
                f"cypher_query never binds a variable to that label, so the rows it "
                f"returns and the asset it claims can diverge. Match it explicitly, "
                f"e.g. 'MATCH (n:{self.asset_label})'."
            )
        id_expression = _expression_for_alias(self.cypher_query, self.asset_id_field)
        owners = set(_PROPERTY_OWNER_RE.findall(id_expression or ""))
        if not owners & asset_vars:
            raise ValueError(
                f"Fact '{self.id}' returns asset_id_field '{self.asset_id_field}' as "
                f"'{id_expression}', which reads no property off {sorted(asset_vars)} "
                f"(the variable(s) bound to asset_label '{self.asset_label}'). The "
                f"(label, id) anchor must describe one node: project the id directly "
                f"off the labeled variable, e.g. "
                f"'{sorted(asset_vars)[0]}.id AS {self.asset_id_field}'."
            )
        reserved = RESERVED_FINDING_FIELDS & aliases
        if reserved:
            raise ValueError(
                f"Fact '{self.id}' aliases reserved Finding field(s) {sorted(reserved)} in "
                f"its cypher_query. 'source' is module provenance set by Rule.parse_results "
                f"and 'extra' collects undeclared columns; pick a different alias "
                f"(e.g. 'ontology_source')."
            )


class Finding(BaseModel):
    """Base class for Rule finding models."""

    # TODO: make this property mandatory one all modules have been updated to new datamodel
    source: str | None = None
    """
    The source of the Fact data, i.e. the Cartography module that ingested it. Set by
    ``Rule.parse_results`` from ``fact.module``, so it is module provenance and nothing
    else: a fact query must not return a ``source`` column (see
    ``RESERVED_FINDING_FIELDS``). A fact that needs the per-row ontology source should
    return ``_ont_source AS ontology_source`` and declare that field on its output model.
    """
    extra: dict[str, Any] = {}
    """A dictionary to hold any extra fields returned by the Fact query that are not explicitly defined in the output model."""

    # Config to coerce numbers to strings during instantiation
    model_config = ConfigDict(coerce_numbers_to_str=True)

    # Coerce o strings
    @no_type_check
    @model_validator(mode="before")
    @classmethod
    def coerce_to_string(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        for name, f in cls.model_fields.items():
            if f.annotation is not str:
                continue
            if name not in data:
                continue
            v = data[name]
            if isinstance(v, (list, tuple, set)):
                data[name] = ", ".join(v)
            if isinstance(v, dict):
                data[name] = json.dumps(v)

        return data


@dataclass(frozen=True)
class Rule:
    """A Rule represents a security issue or misconfiguration detected in the environment."""

    id: str
    """A unique identifier for the Rule. Should be globally unique within Cartography."""
    name: str
    """A brief name for the Rule."""
    tags: tuple[str, ...]
    """Tags associated with the Rule for categorization and filtering."""
    description: str
    """A brief description of the Rule. Can include details about the security issue or misconfiguration."""
    version: str
    """The version of the Rule definition."""
    facts: tuple[Fact, ...]
    """The Facts that contribute to this Rule."""
    output_model: type[Finding]
    """The output model class for the Rule."""
    references: list[RuleReference] = field(default_factory=list)
    """References or links to external resources related to the Rule."""
    frameworks: tuple[Framework, ...] = ()
    """Compliance framework requirement/control mappings for this rule."""

    @property
    def modules(self) -> set[Module]:
        """Returns the set of modules associated with this rule."""
        return {fact.module for fact in self.facts}

    def has_framework(
        self,
        short_name: str | None = None,
        scope: str | None = None,
        revision: str | None = None,
    ) -> bool:
        """
        Check if this rule has a framework matching the given criteria.

        Args:
            short_name: Filter by framework short name (case-insensitive).
            scope: Filter by framework scope (case-insensitive).
            revision: Filter by framework revision (case-insensitive).

        Returns:
            True if any framework matches all provided criteria.
        """
        return any(fw.matches(short_name, scope, revision) for fw in self.frameworks)

    def get_fact_by_id(self, fact_id: str) -> Fact | None:
        """
        Returns a fact by its ID, or None if not found.

        Args:
            fact_id (str): The ID of the Fact to find (case-insensitive).

        Returns:
            Fact | None: The matching Fact, or None if not found.
        """
        for fact in self.facts:
            if fact.id.lower() == fact_id.lower():
                return fact
        return None

    def parse_results(
        self, fact: Fact, fact_results: list[dict[str, Any]]
    ) -> list[Finding]:
        """
        Parse raw query results into typed Finding objects.

        This method converts the raw dictionary results from a Cypher query
        into strongly-typed Finding objects using the Rule's output_model.
        Fields not defined in the output model are stored in the ``extra`` dict.

        Args:
            fact (Fact): The Fact that produced these results (used for source tracking).
            fact_results (list[dict[str, Any]]): Raw results from the Cypher query.

        Returns:
            list[Finding]: A list of typed Finding objects.
        """
        result: list[Finding] = []
        for result_item in fact_results:
            parsed_output: dict[str, Any] = {"extra": {}, "source": fact.module.value}
            for key, value in result_item.items():
                if value is None:
                    continue
                if key not in self.output_model.model_fields:
                    parsed_output["extra"][key] = value
                else:
                    parsed_output[key] = value
            result.append(self.output_model(**parsed_output))
        return result
