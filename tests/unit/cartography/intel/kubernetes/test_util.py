import pytest
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.util import get_gpu_quantity
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import normalize_global_ip_addresses
from cartography.intel.kubernetes.util import normalize_ip_addresses


def _raiser(status: int):
    def list_func(**kwargs):
        raise ApiException(status=status, reason="boom")

    return list_func


def test_k8s_paginate_swallows_errors_by_default():
    # With no raise flags, an API error is logged and swallowed (partial result).
    assert k8s_paginate(_raiser(500)) == []


def test_k8s_paginate_raise_on_error_reraises_any_status():
    # raise_on_error propagates every ApiException so callers cannot mistake a
    # partial result for a complete one.
    with pytest.raises(ApiException):
        k8s_paginate(_raiser(500), raise_on_error=True)
    with pytest.raises(ApiException):
        k8s_paginate(_raiser(403), raise_on_error=True)


def test_k8s_paginate_raise_on_forbidden_is_status_scoped():
    # raise_on_forbidden re-raises only 401/403; other errors stay swallowed.
    with pytest.raises(ApiException):
        k8s_paginate(_raiser(403), raise_on_forbidden=True)
    assert k8s_paginate(_raiser(500), raise_on_forbidden=True) == []


def test_get_gpu_quantity_sums_extended_gpu_resources():
    assert (
        get_gpu_quantity(
            {
                "cpu": "32",
                "nvidia.com/gpu": "8",
                "nvidia.com/mig-1g.10gb": "7",
                "gpu.intel.com/i915": "2",
                "example.com/gpu": "2e0",
                "gpu.intel.com/monitoring": "1",
            }
        )
        == 19
    )
    assert get_gpu_quantity({"example.com/gpu": "not-a-number"}) is None


def test_normalize_global_ip_addresses_filters_non_global_values():
    assert normalize_global_ip_addresses(
        [
            "8.8.8.8",
            "8.8.8.8",
            "2001:4860:4860:0:0:0:0:8888",
            "10.0.0.1",
            "127.0.0.1",
            "fe80::1",
            "not-an-ip",
        ]
    ) == ["2001:4860:4860::8888", "8.8.8.8"]
    assert normalize_ip_addresses(["10.0.0.1", "invalid", "10.0.0.1"]) == ["10.0.0.1"]
