from __future__ import annotations

import argparse
import inspect
import json
import logging
import re
from collections import Counter
from collections import defaultdict
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from datetime import date
from pathlib import Path
from pkgutil import iter_modules
from typing import Any

import cartography.models
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection

logger = logging.getLogger(__name__)

_MODEL_BASE_CLASSES = (
    CartographyNodeSchema,
    CartographyRelSchema,
    CartographyNodeProperties,
    CartographyRelProperties,
)
_NODE_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
_TABLE_SEPARATOR_RE = re.compile(r"^\|\s*-+\s*\|\s*-+")
_DOC_TOKEN_RE = re.compile(
    r"\([^()]*\)|<-\s*\[[^\]]+\]\s*-|-\s*\[[^\]]+\]\s*->|-\s*\[[^\]]+\]\s*-",
    re.DOTALL,
)
_DOC_REL_RE = re.compile(r"^(<-|-)\s*\[([^\]]+)\]\s*(->|-)$", re.DOTALL)
_DOC_NODE_LABEL_RE = re.compile(r":\s*([A-Za-z][A-Za-z0-9_]*)")
_DOC_REL_LABEL_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_DOC_PROPERTY_ALLOWLIST = frozenset(
    {
        # firstseen is set by the query builder rather than model dataclasses.
        "firstseen",
    },
)

# Legacy docs section names that are accepted aliases for specific modules.
DOC_PRIMARY_LABEL_OVERRIDES_BY_MODULE_AND_NAME = {
    ("aws", "DNSZone"): "AWSDNSZone",
    ("aws", "Package"): "AWSInspectorPackage",
}
ACCEPTED_DOC_LABELS = frozenset(
    {
        # DEPRECATED: Okta still uses legacy query-based ingestion, not model
        # dataclasses. Keep these explicit docs labels out of P1 unknown-label
        # classification until Okta is migrated to CartographyNodeSchema.
        "OktaAdministrationRole",
        "OktaApplication",
        "OktaGroup",
        "OktaOrganization",
        "OktaTrustedOrigin",
        "OktaUser",
        "OktaUserFactor",
        "ReplyUri",
    }
)


@dataclass(frozen=True)
class ModelNode:
    label: str
    module: str
    properties: tuple[str, ...]
    extra_labels: tuple[str, ...]
    model_file: str | None
    model_line: int | None


@dataclass(frozen=True)
class ModelRelationship:
    rel_label: str
    source_label: str
    target_label: str
    direction: str
    module: str
    model_file: str | None
    model_line: int | None
    owner_label: str | None
    rel_class_name: str | None

    @property
    def pattern(self) -> str:
        return format_pattern(self.source_label, self.rel_label, self.target_label)


@dataclass(frozen=True)
class DocProperty:
    name: str
    line: int


@dataclass(frozen=True)
class DocRelationship:
    module: str
    doc_file: str
    doc_line: int
    section_label: str
    source_label: str
    target_label: str
    rel_label: str
    doc_pattern: str


@dataclass(frozen=True)
class DocParseWarning:
    severity: str
    issue_type: str
    module: str
    doc_file: str
    doc_line: int
    node_label: str | None
    doc_pattern: str
    rationale: str


@dataclass(frozen=True)
class DocNode:
    module: str
    doc_file: str
    line: int
    label: str
    aliases: tuple[str, ...]
    properties: tuple[DocProperty, ...]
    relationships: tuple[DocRelationship, ...]
    warnings: tuple[DocParseWarning, ...]

    @property
    def labels(self) -> tuple[str, ...]:
        return (self.label, *self.aliases)


@dataclass(frozen=True)
class Finding:
    severity: str
    issue_type: str
    module: str | None
    doc_file: str | None
    doc_line: int | None
    model_file: str | None
    model_line: int | None
    node_label: str | None
    property_name: str | None
    rel_label: str | None
    doc_pattern: str | None
    model_pattern: str | None
    doc_source_label: str | None
    doc_target_label: str | None
    model_source_label: str | None
    model_target_label: str | None
    confidence: str
    rationale: str
    suggested_fix: str


@dataclass(frozen=True)
class AuditResult:
    findings: tuple[Finding, ...]
    model_nodes: tuple[ModelNode, ...]
    model_relationships: tuple[ModelRelationship, ...]
    doc_nodes: tuple[DocNode, ...]


def format_pattern(source_label: str, rel_label: str, target_label: str) -> str:
    return f"(:{source_label})-[:{rel_label}]->(:{target_label})"


