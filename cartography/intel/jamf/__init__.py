from typing import Optional

import neo4j

from cartography.intel.jamf import computers
from cartography.config import Config
from cartography.settings import populate_settings_from_config
from cartography.settings import check_module_settings
from cartography.settings import settings
from cartography.util import timeit


@timeit
def start_jamf_ingestion(neo4j_session: neo4j.Session, config: Optional[Config]) -> None:
    # DEPRECATED: This is a temporary measure to support the old config format
    # and the new config format. The old config format is deprecated and will be removed in a future release.
    if config is not None:
        populate_settings_from_config(config)

    if not check_module_settings('JAMF', ['base_url', 'username', 'password']):
        return

    common_job_parameters = {
        "UPDATE_TAG": settings.common.update_tag,
    }
    computers.sync(
        neo4j_session,
        settings.jamf.base_url,
        settings.jamf.user,
        settings.jamf.password,
        common_job_parameters,
    )
