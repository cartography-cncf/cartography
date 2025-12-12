from unittest.mock import MagicMock
from unittest.mock import patch

import neo4j.exceptions
import pytest

from cartography.client.core.tx import _entity_not_found_backoff_handler
from cartography.client.core.tx import _is_retryable_client_error
from cartography.client.core.tx import _run_index_query_with_retry
from cartography.client.core.tx import _run_with_retry
from cartography.client.core.tx import execute_write_with_retry


def _create_client_error(
    code: str, message: str = "Test error"
) -> neo4j.exceptions.ClientError:
    """Helper to create a ClientError with a specific code."""
    exc = neo4j.exceptions.ClientError(message)
    # Set the code attribute (this is how Neo4j driver sets it internally)
    object.__setattr__(exc, "_neo4j_code", code)
    return exc


# Tests for _is_retryable_client_error


def test_entity_not_found_is_retryable():
    """EntityNotFound errors should be retryable."""
    exc = _create_client_error("Neo.ClientError.Statement.EntityNotFound")
    assert _is_retryable_client_error(exc) is True


def test_other_client_errors_not_retryable():
    """Other ClientErrors should NOT be retryable."""
    exc = _create_client_error("Neo.ClientError.Statement.SyntaxError")
    assert _is_retryable_client_error(exc) is False


def test_non_client_error_not_retryable():
    """Non-ClientError exceptions should NOT be retryable."""
    exc = ValueError("some error")
    assert _is_retryable_client_error(exc) is False


# Tests for _entity_not_found_backoff_handler


@patch("cartography.client.core.tx.logger")
def test_logs_entity_not_found_with_valid_wait(mock_logger):
    """Should log warning for EntityNotFound with valid wait time."""
    exc = _create_client_error("Neo.ClientError.Statement.EntityNotFound")
    details = {
        "exception": exc,
        "tries": 2,
        "wait": 1.5,
        "target": "test_function",
    }
    _entity_not_found_backoff_handler(details)

    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0][0]
    assert "EntityNotFound retry 2/5" in call_args
    assert "1.5" in call_args


@patch("cartography.client.core.tx.logger")
def test_logs_entity_not_found_first_encounter(mock_logger):
    """Should log clear message on first EntityNotFound encounter."""
    exc = _create_client_error("Neo.ClientError.Statement.EntityNotFound")
    details = {
        "exception": exc,
        "tries": 1,
        "wait": 1.0,
        "target": "test_function",
    }
    _entity_not_found_backoff_handler(details)

    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0][0]
    assert "Encountered EntityNotFound error (attempt 1/5)" in call_args
    assert "This is expected during concurrent write operations" in call_args


@patch("cartography.client.core.tx.logger")
def test_logs_entity_not_found_with_none_wait(mock_logger):
    """Should handle None wait gracefully and log 'unknown'."""
    exc = _create_client_error("Neo.ClientError.Statement.EntityNotFound")
    details = {
        "exception": exc,
        "tries": 2,
        "wait": None,
        "target": "test_function",
    }
    _entity_not_found_backoff_handler(details)

    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0][0]
    assert "unknown" in call_args


@patch("cartography.client.core.tx.backoff_handler")
@patch("cartography.client.core.tx.logger")
def test_falls_back_to_standard_handler_for_other_errors(
    mock_logger, mock_backoff_handler
):
    """Should use standard backoff handler for non-EntityNotFound errors."""
    exc = ValueError("some error")
    details = {
        "exception": exc,
        "tries": 2,
        "wait": 1.5,
        "target": "test_function",
    }
    _entity_not_found_backoff_handler(details)

    # Should not log EntityNotFound warning
    mock_logger.warning.assert_not_called()
    # Should call standard backoff handler
    mock_backoff_handler.assert_called_once_with(details)


# Tests for _run_with_retry


def test_succeeds_on_first_try():
    """Should return result immediately if operation succeeds."""
    operation = MagicMock(return_value="success")
    result = _run_with_retry(operation, "test_target")

    assert result == "success"
    operation.assert_called_once()


