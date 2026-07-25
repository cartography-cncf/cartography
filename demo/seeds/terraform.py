import json
from unittest.mock import mock_open
from unittest.mock import patch

from demo.seeds.base import Seed
from tests.data.terraform.state import SAMPLE_STATE_FILE


class TerraformSeed(Seed):
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=json.dumps(SAMPLE_STATE_FILE).encode("utf-8"),
    )
    @patch("cartography.intel.common.object_store.LocalReportReader.list_reports")
    def seed(self, mock_list, mock_file) -> None:
        from cartography.intel.terraform import start_terraform_ingestion

        mock_list.return_value = []
        from cartography.config import Config

        config = Config(
            neo4j_uri="bolt://localhost:7687",
            update_tag=self.update_tag,
            terraform_state_source="/tmp/states/",
        )
        start_terraform_ingestion(self.neo4j_session, config)