def _relative_path(path: str | Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    path_obj = Path(path)
    try:
        return path_obj.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path_obj.as_posix()


def _source_ref_for_class(
    model_class: type[Any],
    repo_root: Path,
) -> tuple[str | None, int | None]:
    try:
        source_file = inspect.getsourcefile(model_class)
        _, line_number = inspect.getsourcelines(model_class)
    except (OSError, TypeError):
        return None, None
    return _relative_path(source_file, repo_root), line_number


def _field_line_for_class(
    properties_class: type[Any],
    field_name: str,
    repo_root: Path,
) -> tuple[str | None, int | None]:
    try:
        source_file = inspect.getsourcefile(properties_class)
        source_lines, start_line = inspect.getsourcelines(properties_class)
    except (OSError, TypeError):
        return _source_ref_for_class(properties_class, repo_root)

    field_re = re.compile(rf"^\s*{re.escape(field_name)}\s*:")
    for offset, line in enumerate(source_lines):
        if field_re.match(line):
            return _relative_path(source_file, repo_root), start_line + offset
    return _relative_path(source_file, repo_root), start_line


def _iter_model_classes(
    module: Any,
) -> Iterable[tuple[str, type[Any]]]:
    for sub_module_info in iter_modules(module.__path__):
        sub_module = __import__(
            f"{module.__name__}.{sub_module_info.name}",
            fromlist=[""],
        )
        for value in sub_module.__dict__.values():
            if not inspect.isclass(value):
                continue
            if value in _MODEL_BASE_CLASSES:
                continue
            if value.__module__ != sub_module.__name__:
                continue
            if issubclass(value, _MODEL_BASE_CLASSES):
                yield sub_module.__name__, value

        if hasattr(sub_module, "__path__"):
            yield from _iter_model_classes(sub_module)


def _module_slug(module_name: str) -> str:
    prefix = "cartography.models."
    if module_name.startswith(prefix):
        return module_name[len(prefix) :].split(".", 1)[0]
    return module_name.rsplit(".", 1)[-1]


def _extra_label_strings(extra_labels_obj: object) -> tuple[str, ...]:
    if not isinstance(extra_labels_obj, ExtraNodeLabels):
        return ()

    labels: set[str] = set()
    for label in extra_labels_obj.labels:
        labels.add(label.label if isinstance(label, ConditionalNodeLabel) else label)
    return tuple(sorted(labels))


def _node_property_names(properties_obj: object) -> tuple[str, ...]:
    if not isinstance(properties_obj, CartographyNodeProperties):
        return ()
    return tuple(field.name for field in dataclass_fields(properties_obj))


def _relationship_pattern_from_owner(
    owner_label: str,
    rel_schema: CartographyRelSchema,
) -> tuple[str, str]:
    if rel_schema.direction == LinkDirection.INWARD:
        return rel_schema.target_node_label, owner_label
    return owner_label, rel_schema.target_node_label


def _relationship_pattern_from_matchlink(
    rel_schema: type[CartographyRelSchema],
) -> tuple[str, str] | None:
    source_label = getattr(rel_schema, "source_node_label", None)
    target_label = getattr(rel_schema, "target_node_label", None)
    direction = getattr(rel_schema, "direction", None)
    if not isinstance(source_label, str):
        return None
    if not isinstance(target_label, str):
        return None
    if not isinstance(direction, LinkDirection):
        return None
    if direction == LinkDirection.INWARD:
        return target_label, source_label
    return source_label, target_label


def _iter_node_relationships(
    node_schema: type[CartographyNodeSchema],
) -> Iterable[CartographyRelSchema]:
    sub_resource_relationship = getattr(node_schema, "sub_resource_relationship", None)
    if isinstance(sub_resource_relationship, CartographyRelSchema):
        yield sub_resource_relationship

    other_relationships = getattr(node_schema, "other_relationships", None)
    rels = getattr(other_relationships, "rels", None)
    if rels:
        for rel in rels:
            if isinstance(rel, CartographyRelSchema):
                yield rel


def _ontology_constraint_lines(repo_root: Path) -> dict[tuple[str, str, str], int]:
    try:
        import cartography.models.ontology.constraints as constraints
    except ImportError:
        return {}

    try:
        source_lines, start_line = inspect.getsourcelines(constraints)
    except (OSError, TypeError):
        return {}

    result: dict[tuple[str, str, str], int] = {}
    for offset, line in enumerate(source_lines):
        src_match = re.search(r'src="([^"]+)"', line)
        dst_match = re.search(r'dst="([^"]+)"', line)
        label_match = re.search(r'label="([^"]+)"', line)
        if not src_match or not dst_match or not label_match:
            continue
        result[
            (
                src_match.group(1),
                dst_match.group(1),
                label_match.group(1),
            )
        ] = (
            start_line + offset
        )
    return result


def collect_model_metadata(repo_root: Path) -> tuple[ModelNode, ...]:
    nodes: dict[tuple[str, str], ModelNode] = {}

    for module_name, model_class in _iter_model_classes(cartography.models):
        if not issubclass(model_class, CartographyNodeSchema):
            continue
        label = getattr(model_class, "label", None)
        if not isinstance(label, str):
            continue

        module = _module_slug(module_name)
        model_file, model_line = _source_ref_for_class(model_class, repo_root)
        properties = _node_property_names(getattr(model_class, "properties", None))
        extra_labels = _extra_label_strings(
            getattr(model_class, "extra_node_labels", None)
        )
        nodes[(module, label)] = ModelNode(
            label=label,
            module=module,
            properties=properties,
            extra_labels=extra_labels,
            model_file=model_file,
            model_line=model_line,
        )

    return tuple(sorted(nodes.values(), key=lambda node: (node.module, node.label)))


def collect_model_relationships(repo_root: Path) -> tuple[ModelRelationship, ...]:
    relationships: dict[
        tuple[str, str, str, str, str | None],
        ModelRelationship,
    ] = {}

    for module_name, model_class in _iter_model_classes(cartography.models):
        module = _module_slug(module_name)
        if issubclass(model_class, CartographyNodeSchema):
            owner_label = getattr(model_class, "label", None)
            if not isinstance(owner_label, str):
                continue
            for rel_schema in _iter_node_relationships(model_class):
                source_label, target_label = _relationship_pattern_from_owner(
                    owner_label,
                    rel_schema,
                )
                model_file, model_line = _source_ref_for_class(
                    rel_schema.__class__,
                    repo_root,
                )
                relationship = ModelRelationship(
                    rel_label=rel_schema.rel_label,
                    source_label=source_label,
                    target_label=target_label,
                    direction=rel_schema.direction.name,
                    module=module,
                    model_file=model_file,
                    model_line=model_line,
                    owner_label=owner_label,
                    rel_class_name=rel_schema.__class__.__name__,
                )
                relationships[
                    (
                        module,
                        relationship.rel_label,
                        relationship.source_label,
                        relationship.target_label,
                        relationship.rel_class_name,
                    )
                ] = relationship

        if issubclass(model_class, CartographyRelSchema):
            pattern = _relationship_pattern_from_matchlink(model_class)
            if pattern is None:
                continue
            rel_label = getattr(model_class, "rel_label", None)
            direction = getattr(model_class, "direction", None)
            if not isinstance(rel_label, str):
                continue
            if not isinstance(direction, LinkDirection):
                continue
            source_label, target_label = pattern
            model_file, model_line = _source_ref_for_class(model_class, repo_root)
            relationship = ModelRelationship(
                rel_label=rel_label,
                source_label=source_label,
                target_label=target_label,
                direction=direction.name,
                module=module,
                model_file=model_file,
                model_line=model_line,
                owner_label=getattr(model_class, "source_node_label", None),
                rel_class_name=model_class.__name__,
            )
            relationships[
                (
                    module,
                    relationship.rel_label,
                    relationship.source_label,
                    relationship.target_label,
                    relationship.rel_class_name,
                )
            ] = relationship

    relationships.update(_collect_ontology_relationships(repo_root))
    return tuple(
        sorted(
            relationships.values(),
            key=lambda rel: (
                rel.module,
                rel.rel_label,
                rel.source_label,
                rel.target_label,
                rel.rel_class_name or "",
            ),
        )
    )


def _collect_ontology_relationships(
    repo_root: Path,
) -> dict[tuple[str, str, str, str, str | None], ModelRelationship]:
    try:
        from cartography.models.ontology.constraints import ONTOLOGY_REL_CONSTRAINTS
    except ImportError:
        return {}

    source_file = None
    try:
        import cartography.models.ontology.constraints as constraints

        source_file = _relative_path(inspect.getsourcefile(constraints), repo_root)
    except (OSError, TypeError):
        source_file = None

    line_by_constraint = _ontology_constraint_lines(repo_root)
    relationships: dict[
        tuple[str, str, str, str, str | None],
        ModelRelationship,
    ] = {}
    for constraint in ONTOLOGY_REL_CONSTRAINTS:
        relationship = ModelRelationship(
            rel_label=constraint.label,
            source_label=constraint.src,
            target_label=constraint.dst,
            direction="OUTWARD",
            module="ontology",
            model_file=source_file,
            model_line=line_by_constraint.get(
                (constraint.src, constraint.dst, constraint.label),
            ),
            owner_label=constraint.src,
            rel_class_name="RelConstraint",
        )
        relationships[
            (
                relationship.module,
                relationship.rel_label,
                relationship.source_label,
                relationship.target_label,
                relationship.rel_class_name,
            )
        ] = relationship
    return relationships


def _parse_node_label(title: str, module: str) -> tuple[str, tuple[str, ...]]:
    normalized = title.replace("::", ":")
    parts = [part.strip() for part in normalized.split(":")]
    main_name = parts[0] if parts else title.strip()
    main_name = DOC_PRIMARY_LABEL_OVERRIDES_BY_MODULE_AND_NAME.get(
        (module, main_name),
        main_name,
    )
    aliases = tuple(alias for alias in parts[1:] if _is_valid_label(alias))
    return main_name, aliases


def _is_valid_label(label: str) -> bool:
    return bool(label) and label.isidentifier() and label[0].isalpha()


def _clean_doc_property_name(raw_name: str) -> str:
    return raw_name.replace("**", "").replace("`", "").replace("\\", "").strip()


def _parse_property_table(
    lines: Sequence[str], first_line: int
) -> tuple[DocProperty, ...]:
    properties: list[DocProperty] = []
    in_table = False

    for offset, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#### Relationships"):
            break
        if stripped.startswith("|"):
            in_table = True
        elif in_table:
            break

        if not in_table or not stripped.startswith("|"):
            continue
        if "Field" in stripped and "Description" in stripped:
            continue
        if _TABLE_SEPARATOR_RE.match(stripped):
            continue

        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) < 2:
            continue
        field_name = _clean_doc_property_name(parts[0])
        if field_name:
            properties.append(DocProperty(field_name, first_line + offset))

    return tuple(properties)


