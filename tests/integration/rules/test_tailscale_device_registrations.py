from cartography.client.core.tx import read_list_of_dicts_tx
from cartography.rules.data.rules.device_security_posture_gaps import (
    _device_update_gaps,
)
from cartography.rules.data.rules.device_security_posture_gaps import (
    _tailscale_device_posture_gaps,
)
from cartography.rules.data.rules.tailscale_security_configuration_gaps import (
    _tailscale_device_key_expiry_disabled,
)


def _rows(neo4j_session, fact):
    return neo4j_session.execute_read(read_list_of_dicts_tx, fact.cypher_query)


def test_a_reregistered_hostname_reports_only_its_current_registration(
    neo4j_session,
) -> None:
    """
    A host that re-registers keeps its old registration until it expires, so two
    live devices share one hostname. The hostname-keyed facts must emit one row for
    it, taken from the most recently seen registration: two rows collide on the
    finding identity, and the stale registration must not raise findings the
    machine no longer has.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (tailnet:TailscaleTailnet {id: 'example.com'})
        CREATE (tailnet)-[:RESOURCE]->(:TailscaleDevice {
            id: 'old-registration', hostname: 'gateway',
            last_seen: '2026-01-01T00:00:00Z',
            key_expiry_disabled: true, update_available: true,
            posture_node_ts_state_encrypted: false
        })
        CREATE (tailnet)-[:RESOURCE]->(:TailscaleDevice {
            id: 'new-registration', hostname: 'gateway',
            last_seen: '2026-01-02T00:00:00Z',
            key_expiry_disabled: true, update_available: false,
            posture_node_ts_state_encrypted: true
        })
        CREATE (tailnet)-[:RESOURCE]->(:TailscaleDevice {
            id: 'laptop-registration', hostname: 'laptop',
            last_seen: '2026-01-02T00:00:00Z',
            update_available: true
        })
        """
    )

    key_expiry = _rows(neo4j_session, _tailscale_device_key_expiry_disabled)
    assert [(row["asset_name"], row["asset_id"]) for row in key_expiry] == [
        ("gateway", "new-registration"),
    ]

    updates = _rows(neo4j_session, _device_update_gaps)
    assert [(row["device_name"], row["device_id"]) for row in updates] == [
        ("laptop", "laptop-registration"),
    ]

    assert _rows(neo4j_session, _tailscale_device_posture_gaps) == []
