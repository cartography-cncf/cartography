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
        job_name = path.name
        # Minimal fix for aws_s3acl_analysis.json dependency on AWS_ID
        if job_name == "aws_s3acl_analysis.json" and "AWS_ID" not in config.__dict__:
            logger.warning(
                "Skipping %s because AWS_ID is missing. Run the AWS sync module in the same execution to enable this analysis.",
                job_name,
            )
            continue
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