def _relationship_section_text(
    lines: Sequence[str],
    first_line: int,
) -> tuple[str, int] | None:
    for offset, line in enumerate(lines):
        if line.strip().startswith("#### Relationships"):
            body_lines = lines[offset + 1 :]
            return "\n".join(body_lines), first_line + offset + 1
    return None


@dataclass(frozen=True)
class _DocToken:
    kind: str
    text: str
    start: int
    end: int


def _line_for_offset(text: str, first_line: int, offset: int) -> int:
    return first_line + text.count("\n", 0, offset)


def _parse_doc_node_labels(node_token: str) -> tuple[str, ...]:
    content = node_token.strip()[1:-1].strip()
    if not content:
        return ()

    labels: list[str] = []
    for part in content.split(","):
        part = part.strip()
        if not part or part == "...":
            continue
        part = part.split("{", 1)[0].strip()
        colon_labels = _DOC_NODE_LABEL_RE.findall(part)
        if colon_labels:
            labels.extend(label for label in colon_labels if _is_valid_label(label))
            continue
        if _is_valid_label(part) and part[0].isupper():
            labels.append(part)

    return tuple(dict.fromkeys(labels))


def _parse_doc_rel_token(rel_token: str) -> tuple[str | None, tuple[str, ...]]:
    match = _DOC_REL_RE.match(rel_token.strip())
    if match is None:
        return None, ()

    left_arrow, body, right_arrow = match.groups()
    if left_arrow == "-" and right_arrow == "->":
        direction = "OUTWARD"
    elif left_arrow == "<-" and right_arrow == "-":
        direction = "INWARD"
    else:
        direction = None

    body = body.strip()
    if ":" in body:
        body = body.split(":", 1)[1]
    body = body.split("{", 1)[0].strip()
    body = re.sub(r"\s+", "", body)
    labels: list[str] = []
    for candidate in body.split("|"):
        candidate = candidate.split("*", 1)[0]
        if _DOC_REL_LABEL_RE.match(candidate):
            labels.append(candidate)
    return direction, tuple(dict.fromkeys(labels))


