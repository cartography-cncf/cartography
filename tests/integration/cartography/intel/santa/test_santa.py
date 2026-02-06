from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.ontology.devices
import cartography.intel.ontology.users
import cartography.intel.santa
from cartography.config import Config
from tests.data.santa.events import EVENT_ROWS
from tests.data.santa.events import EVENT_ROWS_SECOND_RUN
from tests.data.santa.machines import MACHINE_SNAPSHOTS
from tests.data.santa.machines import MACHINE_SNAPSHOTS_SECOND_RUN
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _build_config(update_tag: int) -> Config:
    return Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=update_tag,
        santa_base_url="https://zentral.example.com",
        santa_token="test-token",
        santa_source_name="Santa",
        santa_event_lookback_days=3650,
        santa_request_timeout=30,
    )


def _run_santa_sync(
    neo4j_session,
    machine_snapshots: list[dict],
    event_rows: list[dict],
    update_tag: int,
) -> None:
    client = Mock()
    client.export_machine_snapshots.return_value = machine_snapshots
    client.export_santa_events.return_value = event_rows

    with patch.object(
        cartography.intel.santa, "ZentralSantaClient", return_value=client
    ):
        cartography.intel.santa.start_santa_ingestion(
            neo4j_session,
            _build_config(update_tag),
        )


def test_santa_sync_loads_nodes_and_relationships(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _run_santa_sync(neo4j_session, MACHINE_SNAPSHOTS, EVENT_ROWS, TEST_UPDATE_TAG)

    assert check_nodes(neo4j_session, "SantaMachine", ["id", "hostname"]) == {
        ("C02ABC123", "donut-mac"),
        ("C02DEF456", "lisa-mac"),
    }

    assert check_nodes(neo4j_session, "SantaUser", ["id", "email"]) == {
        ("homer@simpson.corp", "homer@simpson.corp"),
        ("lisa@simpson.corp", "lisa@simpson.corp"),
    }

    assert check_nodes(
        neo4j_session,
        "SantaObservedApplication",
        ["id", "name"],
    ) == {
        ("com.apple.terminal", "Terminal"),
        ("com.google.chrome", "Google Chrome"),
    }

    assert check_nodes(
        neo4j_session,
        "SantaObservedApplicationVersion",
        ["id", "version"],
    ) == {
        ("com.apple.terminal:2.14", "2.14"),
        ("com.google.chrome:124.0", "124.0"),
    }

    assert check_rels(
        neo4j_session,
        "SantaMachine",
        "id",
        "SantaUser",
        "id",
        "PRIMARY_USER",
        rel_direction_right=True,
    ) == {
        ("C02ABC123", "homer@simpson.corp"),
        ("C02DEF456", "lisa@simpson.corp"),
    }

    assert check_rels(
        neo4j_session,
        "SantaMachine",
        "id",
        "SantaObservedApplicationVersion",
        "id",
        "OBSERVED_EXECUTION",
        rel_direction_right=True,
    ) == {
        ("C02ABC123", "com.apple.terminal:2.14"),
        ("C02DEF456", "com.google.chrome:124.0"),
    }

    assert check_rels(
        neo4j_session,
        "SantaObservedApplication",
        "id",
        "SantaObservedApplicationVersion",
        "id",
        "VERSION",
        rel_direction_right=True,
    ) == {
        ("com.apple.terminal", "com.apple.terminal:2.14"),
        ("com.google.chrome", "com.google.chrome:124.0"),
    }

    assert check_rels(
        neo4j_session,
        "SantaUser",
        "id",
        "SantaObservedApplicationVersion",
        "id",
        "EXECUTED",
        rel_direction_right=True,
    ) == {
        ("homer@simpson.corp", "com.apple.terminal:2.14"),
        ("lisa@simpson.corp", "com.google.chrome:124.0"),
    }


def test_santa_sync_cleanup_removes_stale_records(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")

    client = Mock()
    client.export_machine_snapshots.side_effect = [
        MACHINE_SNAPSHOTS,
        MACHINE_SNAPSHOTS_SECOND_RUN,
    ]
    client.export_santa_events.side_effect = [
        EVENT_ROWS,
        EVENT_ROWS_SECOND_RUN,
    ]

    with patch.object(
        cartography.intel.santa, "ZentralSantaClient", return_value=client
    ):
        cartography.intel.santa.start_santa_ingestion(
            neo4j_session,
            _build_config(TEST_UPDATE_TAG),
        )
        cartography.intel.santa.start_santa_ingestion(
            neo4j_session,
            _build_config(TEST_UPDATE_TAG + 1),
        )

    assert check_nodes(neo4j_session, "SantaMachine", ["id"]) == {("C02DEF456",)}
    assert check_nodes(neo4j_session, "SantaUser", ["id"]) == {("lisa@simpson.corp",)}
    assert check_nodes(
        neo4j_session,
        "SantaObservedApplicationVersion",
        ["id"],
    ) == {("com.google.chrome:125.1",)}


def test_santa_ontology_links_users_and_devices(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _run_santa_sync(neo4j_session, MACHINE_SNAPSHOTS, EVENT_ROWS, TEST_UPDATE_TAG)

    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG}

    cartography.intel.ontology.users.sync(
        neo4j_session,
        ["santa"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    cartography.intel.ontology.devices.sync(
        neo4j_session,
        ["santa"],
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(neo4j_session, "Device", ["hostname"]) == {
        ("donut-mac",),
        ("lisa-mac",),
    }

    assert check_rels(
        neo4j_session,
        "Device",
        "hostname",
        "SantaMachine",
        "hostname",
        "OBSERVED_AS",
        rel_direction_right=True,
    ) == {
        ("donut-mac", "donut-mac"),
        ("lisa-mac", "lisa-mac"),
    }

    assert check_rels(
        neo4j_session,
        "User",
        "email",
        "Device",
        "hostname",
        "OWNS",
        rel_direction_right=True,
    ) == {
        ("homer@simpson.corp", "donut-mac"),
        ("lisa@simpson.corp", "lisa-mac"),
    }
