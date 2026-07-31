from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from typing import Iterable
from typing import Mapping
from typing import Sequence
from typing import TypeVar

import neo4j

from cartography.client.core.tx import read_list_of_values_tx
from cartography.client.core.tx import run_write_query
from cartography.helpers import batch

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_T = TypeVar("_T", bound=Mapping[str, Any])


@dataclass(frozen=True)
class ContainerImageLayerGraphShape:
    """Describe the graph closure owned by a provider's layer enrichment."""

    image_label: str
    layer_label: str
    scope_label: str
    scope_properties: tuple[str, ...]
    image_scoped: bool = True
    layer_scoped: bool = True
    image_layer_rel_types: tuple[str, ...] = ("HAS_LAYER", "HEAD", "TAIL")
    stable_image_rel_types: tuple[str, ...] = ("BUILT_FROM",)
    stable_image_rels_are_matchlinks: bool = False
    has_next: bool = False
    image_digest_property: str = "digest"
    image_layer_ids_property: str = "layer_diff_ids"
    layer_id_property: str = "diff_id"

    def __post_init__(self) -> None:
        identifiers = (
            self.image_label,
            self.layer_label,
            self.scope_label,
            self.image_digest_property,
            self.image_layer_ids_property,
            self.layer_id_property,
            *self.scope_properties,
            *self.image_layer_rel_types,
            *self.stable_image_rel_types,
        )
        invalid = [value for value in identifiers if not _IDENTIFIER.fullmatch(value)]
        if invalid:
            raise ValueError(f"Invalid Cypher identifier(s): {', '.join(invalid)}")