def _parse_doc_relationships(
    text: str,
    first_line: int,
    module: str,
    doc_file: str,
    section_label: str,
) -> tuple[tuple[DocRelationship, ...], tuple[DocParseWarning, ...]]:
    tokens = [
        _DocToken(
            kind="node" if match.group(0).startswith("(") else "rel",
            text=match.group(0),
            start=match.start(),
            end=match.end(),
        )
        for match in _DOC_TOKEN_RE.finditer(text)
    ]
    relationships: list[DocRelationship] = []
    warnings: list[DocParseWarning] = []
    seen_segments: set[tuple[int, int, int]] = set()

    for idx in range(len(tokens) - 2):
        left_token = tokens[idx]
        rel_token = tokens[idx + 1]
        right_token = tokens[idx + 2]
        if (
            left_token.kind != "node"
            or rel_token.kind != "rel"
            or right_token.kind != "node"
        ):
            continue
        segment_key = (left_token.start, rel_token.start, right_token.start)
        if segment_key in seen_segments:
            continue
        seen_segments.add(segment_key)

        line = _line_for_offset(text, first_line, left_token.start)
        doc_pattern = text[left_token.start : right_token.end].strip()
        direction, rel_labels = _parse_doc_rel_token(rel_token.text)
        left_labels = _parse_doc_node_labels(left_token.text)
        right_labels = _parse_doc_node_labels(right_token.text)

        if direction is None:
            warnings.append(
                DocParseWarning(
                    severity="P3",
                    issue_type="ambiguous_relationship_pattern",
                    module=module,
                    doc_file=doc_file,
                    doc_line=line,
                    node_label=section_label,
                    doc_pattern=doc_pattern,
                    rationale="Relationship pattern is explicit but not direction-bearing.",
                )
            )
            continue
        if len(rel_labels) != 1:
            warnings.append(
                DocParseWarning(
                    severity="P3",
                    issue_type="ambiguous_relationship_pattern",
                    module=module,
                    doc_file=doc_file,
                    doc_line=line,
                    node_label=section_label,
                    doc_pattern=doc_pattern,
                    rationale="Relationship pattern contains zero or multiple relationship labels.",
                )
            )
            continue
        if not left_labels or not right_labels:
            warnings.append(
                DocParseWarning(
                    severity="P3",
                    issue_type="unlabeled_relationship_pattern",
                    module=module,
                    doc_file=doc_file,
                    doc_line=line,
                    node_label=section_label,
                    doc_pattern=doc_pattern,
                    rationale="Relationship pattern has an unlabeled endpoint.",
                )
            )
            continue

        rel_label = rel_labels[0]
        if direction == "OUTWARD":
            sources = left_labels
            targets = right_labels
        else:
            sources = right_labels
            targets = left_labels

        for source_label in sources:
            for target_label in targets:
                relationships.append(
                    DocRelationship(
                        module=module,
                        doc_file=doc_file,
                        doc_line=line,
                        section_label=section_label,
                        source_label=source_label,
                        target_label=target_label,
                        rel_label=rel_label,
                        doc_pattern=format_pattern(
                            source_label,
                            rel_label,
                            target_label,
                        ),
                    )
                )

    return tuple(relationships), tuple(warnings)


def parse_schema_doc_content(
    content: str,
    module: str,
    doc_file: str,
) -> tuple[DocNode, ...]:
    matches = list(_NODE_HEADING_RE.finditer(content))
    doc_nodes: list[DocNode] = []

    for index, match in enumerate(matches):
        title = match.group(1).strip()
        next_start = (
            matches[index + 1].start() if index + 1 < len(matches) else len(content)
        )
        section = content[match.end() : next_start]
        heading_line = content.count("\n", 0, match.start()) + 1
        lines = section.splitlines()
        first_section_line = heading_line + 1
        label, aliases = _parse_node_label(title, module)
        if not _is_valid_label(label):
            continue
        properties = _parse_property_table(lines, first_section_line)
        relationships: tuple[DocRelationship, ...] = ()
        warnings: tuple[DocParseWarning, ...] = ()
        rel_section = _relationship_section_text(lines, first_section_line)
        if rel_section is not None:
            rel_text, rel_first_line = rel_section
            relationships, warnings = _parse_doc_relationships(
                rel_text,
                rel_first_line,
                module,
                doc_file,
                label,
            )

        doc_nodes.append(
            DocNode(
                module=module,
                doc_file=doc_file,
                line=heading_line,
                label=label,
                aliases=aliases,
                properties=properties,
                relationships=relationships,
                warnings=warnings,
            )
        )

    return tuple(doc_nodes)


