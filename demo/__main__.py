import logging
import os
import time

import neo4j

from cartography.intel import create_indexes
from demo.seeds.cloudlare import CloudflareSeed
from demo.seeds.digitalocean import DigitalOceanSeed
from demo.seeds.duo import DuoSeed
from demo.seeds.entra import EntraSeed
from demo.seeds.github import GithubSeed
from demo.seeds.kandji import KandjiSeed
from demo.seeds.lastpass import LastpassSeed
from demo.seeds.semgrep import SemgrepSeed
from demo.seeds.snipeit import SnipeitSeed
from demo.seeds.tailscale import TailscaleSeed

NEO4J_URL = os.environ.get("NEO4J_URL", "bolt://localhost:7687")

logger = logging.getLogger(__name__)


def main():
    # Set up Neo4j connection
    neo4j_driver = neo4j.GraphDatabase.driver(NEO4J_URL)
    neo4j_session = neo4j_driver.session()

    UPDATE_TAG = int(time.time())

    # Clear the previous database
    logger.info("Clearing the existing database...")
    neo4j_session.run("MATCH (n) DETACH DELETE n;")

    # Create indexes
    logger.info("Creating indexes...")
    create_indexes.run(neo4j_session, None)

    # Create Human
    # This is an uggly hack to create a human node for the demo.
    # We are still working on a better way to build humans (and other abstracts nodes) on Cartography
    logger.info("Creating human node...")
    humans = [
        {"email": "mbsimpson@simpson.corp"},
        {"email": "hjsimpson@simpson.corp"},
        {"email": "lmsimpson@simpson.corp"},
        {"email": "bjsimpson@simpson.corp"},
    ]
    neo4j_session.run(
        "UNWIND $data as item MERGE (h:Human{email: item.email})",
        data=humans,
    )

    # Load the demo data
    logger.info("Loading demo data...")
    # TODO: AWS
    # TODO: Azure
    # TODO: BigFix
    logger.info("    loading Cloudflare")
    CloudflareSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: CrowdStrike
    # TODO: CVE
    logger.info("    loading DigitalOcean")
    DigitalOceanSeed(neo4j_session, UPDATE_TAG).run()
    logger.info("    loading Duo")
    DuoSeed(neo4j_session, UPDATE_TAG).run()
    logger.info("    loading Entra")
    EntraSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: GCP after data model migration
    logger.info("    loading GitHub")
    GithubSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: Gsuite after data model migration
    # TODO: Jamf after data model migration
    logger.info("    loading Kandji")
    KandjiSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: Kubernetes
    logger.info("    loading LastPass")
    LastpassSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: OCI after data model migration
    # TODO: Okta after data model migration
    # TODO: PagerDuty after data model migration
    logger.info("    loading Semgrep")
    SemgrepSeed(neo4j_session, UPDATE_TAG).run()
    logger.info("    loading SnipeIT")
    SnipeitSeed(neo4j_session, UPDATE_TAG).run()
    logger.info("    loading Tailscale")
    TailscaleSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: Analysis

    # Close the session
    neo4j_session.close()


if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)
    main()
