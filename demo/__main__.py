import logging
import os
import time

import neo4j

from cartography.intel import create_indexes
from demo.seeds.digitalocean import DigitalOceanSeed
from demo.seeds.entra import EntraSeed
from demo.seeds.github import GithubSeed
from demo.seeds.lastpass import LastpassSeed
from demo.seeds.snipeit import SnipeitSeed

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

    # Load the demo data
    logger.info("Loading demo data...")
    # TODO: AWS
    # TODO: Azure
    # TODO: BigFix
    # TODO: CrowdStrike
    # TODO: CVE
    logger.info("    DigitalOcean")
    DigitalOceanSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: Duo
    logger.info("    Entra")
    EntraSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: GCP
    logger.info("    GitHub")
    GithubSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: Jamf
    # TODO: Kandji
    # TODO: Kubernetes
    logger.info("    LastPass")
    LastpassSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: OCI
    # TODO: Okta
    # TODO: PagerDuty
    # TODO: Semgrep
    logger.info("    SnipeIT")
    SnipeitSeed(neo4j_session, UPDATE_TAG).run()
    # TODO: Analysis

    # Close the session
    neo4j_session.close()


if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)
    main()
