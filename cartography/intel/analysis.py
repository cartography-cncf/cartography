import logging
import pathlib

import neo4j

from cartography.config import Config
from cartography.graph.job import GraphJob

logger = logging.getLogger(__name__)


def run(neo4j_session: neo4j.Session, config: Config) -> None:
    analysis_job_directory_path = config.analysis_job_directory
    if not analysis_job_directory_path:
        logger.info("Skipping analysis because no job path was provided.")
        return
    analysis_job_directory = pathlib.Path(analysis_job_directory_path)
    if not analysis_job_directory.exists():
        logger.warning(
            "Skipping analysis because the provided job path '%s' does not exist.",
            analysis_job_directory,
        )
        return
    if not analysis_job_directory.is_dir():
        logger.warning(
            "Skipping analysis because the provided job path '%s' is not a directory.",
            analysis_job_directory,
        )
        return
    logger.info("Loading analysis jobs from directory: %s", analysis_job_directory)
    for path in analysis_job_directory.glob("**/*.json"):
        logger.info("Running discovered analysis job: %s", path)
        try:
            GraphJob.run_from_json_file(
                path,
                neo4j_session,
                {"UPDATE_TAG": config.update_tag},
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            logger.exception(
                "An exception occurred while executing discovered analysis job: %s",
                path,
            )
