from typing import Optional

from statsd import StatsClient


class ScopedStatsClient:
    """
    A proxy wrapper for StatsD client with scoped metric prefixing capabilities.

    This class provides a hierarchical scoping mechanism for StatsD metrics, allowing
    metric names to be automatically prefixed based on the scope. This enables
    organized metric namespacing and nested scoping for better metric organization.

    Attributes:
        _client: The underlying StatsClient instance (class-level).
        _scope_prefix: The prefix string for this scope level.
        _root: Reference to the root ScopedStatsClient instance.

    Examples:
        Basic scoped client usage:
        >>> root_client = ScopedStatsClient.get_root_client()
        >>> aws_client = root_client.get_stats_client('aws')
        >>> aws_client.incr('ec2.instances')  # Metric: aws.ec2.instances

        Nested scoping:
        >>> root_client = ScopedStatsClient.get_root_client()
        >>> aws_client = root_client.get_stats_client('aws')
        >>> ec2_client = aws_client.get_stats_client('ec2')
        >>> ec2_client.incr('instances')  # Metric: aws.ec2.instances

        Timer usage:
        >>> client = ScopedStatsClient.get_root_client()
        >>> sync_client = client.get_stats_client('sync')
        >>> with sync_client.timer('duration'):
        ...     # Timed operation
        ...     pass  # Metric: sync.duration

    Note:
        The class maintains a single shared StatsClient instance at the root level.
        All scoped instances are proxies that prefix metrics before forwarding
        to the root client. The client must be enabled via set_stats_client()
        before metrics will be sent.
    """

    _client: StatsClient = None

    def __init__(self, prefix: Optional[str], root: "ScopedStatsClient"):
        self._scope_prefix = prefix
        self._root = root

    def get_stats_client(self, scope: str) -> "ScopedStatsClient":
        """
        Create a new scoped StatsD client with additional prefix.

        This method returns a new ScopedStatsClient proxy that automatically
        prefixes all metric names with the provided scope, in addition to any
        existing prefix from the current client.

        Args:
            scope: The scope prefix to add to metric names. Will be appended
                  to any existing prefix with a dot separator.

        Returns:
            A new ScopedStatsClient instance with the combined prefix.
        """
        if not self._scope_prefix:
            prefix = scope
        else:
            prefix = f"{self._scope_prefix}.{scope}"

        scoped_stats_client = ScopedStatsClient(prefix, self._root)
        return scoped_stats_client

    @staticmethod
    def get_root_client() -> "ScopedStatsClient":
        """
        Create and return the root ScopedStatsClient instance.

        This static method creates a root client with no prefix that serves
        as the base for all scoped clients. The root client maintains the
        actual StatsClient instance and serves as the entry point for the
        scoped client hierarchy.

        Returns:
            A root ScopedStatsClient instance with no prefix.
        """
        client = ScopedStatsClient(prefix=None, root=None)  # type: ignore
        client._root = client
        return client

    def is_enabled(self) -> bool:
        """
        Check if the StatsD client is enabled and configured.

        This method determines whether the underlying StatsD client has been
        properly configured and is ready to send metrics. It checks if the
        root client has a valid StatsClient instance set.

        Returns:
            True if the StatsD client is configured and ready to send metrics,
            False if no client has been set or the client is None.
        """
        return self._root._client is not None

    def incr(self, stat: str, count: int = 1, rate: float = 1.0) -> None:
        """
        Increment a StatsD counter metric.

        This method increments a counter metric using the underlying StatsD client.
        The metric name is automatically prefixed with the current scope prefix.

        Args:
            stat: The name of the counter metric to increment.
            count: The amount to increment by. May be negative for decrementing.
                  Defaults to 1.
            rate: The sample rate (0.0 to 1.0). Only sends data this percentage
                 of the time. The StatsD server accounts for the sample rate.
                 Defaults to 1.0 (always send).

        Examples:
            Basic counter increment:
            >>> client = ScopedStatsClient.get_root_client()
            >>> sync_client = client.get_stats_client('sync')
            >>> sync_client.incr('aws.accounts')  # Metric: sync.aws.accounts

            Increment by custom amount:
            >>> client.incr('processed.items', count=5)

            Using sample rate:
            >>> client.incr('high.volume.metric', rate=0.1)  # Sample 10%
        """
        if self.is_enabled():
            if self._scope_prefix:
                stat = f"{self._scope_prefix}.{stat}"
            self._root._client.incr(stat, count, rate)

    def timer(self, stat: str, rate: float = 1.0):
        """
        Create a StatsD timer context manager for measuring execution time.

        This method returns a timer object that can be used as a context manager
        to measure and report execution time. The metric name is automatically
        prefixed with the current scope prefix.

        Args:
            stat: The name of the timer metric to report.
            rate: The sample rate (0.0 to 1.0). Only sends data this percentage
                 of the time. The StatsD server accounts for the sample rate.
                 Defaults to 1.0 (always send).

        Returns:
            A timer context manager object, or None if the client is not enabled.

        Examples:
            Using as context manager:
            >>> client = ScopedStatsClient.get_root_client()
            >>> sync_client = client.get_stats_client('sync')
            >>> with sync_client.timer('aws.duration'):
            ...     # Timed operation here
            ...     time.sleep(1)  # Metric: sync.aws.duration

            Manual timer usage:
            >>> timer = client.timer('operation.time')
            >>> if timer:
            ...     timer.start()
            ...     # Do work
            ...     timer.stop()  # Sends timing metric
        """
        if self.is_enabled():
            if self._scope_prefix:
                stat = f"{self._scope_prefix}.{stat}"
            return self._root._client.timer(stat, rate)
        return None

    def gauge(self, stat: str, value: int, rate: float = 1.0, delta: bool = False):
        """
        Report a StatsD gauge metric value.

        This method reports a gauge value using the underlying StatsD client.
        Gauges represent a snapshot value that can go up or down. The metric
        name is automatically prefixed with the current scope prefix.

        Args:
            stat: The name of the gauge metric to report.
            value: The gauge value to report.
            rate: The sample rate (0.0 to 1.0). Only sends data this percentage
                 of the time. Defaults to 1.0 (always send).
            delta: If True, the value is added to the current gauge value
                  instead of replacing it. Defaults to False (set absolute value).

        Returns:
            The result from the underlying StatsD client, or None if not enabled.

        Examples:
            Setting absolute gauge value:
            >>> client = ScopedStatsClient.get_root_client()
            >>> aws_client = client.get_stats_client('aws')
            >>> aws_client.gauge('active.connections', 42)  # Metric: aws.active.connections

            Delta gauge update:
            >>> aws_client.gauge('queue.size', 5, delta=True)  # Add 5 to current value

            Using sample rate:
            >>> aws_client.gauge('memory.usage', 1024, rate=0.5)  # Sample 50%

        Note:
            If the client is not enabled, returns None. When delta=True, the
            value is added to the existing gauge value rather than replacing it.
        """
        if self.is_enabled():
            if self._scope_prefix:
                stat = f"{self._scope_prefix}.{stat}"
            return self._root._client.gauge(stat, value, rate=rate, delta=delta)
        return None

    def set_stats_client(self, stats_client: StatsClient) -> None:
        """
        Set the underlying StatsD client for this scoped client hierarchy.

        This method configures the actual StatsClient instance that will be used
        by this scoped client and all other scoped clients in the hierarchy.
        The client is set at the root level, making it available to all scoped
        instances derived from this hierarchy.
        """
        self._root._client = stats_client


# Global _scoped_stats_client
# Will be set when cartography.config.statsd_enabled is True
_scoped_stats_client: ScopedStatsClient = ScopedStatsClient.get_root_client()


def set_stats_client(stats_client: StatsClient) -> None:
    """
    Configure the global StatsD client for cartography metrics.

    This function sets the underlying StatsClient instance that will be used
    by all ScopedStatsClient instances for sending metrics to the StatsD server.
    This should be called once during application initialization when StatsD
    is enabled.

    Args:
        stats_client: A configured StatsClient instance that will handle
                     the actual communication with the StatsD server.

    Note:
        This function modifies the global _scoped_stats_client instance.
        Once set, all subsequent metric operations through ScopedStatsClient
        instances will use this client to send metrics to StatsD.
    """
    global _scoped_stats_client  # noqa: F824
    _scoped_stats_client.set_stats_client(stats_client)


def get_stats_client(prefix: str) -> ScopedStatsClient:
    """
    Get a scoped StatsD client with the specified prefix.

    This function returns a ScopedStatsClient instance that automatically
    prefixes all metrics with the provided prefix string. It uses the global
    _scoped_stats_client as the root client.
    """
    return _scoped_stats_client.get_stats_client(prefix)
