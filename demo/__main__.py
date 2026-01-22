import argparse
import importlib
import inspect
import logging
import os
import pkgutil

import neo4j

import cartography.intel.analysis
from cartography.config import Config
from cartography.intel import create_indexes
from cartography.intel import ontology
from demo import seeds
from demo.seeds.base import AsyncSeed
from demo.seeds.base import Seed

NEO4J_URL = os.environ.get("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
UPDATE_TAG = 0

logger = logging.getLogger(__name__)


def main(force_flag: bool, analysis_job_directory: str) -> None:
    # Set up Neo4j connection
    if NEO4J_USER and NEO4J_PASSWORD:
        neo4j_driver = neo4j.GraphDatabase.driver(
            NEO4J_URL,
            auth=neo4j.basic_auth(NEO4J_USER, NEO4J_PASSWORD),
        )
    else:
        neo4j_driver = neo4j.GraphDatabase.driver(NEO4J_URL)
    neo4j_session = neo4j_driver.session()

    # Config
    config = Config(
        neo4j_uri=NEO4J_URL,
        neo4j_user=NEO4J_USER,
        neo4j_password=NEO4J_PASSWORD,
        ontology_users_source="duo",
        ontology_devices_source="snipeit",
        analysis_job_directory=analysis_job_directory,
    )

    # Check if the database is empty
    logger.info("Checking if the database is empty...")
    result = neo4j_session.run(
        "MATCH (n) WHERE n.lastupdated > 0 RETURN COUNT(n) AS count "
    )
    count = result.single()["count"]
    if count > 0:
        if force_flag:
            logger.warning(
                "Force flag is set. Proceeding to clear the database without confirmation."
            )
        else:
            print(
                "Database already contains data. Are you sure you want to continue? (y/N)"
            )
            answer = input()
            if answer.lower() != "y":
                logger.info("Exiting without making any changes.")
                neo4j_session.close()
                return

    # Clear the previous database
    logger.info("Clearing the existing database...")
    neo4j_session.run("MATCH (n) DETACH DELETE n;")

    # Create indexes
    logger.info("Creating indexes...")
    create_indexes.run(neo4j_session, config)
    # Wait for indexes to finish building to avoid "insanely frequent schema changes"
    # error when we immediately start writing data.
    logger.info("Waiting for indexes to become online...")
    try:
        neo4j_session.run("CALL db.awaitIndexes()")
    except neo4j.exceptions.Neo4jError:
        # Some Neo4j versions require a timeout argument.
        neo4j_session.run("CALL db.awaitIndexes('600s')")

    # Load demo data
    seed_classes: list[type] = []
    for _, mod_name, _ in pkgutil.iter_modules(seeds.__path__):
        if mod_name == "base":
            continue
        module = importlib.import_module(f"demo.seeds.{mod_name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # A valid seed is a concrete subclass declared inside demo.seeds.*
            if (
                issubclass(obj, (Seed, AsyncSeed))
                and obj not in (Seed, AsyncSeed)
                and obj.__module__.startswith("demo.seeds")
            ):
                seed_classes.append(obj)

    # Preserve deterministic order for reproducibility
    seed_classes.sort(key=lambda cls: cls.__name__)

    logger.info("Loading demo data via %d seed classes...", len(seed_classes))
    for seed_cls in seed_classes:
        logger.info("    loading %s", seed_cls.__name__)
        try:
            seed_cls(neo4j_session, UPDATE_TAG).run()
        except Exception:
            logger.exception("Seed %s failed", seed_cls.__name__)

    # Ontology
    logger.info("Building ontology ...")
    ontology.run(neo4j_session, config)

    # Analysis
    logger.info("Running analysis...")
    cartography.intel.analysis.run(neo4j_session, config)

    # Close the session
    neo4j_session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""\
Cartography Demo: Load demo data into a Neo4j database for testing and development purposes.

This script will clear the existing database and load a predefined set of demo data.

Ensure you have a Neo4j instance running and accessible at the specified NEO4J_URL.
The default URL is 'bolt://localhost:7687'. You can change this by setting the NEO4J_URL
environment variable.

Use the -v or --verbose flag for detailed logging, or -q or --quiet to suppress most logs.
The script will prompt for confirmation if the database is not empty. Use with caution
as it will delete all existing data in the Neo4j database.

You can bypass the confirmation prompt by using the --force flag.
"""
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging for cartography.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Restrict cartography logging to warnings and errors only.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force the script to run without confirmation, even if the database is not empty.",
    )
    parser.add_argument(
        "--analysis-job-directory",
        type=str,
        default="cartography/data/jobs/analysis",
        help=(
            "A path to a directory containing analysis jobs to run at the conclusion of the sync. cartography will "
            "discover all JSON files in the given directory (and its subdirectories) and pass them to the GraphJob "
            "API to execute against the graph. This allows you to apply data transformation and augmentation at "
            "the end of a sync run without writing code. cartography does not guarantee the order in which the "
            "jobs are executed."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)

    main(args.force, args.analysis_job_directory)
