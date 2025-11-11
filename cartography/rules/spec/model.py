import logging
from dataclasses import dataclass
from enum import Enum

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


class Maturity(str, Enum):
    """Maturity levels for Facts."""

    EXPERIMENTAL = "EXPERIMENTAL"
    """Experimental: Initial version, may be unstable or incomplete."""

    STABLE = "STABLE"
    """Stable: Well-tested and reliable for production use."""


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
    maturity: Maturity
    """The maturity level of the Fact query."""
    # TODO can we lint the queries. full-on integ tests here are overkill though.
    cypher_query: str
    """The Cypher query to gather information about the environment. Returns data field by field e.g. `RETURN node.prop1, node.prop2`."""


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
    version: str
    """The version of the Finding definition."""
    facts: tuple[Fact, ...]
    """The Facts that contribute to this Finding."""
    references: tuple[str, ...] = ()
    """References or links to external resources related to the Finding."""

    @property
    def modules(self) -> set[Module]:
        """Returns the set of modules associated with this finding."""
        return {fact.module for fact in self.facts}

    def get_fact_by_id(self, fact_id: str) -> Fact | None:
        """Returns a fact by its ID, or None if not found."""
        for fact in self.facts:
            if fact.id.lower() == fact_id.lower():
                return fact
        return None