@patch("cartography.client.core.tx.logger")
@patch("cartography.client.core.tx.time.sleep")
def test_retries_entity_not_found_error(mock_sleep, mock_logger):
    """Should retry EntityNotFound errors up to MAX_RETRIES times."""
    operation = MagicMock()
    # Fail twice with EntityNotFound, then succeed
    operation.side_effect = [
        _create_client_error("Neo.ClientError.Statement.EntityNotFound"),
        _create_client_error("Neo.ClientError.Statement.EntityNotFound"),
        "success",
    ]

    result = _run_with_retry(operation, "test_target")

    assert result == "success"
    assert operation.call_count == 3
    assert mock_sleep.call_count == 2

    # Should log success after recovery
    success_logs = [
        call
        for call in mock_logger.info.call_args_list
        if "Successfully recovered from EntityNotFound" in str(call)
    ]
    assert len(success_logs) == 1


def test_raises_non_retryable_client_error_immediately():
    """Should raise non-retryable ClientErrors immediately without retry."""
    operation = MagicMock()
    operation.side_effect = _create_client_error(
        "Neo.ClientError.Statement.SyntaxError"
    )

    with pytest.raises(neo4j.exceptions.ClientError):
        _run_with_retry(operation, "test_target")

    # Should only be called once (no retries)
    operation.assert_called_once()


@patch("cartography.client.core.tx.time.sleep")
def test_raises_after_max_entity_not_found_retries(mock_sleep):
    """Should raise EntityNotFound error after MAX_RETRIES attempts."""
    operation = MagicMock()
    # Fail all attempts with EntityNotFound
    operation.side_effect = _create_client_error(
        "Neo.ClientError.Statement.EntityNotFound"
    )

    with pytest.raises(neo4j.exceptions.ClientError):
        _run_with_retry(operation, "test_target")

    # Should try MAX_ENTITY_NOT_FOUND_RETRIES (5) times
    assert operation.call_count == 5


@patch("cartography.client.core.tx.time.sleep")
def test_retries_network_errors(mock_sleep):
    """Should retry network errors (ServiceUnavailable, ConnectionResetError, etc)."""
    operation = MagicMock()
    # Fail once with network error, then succeed
    operation.side_effect = [
        neo4j.exceptions.ServiceUnavailable("Connection lost"),
        "success",
    ]

    result = _run_with_retry(operation, "test_target")

    assert result == "success"
    assert operation.call_count == 2
    mock_sleep.assert_called_once()


@patch("cartography.client.core.tx.time.sleep")
@patch("cartography.client.core.tx.logger")
def test_handles_none_wait_time_gracefully(mock_logger, mock_sleep):
    """Should handle None wait time from backoff generator gracefully."""
    operation = MagicMock()
    operation.side_effect = [
        _create_client_error("Neo.ClientError.Statement.EntityNotFound"),
        "success",
    ]

    # Mock backoff.expo() to return None (edge case)
    with patch("cartography.client.core.tx.backoff.expo") as mock_expo:
        mock_expo.return_value = iter([None])
        result = _run_with_retry(operation, "test_target")

    assert result == "success"
    # Should log error about None wait time
    error_logs = [
        call
        for call in mock_logger.error.call_args_list
        if "Unexpected: backoff generator returned None" in str(call)
    ]
    assert len(error_logs) == 1
    # Should still sleep (with fallback 1.0 second)
    mock_sleep.assert_called_once_with(1.0)


# Tests for execute_write_with_retry


@patch("cartography.client.core.tx._run_with_retry")
def test_execute_write_with_retry_calls_run_with_retry(mock_run_with_retry):
    """Should call _run_with_retry with correct arguments."""
    mock_session = MagicMock()
    mock_tx_func = MagicMock()
    mock_run_with_retry.return_value = "result"

    result = execute_write_with_retry(
        mock_session,
        mock_tx_func,
        "arg1",
        "arg2",
        kwarg1="value1",
    )

    assert result == "result"
    mock_run_with_retry.assert_called_once()
    # Verify the operation function was created correctly
    operation_func = mock_run_with_retry.call_args[0][0]

    # Execute the operation to verify it calls execute_write correctly
    operation_func()
    mock_session.execute_write.assert_called_once_with(
        mock_tx_func,
        "arg1",
        "arg2",
        kwarg1="value1",
    )


