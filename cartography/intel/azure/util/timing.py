import threading
from typing import Any
from typing import Dict
from typing import Optional

from azure.core.pipeline.policies import SansIOHTTPPolicy

_local = threading.local()


class ServiceTimingContext:
    """
    Thread-local stats collector for a single Azure service call.

    Mount it as a context manager around any RESOURCE_FUNCTIONS call so that
    AzureTimingPolicy (injected into each SDK client) can record HTTP-level
    metrics without modifying the resource functions themselves.

    Fields
    ------
    service_name   : name of the cartography service being synced
    request_count  : total HTTP requests issued (proxy for pagination depth)
    throttle_count : number of 429 responses received
    retry_count    : number of responses that carried Retry-After / x-ms-retry-after-ms
    """

    __slots__ = ('service_name', 'request_count', 'throttle_count', 'retry_count')

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name
        self.request_count: int = 0
        self.throttle_count: int = 0
        self.retry_count: int = 0

    def __enter__(self) -> 'ServiceTimingContext':
        _local.ctx = self
        return self

    def __exit__(self, *args: Any) -> None:
        _local.ctx = None

    def to_dict(self) -> Dict[str, int]:
        return {
            'request_count': self.request_count,
            'throttle_count': self.throttle_count,
            'retry_count': self.retry_count,
        }


def get_current_context() -> Optional[ServiceTimingContext]:
    """Return the ServiceTimingContext active on the current thread, or None."""
    return getattr(_local, 'ctx', None)


class AzureTimingPolicy(SansIOHTTPPolicy):
    """
    Azure SDK HTTP pipeline policy that records per-request stats into the
    thread-local ServiceTimingContext.

    Stateless — safe to share as a singleton across clients and threads.
    Reading is gated on get_current_context(), so calls outside a
    ServiceTimingContext are silently ignored.

    Inject via per_call_policies when creating any *ManagementClient:

        from cartography.intel.azure.util.timing import get_timing_policy
        client = ComputeManagementClient(
            credentials, subscription_id,
            per_call_policies=[get_timing_policy()],
        )
    """

    def on_request(self, request: Any) -> None:
        ctx = get_current_context()
        if ctx is not None:
            ctx.request_count += 1

    def on_response(self, request: Any, response: Any) -> None:
        ctx = get_current_context()
        if ctx is None:
            return
        http_resp = response.http_response
        if http_resp.status_code == 429:
            ctx.throttle_count += 1
        if http_resp.headers.get('Retry-After') or http_resp.headers.get('x-ms-retry-after-ms'):
            ctx.retry_count += 1


# Singleton — stateless, thread-safe via thread-local reads.
_timing_policy = AzureTimingPolicy()


def get_timing_policy() -> AzureTimingPolicy:
    """Return the shared AzureTimingPolicy singleton for SDK client injection."""
    return _timing_policy
