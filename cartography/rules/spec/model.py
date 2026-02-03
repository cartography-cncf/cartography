import json
import logging
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any
from typing import no_type_check

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator

logger = logging.getLogger(__name__)


class Module(str, Enum):
    """Services that can be monitored"""

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

    DIGITALOCEAN = "DigitalOcean"
    """DigitalOcean cloud services"""

    DUO = "Duo"
    """Duo authentication"""

    ENTRA = "Entra"
    """Entra identity and access management"""

    GCP = "GCP"
    """Google Cloud Platform"""

    GITHUB = "GitHub"
    """GitHub source code management"""

    GOOGLEWORKSPACE = "GoogleWorkspace"
    """Google Workspace identity and access management"""

    JAMF = "Jamf"
    """Jamf endpoint security"""

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

    SCALEWAY = "Scaleway"
    """Scaleway cloud services"""

    SEMGREP = "Semgrep"
    """Semgrep code security"""

    SENTINELONE = "SentinelOne"
    """SentinelOne endpoint security"""

    SNIPEIT = "Snipe-IT"
    """Snipe-IT asset management"""

    SPACELIFT = "SpaceLift"
    """SpaceLift infrastructure as code"""

    TAILSCALE = "TailScale"
    """TailScale VPN"""

    TRIVY = "Trivy"
    """Trivy vulnerability scanner"""

    CROSS_CLOUD = "Cross-Cloud"
    """Multi-cloud or provider-agnostic rules"""


class Maturity(str, Enum):
    """Maturity levels for Facts."""

    EXPERIMENTAL = "EXPERIMENTAL"
    """Experimental: Initial version, may be unstable or incomplete."""

    STABLE = "STABLE"
    """Stable: Well-tested and reliable for production use."""


MODULE_TO_CARTOGRAPHY_INTEL = {
    Module.AIRBYTE: "airbyte",
    Module.ANTHROPIC: "anthropic",
    Module.AWS: "aws",
    Module.AZURE: "azure",
    Module.BIGFIX: "bigfix",
    Module.CLOUDFLARE: "cloudflare",
    Module.CROWDSTRIKE: "crowdstrike",
    Module.DIGITALOCEAN: "digitalocean",
    Module.DUO: "duo",
    Module.ENTRA: "entra",
    Module.GCP: "gcp",
    Module.GITHUB: "github",
    Module.GOOGLEWORKSPACE: "googleworkspace",
    Module.JAMF: "jamf",
    Module.KANDJI: "kandji",
    Module.KEYCLOAK: "keycloak",
    Module.KUBERNETES: "kubernetes",
    Module.LASTPASS: "lastpass",
    Module.OCI: "oci",
    Module.OKTA: "okta",
    Module.OPENAI: "openai",
    Module.PAGERDUTY: "pagerduty",
    Module.SCALEWAY: "scaleway",
    Module.SEMGREP: "semgrep",
    Module.SENTINELONE: "sentinelone",
    Module.SNIPEIT: "snipeit",
    Module.SPACELIFT: "spacelift",
    Module.TAILSCALE: "tailscale",
    Module.TRIVY: "trivy",
}


@dataclass(frozen=True)
class Framework:
    """
    A reference to a compliance framework requirement.

    All fields are case-insensitive and normalized to lowercase on creation.

    Attributes:
        name: Full name of the framework (e.g., "cis aws foundations benchmark").
        short_name: Abbreviated name for filtering (e.g., "cis").
        requirement: The specific requirement identifier (e.g., "1.14").
        scope: Optional platform or domain the framework applies to (e.g., "aws", "gcp").
        revision: Optional version/revision of the framework (e.g., "5.0").
    """

    name: str
    short_name: str
    requirement: str
    scope: str | None = None
    revision: str | None = None

    def __post_init__(self) -> None:
        # Normalize all fields to lowercase for case-insensitive comparison
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
    asset_id_field: str | None = None
    """
    The field name in the output model that uniquely identifies an asset.
    When set, failing count is computed as the count of distinct values of this field
    rather than the total number of finding rows. This is needed when a single asset
    can produce multiple finding rows (e.g., one security group with multiple violating rules).
    """


class Finding(BaseModel):
    """Base class for Rule finding models."""

    # TODO: make this property mandatory one all modules have been updated to new datamodel
    source: str | None = None
    """The source of the Fact data, e.g. the specific Cartography module that ingested the data. This field is useful especially for CROSS_CLOUD facts."""
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
    """Compliance frameworks this rule maps to (e.g., CIS benchmarks)."""

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