def _module_from_schema_doc_path(schema_path: Path) -> str:
    parts = schema_path.parts
    if "modules" in parts:
        modules_index = parts.index("modules")
        if modules_index + 1 < len(parts):
            return parts[modules_index + 1]
    return schema_path.parent.name


def collect_doc_metadata(repo_root: Path) -> tuple[DocNode, ...]:
    docs_root = repo_root / "docs"
    doc_nodes: list[DocNode] = []
    for schema_path in sorted(docs_root.rglob("schema.md")):
        module = _module_from_schema_doc_path(schema_path)
        doc_file = _relative_path(schema_path, repo_root)
        if doc_file is None:
            continue
        doc_nodes.extend(
            parse_schema_doc_content(
                schema_path.read_text(),
                module,
                doc_file,
            )
        )
    return tuple(doc_nodes)


def _label_to_primaries(model_nodes: Sequence[ModelNode]) -> dict[str, set[str]]:
    labels: dict[str, set[str]] = defaultdict(set)
    for node in model_nodes:
        labels[node.label].add(node.label)
        for extra_label in node.extra_labels:
            labels[extra_label].add(node.label)
    return labels


def _known_label_candidates(
    label: str,
    module: str | None,
    label_to_primary: dict[str, set[str]],
) -> set[str]:
    candidates = {label}
    candidates.update(label_to_primary.get(label, set()))
    if module is not None:
        override = DOC_PRIMARY_LABEL_OVERRIDES_BY_MODULE_AND_NAME.get((module, label))
        if override:
            candidates.add(override)
            candidates.update(label_to_primary.get(override, set()))
    return candidates


def _labels_equivalent(
    doc_label: str,
    model_label: str,
    module: str | None,
    label_to_primary: dict[str, set[str]],
) -> bool:
    doc_candidates = _known_label_candidates(doc_label, module, label_to_primary)
    model_candidates = _known_label_candidates(model_label, module, label_to_primary)
    return bool(doc_candidates & model_candidates)


def _label_is_known(
    label: str,
    module: str | None,
    label_to_primary: dict[str, set[str]],
) -> bool:
    if label in ACCEPTED_DOC_LABELS:
        return True
    candidates = _known_label_candidates(label, module, label_to_primary)
    known_labels = set(label_to_primary)
    return bool(candidates & known_labels)


def _doc_node_model_matches(
    doc_node: DocNode,
    model_nodes: Sequence[ModelNode],
    label_to_primary: dict[str, set[str]],
) -> tuple[ModelNode, ...]:
    matches: list[ModelNode] = []
    for model_node in model_nodes:
        if model_node.module != doc_node.module:
            continue
        if any(
            _labels_equivalent(
                label, model_node.label, doc_node.module, label_to_primary
            )
            for label in doc_node.labels
        ):
            matches.append(model_node)
    return tuple(matches)


def _model_relationship_is_documented(
    model_rel: ModelRelationship,
    doc_relationships: Sequence[DocRelationship],
    label_to_primary: dict[str, set[str]],
) -> bool:
    for doc_rel in doc_relationships:
        if doc_rel.module != model_rel.module:
            continue
        if doc_rel.rel_label != model_rel.rel_label:
            continue
        if not _labels_equivalent(
            doc_rel.source_label,
            model_rel.source_label,
            model_rel.module,
            label_to_primary,
        ):
            continue
        if not _labels_equivalent(
            doc_rel.target_label,
            model_rel.target_label,
            model_rel.module,
            label_to_primary,
        ):
            continue
        return True
    return False


def _find_same_orientation_model_rel(
    doc_rel: DocRelationship,
    model_relationships: Sequence[ModelRelationship],
    label_to_primary: dict[str, set[str]],
) -> ModelRelationship | None:
    for model_rel in model_relationships:
        if model_rel.module != doc_rel.module:
            continue
        if model_rel.rel_label != doc_rel.rel_label:
            continue
        if not _labels_equivalent(
            doc_rel.source_label,
            model_rel.source_label,
            doc_rel.module,
            label_to_primary,
        ):
            continue
        if not _labels_equivalent(
            doc_rel.target_label,
            model_rel.target_label,
            doc_rel.module,
            label_to_primary,
        ):
            continue
        return model_rel
    return None


def _find_reversed_model_rel(
    doc_rel: DocRelationship,
    model_relationships: Sequence[ModelRelationship],
    label_to_primary: dict[str, set[str]],
) -> ModelRelationship | None:
    for model_rel in model_relationships:
        if model_rel.module != doc_rel.module:
            continue
        if model_rel.rel_label != doc_rel.rel_label:
            continue
        if not _labels_equivalent(
            doc_rel.source_label,
            model_rel.target_label,
            doc_rel.module,
            label_to_primary,
        ):
            continue
        if not _labels_equivalent(
            doc_rel.target_label,
            model_rel.source_label,
            doc_rel.module,
            label_to_primary,
        ):
            continue
        return model_rel
    return None


def _best_model_rel_candidate(
    doc_rel: DocRelationship,
    model_relationships: Sequence[ModelRelationship],
) -> ModelRelationship | None:
    same_label = [
        model_rel
        for model_rel in model_relationships
        if model_rel.module == doc_rel.module
        and model_rel.rel_label == doc_rel.rel_label
    ]
    return same_label[0] if same_label else None


