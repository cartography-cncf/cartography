from typing import Optional

from statsd import StatsClient


class ScopedStatsClient:
    """
    A Proxy object for an underlying statsd client.
    Adds a new call, get_scoped_stats_client(scope), which returns a new proxy to the same
    client which will prefix all calls to underlying methods with the scoped prefix:
    new_client = client.get_scoped_stats_client('a')
    new_client.incr('b') # Metric name = a.b
    This can be nested:
    newer_client = new_client.get_scoped_stats_client('subsystem')
    newer_client.incr('bad') # Metric name = a.subsystem.bad
    """

    _client: StatsClient = None

    def __init__(self, prefix: Optional[str], root: "ScopedStatsClient"):
        self._scope_prefix = prefix
        self._root = root

    def get_stats_client(self, scope: str) -> "ScopedStatsClient":
        """
        This method returns a new proxy to the same client
        which will prefix all calls to underlying methods with the scoped prefix
        """
        if not self._scope_prefix:
            prefix = scope
        else:
            prefix = f"{self._scope_prefix}.{scope}"

        scoped_stats_client = ScopedStatsClient(prefix, self._root)
        return scoped_stats_client

    @staticmethod
    def get_root_client() -> "ScopedStatsClient":
        client = ScopedStatsClient(prefix=None, root=None)  # type: ignore
        client._root = client
        return client

    def is_enabled(self) -> bool:
        return self._root._client is not None

    def incr(self, stat: str, count: int = 1, rate: float = 1.0) -> None:
        """
        This method uses statsd to increment a counter.
        :param stat: the name of the counter metric stat (string) to increment
        :param count: the amount (integer) to increment by. May be negative
        :param rate: a sample rate, a float between 0 and 1. Will only send data this percentage of the time.
                             The statsd server will take the sample rate into account for counters
        """
        if self.is_enabled():
            if self._scope_prefix:
                stat = f"{self._scope_prefix}.{stat}"
            self._root._client.incr(stat, count, rate)

    def timer(self, stat: str, rate: float = 1.0):
        """
        This method uses statsd to retrieve a timer.
        When Timer.stop() is called, a timing stat will automatically be sent to statsd
        :param stat: the name of the timer metric stat (string) to report
        :param rate: a sample rate, a float between 0 and 1. Will only send data this percentage of the time.
                             The statsd server will take the sample rate into account for counters
        """
        if self.is_enabled():
            if self._scope_prefix:
                stat = f"{self._scope_prefix}.{stat}"
            return self._root._client.timer(stat, rate)
        return None

    def gauge(self, stat: str, value: int, rate: float = 1.0, delta: bool = False):
        """
        This method uses statsd to report a gauge value.
        :param stat: the name of the gauge to report.
        :param value: the value to report.
        :param rate: a sample rate, a float between 0 and 1. Will only send data this percentage of the time.
        :param delta: if True, the current reported value will be updated instead of being set by the new value.
        """
        if self.is_enabled():
            if self._scope_prefix:
                stat = f"{self._scope_prefix}.{stat}"
            return self._root._client.gauge(stat, value, rate=rate, delta=delta)
        return None

    def set_stats_client(self, stats_client: StatsClient) -> None:
        self._root._client = stats_client


# Global _scoped_stats_client
# Will be set when cartography.config.statsd_enabled is True
_scoped_stats_client: ScopedStatsClient = ScopedStatsClient.get_root_client()


def set_stats_client(stats_client: StatsClient) -> None:
    """
    This is used to set the module level stats client configured to talk with a statsd host
    """
    global _scoped_stats_client  # noqa: F824
    _scoped_stats_client.set_stats_client(stats_client)


def get_stats_client(prefix: str) -> ScopedStatsClient:
    """
    Returns a ScopedStatsClient object, which is a simple wrapper over statsd.client.Statsclient
    that allows one to scope down the metric as needed
    """
    return _scoped_stats_client.get_stats_client(prefix)