# Integration tests simulating real-world concurrent write scenarios


@patch("cartography.client.core.tx.time.sleep")
def test_simulates_concurrent_gcp_firewall_write_conflict(mock_sleep):
    """
    Simulates the scenario from the bug report where GCP firewall ingestion
    encounters EntityNotFound due to concurrent writes.

    This happens when:
    1. Thread A references a VPC node
    2. Thread B deletes that VPC node
    3. Thread A tries to use the VPC reference and gets EntityNotFound

    See: https://github.com/neo4j/neo4j/issues/6823
    """
    mock_session = MagicMock()

    # Simulate the transaction function that failed in production
    def _load_gcp_ingress_firewalls_tx(tx, fw_list, update_tag):
        # Simulate tx.run() that encounters EntityNotFound on first try
        # due to concurrent deletion of a VPC node
        if not hasattr(tx, "_attempt_count"):
            tx._attempt_count = 0
        tx._attempt_count += 1

        if tx._attempt_count == 1:
            # First attempt: EntityNotFound (concurrent thread deleted VPC)
            raise _create_client_error(
                "Neo.ClientError.Statement.EntityNotFound",
                "Unable to load NODE 4:f6d9b629-13b2-4228-a20f-26750e73c219:352103.",
            )
        else:
            # Second attempt: success (VPC recreated or transaction retried)
            return "success"

    # Setup mock transaction
    mock_tx = MagicMock()
    mock_tx._attempt_count = 0
    mock_session.execute_write.side_effect = lambda func, *args, **kwargs: func(
        mock_tx, *args, **kwargs
    )

    # Execute with retry
    result = execute_write_with_retry(
        mock_session,
        _load_gcp_ingress_firewalls_tx,
        [{"id": "fw-123"}],
        12345,
    )

    # Should succeed after retry
    assert result == "success"
    assert mock_session.execute_write.call_count == 2
    mock_sleep.assert_called_once()  # Should have backed off once


@patch("cartography.client.core.tx.time.sleep")
def test_retries_with_exponential_backoff(mock_sleep):
    """Verify that retries use exponential backoff delays."""
    mock_session = MagicMock()

    call_count = 0

    def failing_tx(tx):
        nonlocal call_count
        call_count += 1
        if call_count < 4:
            raise _create_client_error("Neo.ClientError.Statement.EntityNotFound")
        return "success"

    mock_session.execute_write.side_effect = failing_tx

    result = execute_write_with_retry(mock_session, lambda tx: failing_tx(tx))

    assert result == "success"
    # Should have slept 3 times (between 4 attempts)
    assert mock_sleep.call_count == 3

    # Verify backoff is happening (all sleeps should be > 0)
    sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
    for sleep_time in sleep_calls:
        assert sleep_time > 0, "All backoff delays should be positive"

    # Verify that the last backoff is longer than the first (exponential growth)
    assert (
        sleep_calls[-1] > sleep_calls[0]
    ), f"Expected exponential backoff with last > first, but got {sleep_calls}"


@patch("cartography.client.core.tx.time.sleep")
@patch("cartography.client.core.tx.logger")
def test_network_errors_with_none_wait(mock_logger, mock_sleep):
    """Should handle None wait time for network errors gracefully."""
    operation = MagicMock()
    operation.side_effect = [
        neo4j.exceptions.ServiceUnavailable("Connection lost"),
        "success",
    ]

    # Mock backoff.expo() to return None for network errors (edge case)
    with patch("cartography.client.core.tx.backoff.expo") as mock_expo:
        # First generator for network_wait, second for entity_wait
        mock_expo.return_value = iter([None])
        result = _run_with_retry(operation, "test_target")

    assert result == "success"
    # Should log error about None wait time
    error_logs = [
        call
        for call in mock_logger.error.call_args_list
        if "Unexpected: backoff generator returned None" in str(call)
    ]
    assert len(error_logs) == 1
    # Should still sleep (with fallback 1.0 second)
    mock_sleep.assert_called_once_with(1.0)


