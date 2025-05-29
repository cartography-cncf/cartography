import logging
import pathlib
from typing import Optional

import neo4j

from cartography.config import Config
from cartography.graph.job import GraphJob
from cartography.settings import check_module_settings
from cartography.settings import populate_settings_from_config
from cartography.settings import settings

logger = logging.getLogger(__name__)


def run(neo4j_session: neo4j.Session, config: Optional[Config] = None) -> None:
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings("Analysis", ["job_directory"]):
        return

    analysis_job_directory = pathlib.Path(settings.analysis.job_directory)
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
                {"UPDATE_TAG": settings.common.update_tag},
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            logger.exception(
                "An exception occurred while executing discovered analysis job: %s",
                path,
            )