def _scope_parameters(
    shape: ContainerImageLayerGraphShape,
    scope_values: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    missing = set(shape.scope_properties) - scope_values.keys()
    extra = scope_values.keys() - set(shape.scope_properties)
    if missing or extra:
        raise ValueError(
            "Scope values do not match graph shape: "
            f"missing={sorted(missing)}, extra={sorted(extra)}",
        )

    parameters: dict[str, Any] = {}
    entries = []
    for property_name in shape.scope_properties:
        parameter_name = f"scope_{property_name}"
        entries.append(f"{property_name}: ${parameter_name}")
        parameters[parameter_name] = scope_values[property_name]
    return ", ".join(entries), parameters


def get_complete_layer_digests(
    neo4j_session: neo4j.Session,
    shape: ContainerImageLayerGraphShape,
    digests: Iterable[str] | None,
    scope_values: Mapping[str, Any],
) -> set[str]:
    """Return digests whose layer closure is complete for the current scope."""

    unique_digests = sorted(set(digests)) if digests is not None else None
    if unique_digests == []:
        return set()

    scope_match, parameters = _scope_parameters(shape, scope_values)
    image_scope_predicate = ""
    if shape.image_scoped:
        image_scope_predicate = f"""
        AND EXISTS {{
            MATCH (scope:{shape.scope_label} {{{scope_match}}})-[:RESOURCE]->(img)
        }}
        """

    layer_scope_predicate = ""
    if shape.layer_scoped:
        layer_scope_predicate = f"""
        AND (
            size(img.{shape.image_layer_ids_property}) = 0
            OR all(layer_id IN img.{shape.image_layer_ids_property} WHERE EXISTS {{
                MATCH (scope:{shape.scope_label} {{{scope_match}}})-[:RESOURCE]->
                      (layer:{shape.layer_label} {{{shape.layer_id_property}: layer_id}})
            }})
        )
        """

    relationship_predicates: list[str] = []
    layer_ids = f"img.{shape.image_layer_ids_property}"
    layer_match = (
        f"(layer:{shape.layer_label} " f"{{{shape.layer_id_property}: layer_id}})"
    )
    if "HAS_LAYER" in shape.image_layer_rel_types:
        relationship_predicates.append(
            f"""
            AND (
                size({layer_ids}) = 0
                OR all(layer_id IN {layer_ids} WHERE EXISTS {{
                    MATCH (img)-[:HAS_LAYER]->{layer_match}
                }})
            )
            """,
        )
    if "HEAD" in shape.image_layer_rel_types:
        relationship_predicates.append(
            f"""
            AND (
                size({layer_ids}) = 0
                OR EXISTS {{
                    MATCH (img)-[:HEAD]->
                          (:{shape.layer_label} {{
                              {shape.layer_id_property}: {layer_ids}[0]
                          }})
                }}
            )
            """,
        )
    if "TAIL" in shape.image_layer_rel_types:
        relationship_predicates.append(
            f"""
            AND (
                size({layer_ids}) = 0
                OR EXISTS {{
                    MATCH (img)-[:TAIL]->
                          (:{shape.layer_label} {{
                              {shape.layer_id_property}: {layer_ids}[
                                  size({layer_ids}) - 1
                              ]
                          }})
                }}
            )
            """,
        )
    if shape.has_next:
        relationship_predicates.append(
            f"""
            AND all(layer_index IN CASE
                WHEN size({layer_ids}) > 1
                    THEN range(0, size({layer_ids}) - 2)
                ELSE []
            END WHERE EXISTS {{
                MATCH (:{shape.layer_label} {{
                    {shape.layer_id_property}: {layer_ids}[layer_index]
                }})-[:NEXT]->(:{shape.layer_label} {{
                    {shape.layer_id_property}: {layer_ids}[layer_index + 1]
                }})
            }})
            """,
        )
    relationship_predicate = "\n".join(relationship_predicates)

    digest_predicate = (
        f"img.{shape.image_digest_property} IN $digests"
        if unique_digests is not None
        else "true"
    )
    query = f"""
    MATCH (img:{shape.image_label})
    WHERE {digest_predicate}
      AND img.{shape.image_layer_ids_property} IS NOT NULL
      {image_scope_predicate}
      {layer_scope_predicate}
      {relationship_predicate}
    RETURN img.{shape.image_digest_property}
    """
    values = neo4j_session.execute_read(
        read_list_of_values_tx,
        query,
        **({"digests": unique_digests} if unique_digests is not None else {}),
        **parameters,
    )
    return {str(value) for value in values if value}


def partition_layer_fetches(
    candidates: Sequence[_T],
    complete_digests: set[str],
    *,
    digest_key: str = "digest",
) -> tuple[list[_T], list[_T]]:
    """Partition mapping-shaped candidates into fetch and refresh lists."""

    to_fetch: list[_T] = []
    to_refresh: list[_T] = []
    for candidate in candidates:
        digest = candidate.get(digest_key)
        if digest and str(digest) in complete_digests:
            to_refresh.append(candidate)
        else:
            to_fetch.append(candidate)
    return to_fetch, to_refresh


def refresh_layer_closures(
    neo4j_session: neo4j.Session,
    shape: ContainerImageLayerGraphShape,
    digests: Iterable[str],
    scope_values: Mapping[str, Any],
    update_tag: int,
    *,
    batch_size: int = 500,
) -> None:
    """Refresh an unchanged image and its existing layer closure before cleanup."""

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    unique_digests = sorted(set(digests))
    if not unique_digests:
        return
    for digest_batch in batch(unique_digests, size=batch_size):
        _refresh_layer_closure_batch(
            neo4j_session,
            shape,
            digest_batch,
            scope_values,
            update_tag,
        )


def _refresh_layer_closure_batch(
    neo4j_session: neo4j.Session,
    shape: ContainerImageLayerGraphShape,
    digests: Sequence[str],
    scope_values: Mapping[str, Any],
    update_tag: int,
) -> None:
    scope_match, scope_parameters = _scope_parameters(shape, scope_values)
    parameters = {
        "digests": list(digests),
        "update_tag": update_tag,
        **scope_parameters,
    }

    if shape.image_scoped:
        image_query = f"""
        MATCH (scope:{shape.scope_label} {{{scope_match}}})
              -[resource:RESOURCE]->(img:{shape.image_label})
        WHERE img.{shape.image_digest_property} IN $digests
        SET img.lastupdated = $update_tag,
            resource.lastupdated = $update_tag
        """
    else:
        image_query = f"""
        MATCH (img:{shape.image_label})
        WHERE img.{shape.image_digest_property} IN $digests
        SET img.lastupdated = $update_tag
        """
    run_write_query(neo4j_session, image_query, **parameters)

    layer_query = f"""
    MATCH (img:{shape.image_label})
    WHERE img.{shape.image_digest_property} IN $digests
    UNWIND coalesce(img.{shape.image_layer_ids_property}, []) AS layer_id
    MATCH (layer:{shape.layer_label} {{{shape.layer_id_property}: layer_id}})
    SET layer.lastupdated = $update_tag
    """
    run_write_query(neo4j_session, layer_query, **parameters)

    if shape.layer_scoped:
        layer_scope_query = f"""
        MATCH (img:{shape.image_label})
        WHERE img.{shape.image_digest_property} IN $digests
        UNWIND coalesce(img.{shape.image_layer_ids_property}, []) AS layer_id
        MATCH (scope:{shape.scope_label} {{{scope_match}}})
              -[resource:RESOURCE]->
              (layer:{shape.layer_label} {{{shape.layer_id_property}: layer_id}})
        SET resource.lastupdated = $update_tag
        """
        run_write_query(neo4j_session, layer_scope_query, **parameters)

    if shape.image_layer_rel_types:
        image_layer_query = f"""
        MATCH (img:{shape.image_label})-[relationship]->
              (layer:{shape.layer_label})
        WHERE img.{shape.image_digest_property} IN $digests
          AND type(relationship) IN $relationship_types
          AND layer.{shape.layer_id_property}
              IN coalesce(img.{shape.image_layer_ids_property}, [])
        SET relationship.lastupdated = $update_tag
        """
        run_write_query(
            neo4j_session,
            image_layer_query,
            relationship_types=list(shape.image_layer_rel_types),
            **parameters,
        )

    if shape.stable_image_rel_types:
        matchlink_predicate = ""
        if shape.stable_image_rels_are_matchlinks:
            if len(shape.scope_properties) != 1:
                raise ValueError(
                    "MatchLink relationship refresh requires a single-property scope",
                )
            scope_parameter = f"scope_{shape.scope_properties[0]}"
            matchlink_predicate = f"""
              AND relationship._sub_resource_label = '{shape.scope_label}'
              AND relationship._sub_resource_id = ${scope_parameter}
            """
        stable_image_rel_query = f"""
        MATCH (img:{shape.image_label})-[relationship]->()
        WHERE img.{shape.image_digest_property} IN $digests
          AND type(relationship) IN $relationship_types
          {matchlink_predicate}
        SET relationship.lastupdated = $update_tag
        """
        run_write_query(
            neo4j_session,
            stable_image_rel_query,
            relationship_types=list(shape.stable_image_rel_types),
            **parameters,
        )

    if shape.has_next:
        next_query = f"""
        MATCH (img:{shape.image_label})
        WHERE img.{shape.image_digest_property} IN $digests
        WITH coalesce(img.{shape.image_layer_ids_property}, []) AS layer_ids
        UNWIND CASE
            WHEN size(layer_ids) > 1 THEN range(0, size(layer_ids) - 2)
            ELSE []
        END AS index
        MATCH (left:{shape.layer_label}
               {{{shape.layer_id_property}: layer_ids[index]}})
              -[relationship:NEXT]->
              (right:{shape.layer_label}
               {{{shape.layer_id_property}: layer_ids[index + 1]}})
        SET relationship.lastupdated = $update_tag
        """
        run_write_query(neo4j_session, next_query, **parameters)