def compare_schema_docs_to_models(
    model_nodes: Sequence[ModelNode],
    model_relationships: Sequence[ModelRelationship],
    doc_nodes: Sequence[DocNode],
) -> tuple[Finding, ...]:
    label_to_primary = _label_to_primaries(model_nodes)
    model_nodes_by_module = defaultdict(list)
    for node in model_nodes:
        model_nodes_by_module[node.module].append(node)

    doc_relationships = tuple(
        relationship
        for doc_node in doc_nodes
        for relationship in doc_node.relationships
    )
    findings: list[Finding] = []

    for doc_node in doc_nodes:
        for warning in doc_node.warnings:
            findings.append(
                Finding(
                    severity=warning.severity,
                    issue_type=warning.issue_type,
                    module=warning.module,
                    doc_file=warning.doc_file,
                    doc_line=warning.doc_line,
                    model_file=None,
                    model_line=None,
                    node_label=warning.node_label,
                    property_name=None,
                    rel_label=None,
                    doc_pattern=warning.doc_pattern,
                    model_pattern=None,
                    doc_source_label=None,
                    doc_target_label=None,
                    model_source_label=None,
                    model_target_label=None,
                    confidence="medium",
                    rationale=warning.rationale,
                    suggested_fix="Review this explicit pattern manually; the parser cannot classify it safely.",
                )
            )

    for doc_rel in doc_relationships:
        same_orientation = _find_same_orientation_model_rel(
            doc_rel,
            model_relationships,
            label_to_primary,
        )
        if same_orientation is not None:
            continue

        missing_labels = tuple(
            label
            for label in (doc_rel.source_label, doc_rel.target_label)
            if not _label_is_known(label, doc_rel.module, label_to_primary)
        )
        if missing_labels:
            for missing_label in missing_labels:
                findings.append(
                    Finding(
                        severity="P1",
                        issue_type="unknown_node_label_in_explicit_pattern",
                        module=doc_rel.module,
                        doc_file=doc_rel.doc_file,
                        doc_line=doc_rel.doc_line,
                        model_file=None,
                        model_line=None,
                        node_label=missing_label,
                        property_name=None,
                        rel_label=doc_rel.rel_label,
                        doc_pattern=doc_rel.doc_pattern,
                        model_pattern=None,
                        doc_source_label=doc_rel.source_label,
                        doc_target_label=doc_rel.target_label,
                        model_source_label=None,
                        model_target_label=None,
                        confidence="high",
                        rationale=(
                            f"Explicit docs pattern uses node label {missing_label!r}, "
                            "which is not a model primary label, extra label, or accepted docs override."
                        ),
                        suggested_fix=(
                            f"Replace {missing_label!r} with the modeled label or add an explicit accepted override "
                            "if this is an intentional legacy docs alias."
                        ),
                    )
                )
            continue

        reversed_rel = _find_reversed_model_rel(
            doc_rel,
            model_relationships,
            label_to_primary,
        )
        if reversed_rel is not None:
            findings.append(
                Finding(
                    severity="P1",
                    issue_type="relationship_direction_contradiction",
                    module=doc_rel.module,
                    doc_file=doc_rel.doc_file,
                    doc_line=doc_rel.doc_line,
                    model_file=reversed_rel.model_file,
                    model_line=reversed_rel.model_line,
                    node_label=doc_rel.section_label,
                    property_name=None,
                    rel_label=doc_rel.rel_label,
                    doc_pattern=doc_rel.doc_pattern,
                    model_pattern=reversed_rel.pattern,
                    doc_source_label=doc_rel.source_label,
                    doc_target_label=doc_rel.target_label,
                    model_source_label=reversed_rel.source_label,
                    model_target_label=reversed_rel.target_label,
                    confidence="high",
                    rationale=(
                        "Docs show an explicit relationship arrow whose endpoints are reversed "
                        "relative to the authoritative CartographyRelSchema direction."
                    ),
                    suggested_fix=(
                        f"Update the docs pattern to `{reversed_rel.pattern}`. Do not add a mirrored graph edge."
                    ),
                )
            )
            continue

        candidate = _best_model_rel_candidate(doc_rel, model_relationships)
        findings.append(
            Finding(
                severity="P2",
                issue_type="docs_only_relationship",
                module=doc_rel.module,
                doc_file=doc_rel.doc_file,
                doc_line=doc_rel.doc_line,
                model_file=candidate.model_file if candidate is not None else None,
                model_line=candidate.model_line if candidate is not None else None,
                node_label=doc_rel.section_label,
                property_name=None,
                rel_label=doc_rel.rel_label,
                doc_pattern=doc_rel.doc_pattern,
                model_pattern=candidate.pattern if candidate is not None else None,
                doc_source_label=doc_rel.source_label,
                doc_target_label=doc_rel.target_label,
                model_source_label=(
                    candidate.source_label if candidate is not None else None
                ),
                model_target_label=(
                    candidate.target_label if candidate is not None else None
                ),
                confidence="medium",
                rationale=(
                    "Docs contain an explicit relationship pattern that did not match a model relationship. "
                    "This may be older docs drift or docs-only explanatory content."
                ),
                suggested_fix=(
                    "Verify whether this relationship is still modeled. If not, remove or qualify the docs example."
                ),
            )
        )

    doc_modules = {doc_node.module for doc_node in doc_nodes}
    for model_rel in model_relationships:
        if model_rel.module not in doc_modules:
            continue
        if _model_relationship_is_documented(
            model_rel,
            doc_relationships,
            label_to_primary,
        ):
            continue
        findings.append(
            Finding(
                severity="P2",
                issue_type="missing_docs_relationship",
                module=model_rel.module,
                doc_file=None,
                doc_line=None,
                model_file=model_rel.model_file,
                model_line=model_rel.model_line,
                node_label=model_rel.owner_label,
                property_name=None,
                rel_label=model_rel.rel_label,
                doc_pattern=None,
                model_pattern=model_rel.pattern,
                doc_source_label=None,
                doc_target_label=None,
                model_source_label=model_rel.source_label,
                model_target_label=model_rel.target_label,
                confidence="high",
                rationale="Model relationship exists but no matching explicit docs relationship pattern was found.",
                suggested_fix=f"Add `{model_rel.pattern}` to the relevant schema.md relationship section.",
            )
        )

    for doc_node in doc_nodes:
        matching_nodes = _doc_node_model_matches(
            doc_node,
            model_nodes_by_module.get(doc_node.module, ()),
            label_to_primary,
        )
        if not matching_nodes:
            findings.append(
                Finding(
                    severity="P2",
                    issue_type="doc_only_node_section",
                    module=doc_node.module,
                    doc_file=doc_node.doc_file,
                    doc_line=doc_node.line,
                    model_file=None,
                    model_line=None,
                    node_label=doc_node.label,
                    property_name=None,
                    rel_label=None,
                    doc_pattern=None,
                    model_pattern=None,
                    doc_source_label=None,
                    doc_target_label=None,
                    model_source_label=None,
                    model_target_label=None,
                    confidence="medium",
                    rationale=(
                        "Docs have a node section that does not resolve to a model primary label, "
                        "extra label, or accepted module override."
                    ),
                    suggested_fix="Map the legacy section title to a modeled label or remove the stale section.",
                )
            )
            continue

        model_property_names = {
            property_name
            for model_node in matching_nodes
            for property_name in model_node.properties
        }
        for doc_property in doc_node.properties:
            if doc_property.name in model_property_names:
                continue
            if doc_property.name in _DOC_PROPERTY_ALLOWLIST:
                continue
            findings.append(
                Finding(
                    severity="P2",
                    issue_type="docs_only_property",
                    module=doc_node.module,
                    doc_file=doc_node.doc_file,
                    doc_line=doc_property.line,
                    model_file=matching_nodes[0].model_file,
                    model_line=matching_nodes[0].model_line,
                    node_label=doc_node.label,
                    property_name=doc_property.name,
                    rel_label=None,
                    doc_pattern=None,
                    model_pattern=None,
                    doc_source_label=None,
                    doc_target_label=None,
                    model_source_label=None,
                    model_target_label=None,
                    confidence="medium",
                    rationale=(
                        "Docs list a property that is not defined on the matched model node schema. "
                        "This may be stale docs or a legacy docs-only field."
                    ),
                    suggested_fix="Verify the property owner and remove or move the docs row if stale.",
                )
            )

        doc_property_names = {doc_property.name for doc_property in doc_node.properties}
        for model_node in matching_nodes:
            for property_name in model_node.properties:
                if property_name in doc_property_names:
                    continue
                model_file, model_line = model_node.model_file, model_node.model_line
                findings.append(
                    Finding(
                        severity="P2",
                        issue_type="missing_docs_property",
                        module=model_node.module,
                        doc_file=doc_node.doc_file,
                        doc_line=doc_node.line,
                        model_file=model_file,
                        model_line=model_line,
                        node_label=model_node.label,
                        property_name=property_name,
                        rel_label=None,
                        doc_pattern=None,
                        model_pattern=None,
                        doc_source_label=None,
                        doc_target_label=None,
                        model_source_label=None,
                        model_target_label=None,
                        confidence="high",
                        rationale="Model property exists but the matched docs node section omits it.",
                        suggested_fix=f"Add a docs row for `{model_node.label}.{property_name}` if the property is user-facing.",
                    )
                )

    for model_node in model_nodes:
        if model_node.module not in doc_modules:
            continue
        has_doc_node = any(
            _doc_node_model_matches(
                doc_node,
                (model_node,),
                label_to_primary,
            )
            for doc_node in doc_nodes
            if doc_node.module == model_node.module
        )
        if has_doc_node:
            continue
        findings.append(
            Finding(
                severity="P2",
                issue_type="missing_docs_node_section",
                module=model_node.module,
                doc_file=None,
                doc_line=None,
                model_file=model_node.model_file,
                model_line=model_node.model_line,
                node_label=model_node.label,
                property_name=None,
                rel_label=None,
                doc_pattern=None,
                model_pattern=None,
                doc_source_label=None,
                doc_target_label=None,
                model_source_label=None,
                model_target_label=None,
                confidence="high",
                rationale="Model node schema exists but no matching schema.md node section was found.",
                suggested_fix=f"Add a `{model_node.label}` section to the module schema docs.",
            )
        )

    return tuple(_dedupe_findings(findings))


