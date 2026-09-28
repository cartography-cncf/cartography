"""
Repository mapping file for the Zizmor module.

Zizmor's JSON output carries no repository identity: for a local run, the only
path information is the literal argument that was passed on the command line.
Callers therefore declare, in a YAML file, which repository each report belongs
to. This mirrors the Semgrep OSS repository mapping file.
"""

import logging

import yaml
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic import ValidationError

from cartography.intel.common.object_store import filter_report_refs
from cartography.intel.common.object_store import read_text_report
from cartography.intel.common.object_store import ReportReader

logger = logging.getLogger(__name__)


class ZizmorRepositoryMappingEntry(BaseModel):
    """One repository and the zizmor reports that were produced for it."""

    owner: str
    repo: str
    url: str
    branch: str
    reports: list[str] = Field(min_length=1)

    @field_validator("owner", "repo", "url", "branch")  # type: ignore[misc]
    @classmethod
    def _validate_required_string(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be empty.")
        return normalized

    @field_validator("reports")  # type: ignore[misc]
    @classmethod
    def _validate_reports(cls, reports: list[str]) -> list[str]:
        normalized_reports: list[str] = []
        for raw_report in reports:
            report_source = raw_report.strip()
            if not report_source:
                raise ValueError("Report source cannot be empty.")
            normalized_reports.append(report_source)
        return normalized_reports

    @property
    def repository_name(self) -> str:
        return f"{self.owner}/{self.repo}"

    @property
    def repository_context(self) -> dict[str, str]:
        return {
            "owner": self.owner,
            "repo": self.repo,
            "repositoryName": self.repository_name,
            "repositoryUrl": self.url,
            "branch": self.branch,
        }


class ZizmorRepositoryMappingFile(BaseModel):
    repositories: list[ZizmorRepositoryMappingEntry] = Field(min_length=1)

    @model_validator(mode="after")  # type: ignore[misc]
    def _reject_duplicate_urls(self) -> "ZizmorRepositoryMappingFile":
        """
        Reject two entries pointing at the same repository.

        A repository URL is the identity of a repository throughout the module:
        it is the join key for `GitHubRepository`, part of every finding's id,
        and the scope of the cleanup query. Two entries sharing one URL break
        that in two ways. Cleanup is authorized per entry, so a fully read entry
        would authorize deleting stale findings for the repository even though a
        second entry for it failed. And because branch is not part of a finding's
        id, entries differing only by branch collide on the same nodes, leaving
        whichever loaded last to win.

        Comparison is case-insensitive: GitHub repository names are unique
        without regard to case, so two URLs differing only by case are the same
        repository and would collide just the same.
        """
        seen: dict[str, str] = {}
        for entry in self.repositories:
            key = entry.url.casefold()
            if key in seen:
                raise ValueError(
                    "Each repository may only appear once, but "
                    f"{entry.url!r} and {seen[key]!r} refer to the same repository. "
                    "List every report for a repository under a single entry's "
                    "'reports'."
                )
            seen[key] = entry.url
        return self


def get_zizmor_repository_mappings(
    reader: ReportReader,
) -> list[ZizmorRepositoryMappingEntry]:
    """
    Read and validate a Zizmor repository mapping file.
    """
    mapping_refs = filter_report_refs(reader.list_reports(), suffix=".yaml")
    mapping_refs.extend(filter_report_refs(reader.list_reports(), suffix=".yml"))

    if len(mapping_refs) != 1:
        raise ValueError(
            "Zizmor repository mapping source must contain exactly one YAML file."
        )
    mapping_ref = mapping_refs[0]

    try:
        mapping_document = yaml.safe_load(read_text_report(reader, mapping_ref))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"Zizmor repository mapping file must be valid YAML: {mapping_ref.uri}"
        ) from exc

    try:
        mapping_file = ZizmorRepositoryMappingFile.model_validate(mapping_document)
    except ValidationError as exc:
        raise ValueError(
            f"Zizmor repository mapping file is invalid {mapping_ref.uri}: {exc}"
        ) from exc

    return mapping_file.repositories
