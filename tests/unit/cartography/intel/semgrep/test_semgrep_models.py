"""
Schema-level checks that every Semgrep finding node connects to both
GitHubRepository and GitLabProject via a FOUND_IN / REQUIRES relationship.
"""

from dataclasses import fields

import pytest

from cartography.models.core.relationships import LinkDirection
from cartography.models.semgrep.dependencies import SemgrepGoLibrarySchema
from cartography.models.semgrep.dependencies import SemgrepNpmLibrarySchema
from cartography.models.semgrep.findings import SemgrepSCAFindingSchema
from cartography.models.semgrep.ossfindings import OSSSemgrepSASTFindingSchema
from cartography.models.semgrep.sast import SemgrepSASTFindingSchema
from cartography.models.semgrep.secrets import SemgrepSecretsFindingSchema


def _find_rel(schema, target_label, rel_label):
    for rel in schema.other_relationships.rels:
        if rel.target_node_label == target_label and rel.rel_label == rel_label:
            return rel
    return None


def _matcher_to_dict(matcher):
    return {f.name: getattr(matcher, f.name) for f in fields(matcher)}


@pytest.mark.parametrize(
    "schema,rel_label,direction,matcher_property",
    [
        (
            SemgrepSCAFindingSchema(),
            "FOUND_IN",
            LinkDirection.OUTWARD,
            "repositoryUrl",
        ),
        (
            SemgrepSASTFindingSchema(),
            "FOUND_IN",
            LinkDirection.OUTWARD,
            "repositoryUrl",
        ),
        (
            SemgrepSecretsFindingSchema(),
            "FOUND_IN",
            LinkDirection.OUTWARD,
            "repositoryUrl",
        ),
        (
            OSSSemgrepSASTFindingSchema(),
            "FOUND_IN",
            LinkDirection.OUTWARD,
            "repositoryUrl",
        ),
        (
            SemgrepGoLibrarySchema(),
            "REQUIRES",
            LinkDirection.INWARD,
            "repo_url",
        ),
        (
            SemgrepNpmLibrarySchema(),
            "REQUIRES",
            LinkDirection.INWARD,
            "repo_url",
        ),
    ],
)
def test_semgrep_schema_has_gitlab_project_rel(
    schema, rel_label, direction, matcher_property
):
    rel = _find_rel(schema, "GitLabProject", rel_label)
    assert rel is not None, f"{schema.label} is missing a GitLabProject {rel_label} rel"
    assert rel.direction == direction
    # The matcher must join on GitLabProject.web_url against the Semgrep finding's URL.
    matcher_dict = _matcher_to_dict(rel.target_node_matcher)
    assert "web_url" in matcher_dict
    assert matcher_dict["web_url"].name == matcher_property