def test_client_error_with_none_code():
    """Should handle ClientError with None code gracefully."""
    # Create a ClientError without setting the code (simulates locally-created error)
    exc = neo4j.exceptions.ClientError("Test error")
    # Don't set _neo4j_code, so it defaults to None

    # Should return False (not retryable)
    assert _is_retryable_client_error(exc) is False


@patch("cartography.client.core.tx.time.sleep")
def test_network_errors_max_retries(mock_sleep):
    """Should raise network error after MAX_RETRIES attempts."""
    operation = MagicMock()
    # Fail all attempts with network error
    operation.side_effect = neo4j.exceptions.ServiceUnavailable("Connection lost")

    with pytest.raises(neo4j.exceptions.ServiceUnavailable):
        _run_with_retry(operation, "test_target")

    # Should try MAX_NETWORK_RETRIES (5) times
    assert operation.call_count == 5


@patch("cartography.client.core.tx.logger")
@patch("cartography.client.core.tx.time.sleep")
def test_network_error_recovery_logging(mock_sleep, mock_logger):
    """Should log successful recovery from network errors."""
    operation = MagicMock()
    # Fail twice with network error, then succeed
    operation.side_effect = [
        neo4j.exceptions.ServiceUnavailable("Connection lost"),
        neo4j.exceptions.ServiceUnavailable("Connection lost"),
        "success",
    ]

    result = _run_with_retry(operation, "test_target")

    assert result == "success"
    assert operation.call_count == 3
    assert mock_sleep.call_count == 2

    # Should log success after recovery from network errors
    success_logs = [
        call
        for call in mock_logger.info.call_args_list
        if "Successfully recovered from network error" in str(call)
    ]
    assert len(success_logs) == 1


# Tests for _run_index_query_with_retry


@patch("cartography.client.core.tx.logger")
def test_run_index_query_ignores_equivalent_schema_rule_already_exists(mock_logger):
    """
    Should ignore EquivalentSchemaRuleAlreadyExists errors during parallel sync.

    This error occurs when multiple parallel sync operations attempt to create
    the same index simultaneously. Even though we use CREATE INDEX IF NOT EXISTS,
    Neo4j has a race condition where concurrent index creation can fail if another
    session creates the index between the existence check and the actual creation.
    """
    mock_session = MagicMock()
    mock_session.run.side_effect = _create_client_error(
        "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists",
        "An equivalent index already exists, 'Index( id=619, name='index_164cdc93', "
        "type='RANGE', schema=(:GCPPolicyBinding {id}), indexProvider='range-1.0' )'.",
    )

    # Should NOT raise an exception
    _run_index_query_with_retry(mock_session, "CREATE INDEX IF NOT EXISTS ...")

    # Should log at debug level
    mock_logger.debug.assert_called_once()
    call_args = mock_logger.debug.call_args[0][0]
    assert "Index already exists" in call_args
    assert "parallel sync" in call_args


def test_run_index_query_raises_other_client_errors():
    """Should raise other ClientErrors that are not EquivalentSchemaRuleAlreadyExists."""
    mock_session = MagicMock()
    mock_session.run.side_effect = _create_client_error(
        "Neo.ClientError.Statement.SyntaxError",
        "Invalid syntax",
    )

    with pytest.raises(neo4j.exceptions.ClientError) as exc_info:
        _run_index_query_with_retry(mock_session, "CREATE INDEX IF NOT EXISTS ...")

    assert exc_info.value.code == "Neo.ClientError.Statement.SyntaxError"


def test_run_index_query_succeeds_normally():
    """Should execute index query successfully when no error occurs."""
    mock_session = MagicMock()
    mock_session.run.return_value = MagicMock()

    # Should NOT raise an exception
    _run_index_query_with_retry(mock_session, "CREATE INDEX IF NOT EXISTS ...")

    mock_session.run.assert_called_once_with("CREATE INDEX IF NOT EXISTS ...")
