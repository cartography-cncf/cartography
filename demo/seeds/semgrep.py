from unittest.mock import patch

import cartography.intel.semgrep.dependencies
import cartography.intel.semgrep.deployment
import cartography.intel.semgrep.findings
import tests.data.semgrep.dependencies
import tests.data.semgrep.deployment
import tests.data.semgrep.sca
from demo.seeds.base import Seed

TENANT_ID = 11223344
SEMGREP_APP_TOKEN = "your_semgrep_app_token"
ECOSYSTEMS = "gomod,npm"
DEPLOYMENT_ID = tests.data.semgrep.deployment.DEPLOYMENTS["id"]
DEPLOYMENT_SLUG = tests.data.semgrep.deployment.DEPLOYMENTS["slug"]


def _mock_get_dependencies(semgrep_app_token: str, deployment_id: str, ecosystem: str):
    if ecosystem == "gomod":
        return tests.data.semgrep.dependencies.RAW_DEPS_GOMOD
    elif ecosystem == "npm":
        return tests.data.semgrep.dependencies.RAW_DEPS_NPM
    else:
        raise ValueError(f"Unexpected value for `ecosystem`: {ecosystem}")


TEST_REPO_ID = "https://github.com/org/repository"
TEST_REPO_FULL_NAME = "org/repository"
TEST_REPO_NAME = "repository"


# TODO: Replace with actual github demo data
def create_dependency_nodes(neo4j_session) -> None:
    # Creates a set of dependency nodes in the graph
    neo4j_session.run(
        """
        MERGE (dep:Dependency{id: $dep_id})
        ON CREATE SET dep.firstseen = timestamp()
        SET dep.lastupdated = $update_tag
        """,
        dep_id="moment|2.29.2",
        update_tag=1234,
    )


# TODO: Replace with actual CVE data
def create_cve_nodes(neo4j_session) -> None:
    # Creates a set of CVE nodes in the graph
    neo4j_session.run(
        """
        MERGE (cve:CVE{id: $cve_id})
        ON CREATE SET cve.firstseen = timestamp()
        SET cve.lastupdated = $update_tag
        """,
        cve_id="CVE-2022-31129",
        update_tag=1234,
    )


class SemgrepSeed(Seed):
    @patch.object(
        cartography.intel.semgrep.deployment,
        "get_deployment",
        return_value=tests.data.semgrep.deployment.DEPLOYMENTS,
    )
    @patch.object(
        cartography.intel.semgrep.dependencies,
        "get_dependencies",
        side_effect=_mock_get_dependencies,
    )
    @patch.object(
        cartography.intel.semgrep.findings,
        "get_sca_vulns",
        return_value=tests.data.semgrep.sca.RAW_VULNS,
    )
    def seed(self, *args) -> None:
        self._seed_deployments()
        self._seed_dependencies()
        self._seed_findings()

    def _seed_deployments(self) -> None:
        cartography.intel.semgrep.deployment.sync_deployment(
            self.neo4j_session,
            SEMGREP_APP_TOKEN,
            self.update_tag,
            {"UPDATE_TAG": self.update_tag},
        )

    def _seed_dependencies(self) -> None:
        cartography.intel.semgrep.dependencies.sync_dependencies(
            self.neo4j_session,
            SEMGREP_APP_TOKEN,
            ECOSYSTEMS,
            self.update_tag,
            {
                "UPDATE_TAG": self.update_tag,
                "DEPLOYMENT_ID": DEPLOYMENT_ID,
                "DEPLOYMENT_SLUG": DEPLOYMENT_SLUG,
            },
        )

    def _seed_findings(self) -> None:
        # TODO: Remove after modifing the gihub data
        create_dependency_nodes(self.neo4j_session)
        # TODO: Remove after inserting the CVE data
        create_cve_nodes(self.neo4j_session)
        cartography.intel.semgrep.findings.sync_findings(
            self.neo4j_session,
            SEMGREP_APP_TOKEN,
            self.update_tag,
            {
                "UPDATE_TAG": self.update_tag,
                "DEPLOYMENT_ID": DEPLOYMENT_ID,
                "DEPLOYMENT_SLUG": DEPLOYMENT_SLUG,
            },
        )
