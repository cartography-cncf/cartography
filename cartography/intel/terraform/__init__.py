import logging

import neo4j

from cartography.config import Config
from cartography.intel.terraform.state import sync_state_file
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def start_terraform_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.terraform_state_source:
        logger.info("Terraform not configured - skipping. See docs to configure.")
        return

    from cartography.intel.common.object_store import ObjectStoreError
    from cartography.intel.common.object_store import read_json_report
    from cartography.intel.common.report_reader_builder import (
        build_report_reader_for_source,
    )
    from cartography.intel.common.report_source import parse_report_source

    source = parse_report_source(config.terraform_state_source)
    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    with build_report_reader_for_source(source, config=config) as reader:
        all_refs = reader.list_reports()
        refs = [
            r
            for r in all_refs
            if r.name.endswith(".tfstate") or r.name.endswith(".json")
        ]

        if not refs:
            logger.warning(
                "Terraform sync configured but no .tfstate/.json files found in %s",
                reader.source_uri,
            )
            return

        logger.info(
            "Processing %d Terraform state file(s) from %s",
            len(refs),
            reader.source_uri,
        )
        failed = 0
        for ref in refs:
            try:
                document = read_json_report(reader, ref)
            except ObjectStoreError as exc:
                logger.error("Failed to read Terraform state %s: %s", ref.uri, exc)
                failed += 1
                continue

            if not isinstance(document, dict):
                logger.warning("Skipping non-object state file: %s", ref.uri)
                continue

            if document.get("version") != 4:
                logger.warning(
                    "Skipping non-v4 Terraform state file %s (version=%s)",
                    ref.uri,
                    document.get("version"),
                )
                continue

            sync_state_file(
                neo4j_session,
                document,
                ref.uri,
                config.update_tag,
                common_job_parameters,
            )

        if failed:
            logger.warning("%d Terraform state file(s) failed to read/parse.", failed)
