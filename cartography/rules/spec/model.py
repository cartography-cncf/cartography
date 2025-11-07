import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import no_type_check

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class Module(str, Enum):
    """Services that can be monitored"""

    AWS = "AWS"
    """Amazon Web Services"""

    AZURE = "Azure"
    """Microsoft Azure"""

    GCP = "GCP"
    """Google Cloud Platform"""

    GITHUB = "GitHub"
    """GitHub source code management"""

    OKTA = "Okta"
    """Okta identity and access management"""

    CLOUDFLARE = "Cloudflare"
    """Cloudflare services"""

    CROSS_CLOUD = "CROSS_CLOUD"
    """Multi-cloud or provider-agnostic rules"""


MODULE_TO_CARTOGRAPHY_INTEL = {
    Module.AWS: "aws",
    Module.AZURE: "azure",
    Module.GCP: "gcp",
    Module.GITHUB: "github",
    Module.OKTA: "okta",
    Module.CLOUDFLARE: "cloudflare",
}


@dataclass(frozen=True)
class Fact:
    """A Fact gathers information about the environment using a Cypher query."""

    id: str
    """A descriptive identifier for the Fact. By convention, should be lowercase and use underscores like `finding-name-module`."""
    name: str
    """A descriptive name for the Fact."""
    description: str
    """More details about the Fact. Information on details that we're querying for."""
    module: Module
    """The Module that the Fact is associated with e.g. AWS, Azure, GCP, etc."""
    # TODO can we lint the queries. full-on integ tests here are overkill though.
    cypher_query: str
    """The Cypher query to gather information about the environment. Returns data field by field e.g. `RETURN node.prop1, node.prop2`."""
    cypher_visual_query: str
    """
    Same as `cypher_query`, returns it in a visual format for the web interface with `.. RETURN *`.
    Often includes additional relationships to help give context.
    """


# Finding output model base class
class FindingOutput(BaseModel):
    """Base class for Finding output models."""

    # TODO: make this property mandatory one all modules have been updated to new datamodel
    source: str | None = None
    """The source of the Fact data, e.g. the specific Cartography module that ingested the data. This field is useful especially for CROSS_CLOUD facts."""
    extra: dict[str, Any] = {}
    """A dictionary to hold any extra fields returned by the Fact query that are not explicitly defined in the output model."""

    # Config to coerce numbers to strings during instantiation
    model_config = ConfigDict(coerce_numbers_to_str=True)

    # Coerce to strings
    @no_type_check
    @model_validator(mode="before")
    @classmethod
    def coerce_to_string(cls, data: Any):
        if not isinstance(data, dict):
            return data

        for name, field in cls.model_fields.items():
            if field.annotation is not str:
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
class Finding:
    """A Finding represents a security issue or misconfiguration detected in the environment."""

    id: str
    """A unique identifier for the Finding. Should be globally unique within Cartography."""
    name: str
    """A brief name for the Finding."""
    tags: tuple[str, ...]
    """Tags associated with the Finding for categorization and filtering."""
    description: str
    """A brief description of the Finding. Can include details about the security issue or misconfiguration."""
    facts: tuple[Fact, ...]
    """The Facts that contribute to this Finding."""
    output_model: type[FindingOutput]
    """The output model class for the Finding."""

    def parse_results(self, fact_results: list[dict[str, Any]]) -> list[FindingOutput]:
        # DOC
        result: list[FindingOutput] = []
        for result_item in fact_results:
            parsed_output: dict[str, Any] = {"extra": {}, "source": None}
            for key, value in result_item.items():
                if key == "_source":
                    parsed_output["source"] = value
                elif key not in self.output_model.model_fields and value is not None:
                    parsed_output["extra"][key] = value
                else:
                    parsed_output[key] = value
            try:
                # Try to parse normally
                result.append(self.output_model(**parsed_output))
            except ValidationError as e:
                # Handle validation errors
                logger.warning(
                    "Validation error parsing finding output for finding %s: %s",
                    self.id,
                    e,
                )
        return result

    @property
    def modules(self) -> set[Module]:
        """Returns the set of modules associated with this finding."""
        return {fact.module for fact in self.facts}


@dataclass(frozen=True)
class Requirement:
    """
    A requirement within a security framework with one or more facts.

    Notes:
    - `attributes` is reserved for metadata such as tags, categories, or references.
    - Do NOT put evaluation logic, thresholds, or org-specific preferences here.
    """

    id: str
    """A unique identifier for the requirement, e.g. T1098 in MITRE ATT&CK."""
    name: str
    """A brief name for the requirement, e.g. "Account Manipulation"."""
    description: str
    """A brief description of the requirement."""
    target_assets: str
    """
    A short description of the assets that this requirement is related to. E.g. "Cloud
    identities that can manipulate other identities". This field is used as
    documentation: `description` tells us information about the requirement;
    `target_assets` tells us what specific objects in cartography we will search for to
    find Facts related to the requirement.
    """
    findings: tuple[Finding, ...]
    """The findings that are related to this requirement."""
    attributes: dict[str, Any] | None = None
    """
    Metadata attributes for the requirement. Example:
    ```json
    {
        "tactic": "initial_access",
        "technique_id": "T1190",
        "services": ["ec2", "s3", "rds", "azure_storage"],
        "providers": ["AWS", "AZURE"],
    }
    ```
    """
    requirement_url: str | None = None
    """A URL reference to the requirement in the framework, e.g. https://attack.mitre.org/techniques/T1098/"""


@dataclass(frozen=True)
class Framework:
    """A security framework containing requirements for comprehensive assessment."""

    id: str
    name: str
    description: str
    version: str
    requirements: tuple[Requirement, ...]
    source_url: str | None = None

    def get_requirement_by_id(self, requirement_id: str) -> Requirement | None:
        """Returns a requirement by its ID, or None if not found."""
        for req in self.requirements:
            if req.id.lower() == requirement_id.lower():
                return req
        return None

    def get_findings_by_requirement(self, requirement_id: str) -> list[Finding]:
        """Returns all findings for a given requirement ID. If no requirement ID is provided, returns all findings in the framework."""
        requirement = self.get_requirement_by_id(requirement_id)
        if requirement:
            return list(requirement.findings)
        return []

    def get_finding_by_id(self, requirement_id: str, finding_id: str) -> Finding | None:
        """Returns a finding by its ID within a requirement, or None if not found."""
        for finding in self.get_findings_by_requirement(requirement_id):
            if finding.id.lower() == finding_id.lower():
                return finding
        return None

    def get_facts_by_finding(self, requirement_id: str, finding_id: str) -> list[Fact]:
        """Returns all facts for a given finding ID within a requirement."""
        finding = self.get_finding_by_id(requirement_id, finding_id)
        if finding:
            return list(finding.facts)
        return []

    def get_fact_by_id(
        self, requirement_id: str, finding_id: str, fact_id: str
    ) -> Fact | None:
        """Returns a fact by its ID within a finding and requirement, or None if not found."""
        for fact in self.get_facts_by_finding(requirement_id, finding_id):
            if fact.id.lower() == fact_id.lower():
                return fact
        return None