def _dedupe_findings(findings: Iterable[Finding]) -> list[Finding]:
    deduped: dict[tuple[Any, ...], Finding] = {}
    for finding in findings:
        key = (
            finding.severity,
            finding.issue_type,
            finding.module,
            finding.doc_file,
            finding.doc_line,
            finding.model_file,
            finding.model_line,
            finding.node_label,
            finding.property_name,
            finding.rel_label,
            finding.doc_pattern,
            finding.model_pattern,
            finding.doc_source_label,
            finding.doc_target_label,
            finding.model_source_label,
            finding.model_target_label,
        )
        deduped.setdefault(key, finding)
    return sorted(
        deduped.values(),
        key=lambda finding: (
            finding.severity,
            finding.module or "",
            finding.issue_type,
            finding.doc_file or "",
            finding.doc_line or 0,
            finding.model_file or "",
            finding.model_line or 0,
            finding.node_label or "",
            finding.property_name or "",
            finding.rel_label or "",
            finding.doc_pattern or "",
            finding.model_pattern or "",
        ),
    )


def run_schema_docs_audit(repo_root: Path) -> AuditResult:
    model_nodes = collect_model_metadata(repo_root)
    model_relationships = collect_model_relationships(repo_root)
    doc_nodes = collect_doc_metadata(repo_root)
    findings = compare_schema_docs_to_models(
        model_nodes,
        model_relationships,
        doc_nodes,
    )
    return AuditResult(
        findings=findings,
        model_nodes=model_nodes,
        model_relationships=model_relationships,
        doc_nodes=doc_nodes,
    )


def write_json_report(findings: Sequence[Finding], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([asdict(finding) for finding in findings], indent=2, sort_keys=True)
        + "\n",
    )


def _md_escape(value: object | None) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _ref(file_path: str | None, line: int | None) -> str:
    if file_path is None:
        return ""
    if line is None:
        return file_path
    return f"{file_path}:{line}"


def _count_by(
    findings: Sequence[Finding],
    *fields: str,
) -> list[tuple[tuple[str, ...], int]]:
    counter: Counter[tuple[str, ...]] = Counter()
    for finding in findings:
        counter[
            tuple(str(getattr(finding, field) or "unknown") for field in fields)
        ] += 1
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))


def render_markdown_report(result: AuditResult) -> str:
    findings = result.findings
    lines: list[str] = [
        f"# Cartography schema documentation audit, {date.today().isoformat()}",
        "",
        "Cartography model code is treated as the source of truth. Explicit docs arrow patterns are authoritative for docs-side source, relationship, and target labels.",
        "",
        "## Summary",
        "",
        f"- Model nodes inspected: {len(result.model_nodes)}",
        f"- Model relationships inspected: {len(result.model_relationships)}",
        f"- Docs node sections inspected: {len(result.doc_nodes)}",
        f"- Findings emitted: {len(findings)}",
        "",
        "| Severity | Count |",
        "|---|---:|",
    ]
    for (severity,), count in _count_by(findings, "severity"):
        lines.append(f"| {severity} | {count} |")

    lines.extend(
        [
            "",
            "## Findings By Module",
            "",
            "| Module | Severity | Count |",
            "|---|---|---:|",
        ]
    )
    for (module, severity), count in _count_by(findings, "module", "severity"):
        lines.append(f"| {module} | {severity} | {count} |")

    p1_findings = [finding for finding in findings if finding.severity == "P1"]
    lines.extend(
        [
            "",
            "## P1 Contradictions",
            "",
        ]
    )
    if not p1_findings:
        lines.append("No P1 contradictions were detected.")
    else:
        lines.extend(
            [
                "| Type | Module | Docs | Model | Docs Pattern | Model Pattern | Suggested Fix |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for finding in p1_findings:
            lines.append(
                "| "
                + " | ".join(
                    (
                        _md_escape(finding.issue_type),
                        _md_escape(finding.module),
                        _md_escape(_ref(finding.doc_file, finding.doc_line)),
                        _md_escape(_ref(finding.model_file, finding.model_line)),
                        _md_escape(finding.doc_pattern),
                        _md_escape(finding.model_pattern),
                        _md_escape(finding.suggested_fix),
                    )
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## P2 And P3 Inventory",
            "",
            "The JSON report contains every finding with the full required field set. This markdown report keeps non-P1 output summarized to avoid hiding hard contradictions in coverage noise.",
            "",
            "| Severity | Issue Type | Count |",
            "|---|---|---:|",
        ]
    )
    for (severity, issue_type), count in _count_by(findings, "severity", "issue_type"):
        if severity == "P1":
            continue
        lines.append(f"| {severity} | {issue_type} | {count} |")

    if p1_findings:
        recommended_next = (
            "Recommended next: fix the P1 docs contradictions first, then decide "
            "which P2 coverage gaps are useful enough to document."
        )
    else:
        recommended_next = (
            "Recommended next: decide which P2 coverage gaps are useful enough to "
            "document; no P1 docs contradictions remain."
        )

    lines.extend(["", recommended_next, ""])
    return "\n".join(lines)


def write_markdown_report(result: AuditResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(result))


def write_reports(result: AuditResult, reports_dir: Path) -> tuple[Path, Path]:
    json_path = reports_dir / "schema_doc_contradictions.json"
    markdown_path = reports_dir / "schema_doc_contradictions.md"
    write_json_report(result.findings, json_path)
    write_markdown_report(result, markdown_path)
    return markdown_path, json_path


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit docs/**/schema.md against Cartography model definitions.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the Cartography repository root.",
    )
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory where schema_doc_contradictions reports should be written.",
    )
    parser.add_argument(
        "--fail-on-p1",
        action="store_true",
        help="Exit with status 1 when P1 contradictions are found.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    result = run_schema_docs_audit(repo_root)
    markdown_path, json_path = write_reports(result, repo_root / args.reports_dir)
    severity_counts = Counter(finding.severity for finding in result.findings)
    print(f"Wrote {markdown_path}")
    print(f"Wrote {json_path}")
    print(
        "Findings: "
        + ", ".join(
            f"{severity}={count}" for severity, count in sorted(severity_counts.items())
        )
    )
    if args.fail_on_p1 and severity_counts.get("P1", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
