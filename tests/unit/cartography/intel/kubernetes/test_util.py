from types import SimpleNamespace

import pytest
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes import ingress
from cartography.intel.kubernetes import nodes
from cartography.intel.kubernetes import services
from cartography.intel.kubernetes.util import get_gpu_quantity
from cartography.intel.kubernetes.util import is_skippable_list_error
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import k8s_paginate_pages


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


def _paged_list_func(pages: list[list[str]], calls: list[str | None]):
    def list_pod_for_all_namespaces(limit, _continue=None):
        calls.append(_continue)
        index = int(_continue) if _continue else 0
        next_token = str(index + 1) if index + 1 < len(pages) else None
        return SimpleNamespace(
            items=pages[index],
            metadata=SimpleNamespace(_continue=next_token),
        )

    return list_pod_for_all_namespaces


def test_k8s_paginate_pages_fetches_lazily():
    calls: list[str | None] = []
    pages = k8s_paginate_pages(_paged_list_func([["a", "b"], ["c"]], calls))

    assert calls == []
    assert next(pages) == ["a", "b"]
    # The next page is not requested until the caller is done with this one.
    assert calls == [None]
    assert next(pages) == ["c"]
    assert calls == [None, "1"]
    assert list(pages) == []


def test_k8s_paginate_flattens_pages():
    calls: list[str | None] = []
    assert k8s_paginate(_paged_list_func([["a", "b"], ["c"]], calls)) == [
        "a",
        "b",
        "c",
    ]


def test_k8s_paginate_pages_error_semantics_match_k8s_paginate():
    assert list(k8s_paginate_pages(_raiser(500))) == []
    with pytest.raises(ApiException):
        list(k8s_paginate_pages(_raiser(500), raise_on_error=True))
    with pytest.raises(ApiException):
        list(k8s_paginate_pages(_raiser(403), raise_on_forbidden=True))


@pytest.mark.parametrize(
    "status,skippable",
    [
        (401, True),
        (403, True),
        (None, True),
        # The continue token of a paginated list expired.
        (410, True),
        (429, True),
        (503, True),
        (400, False),
        (404, False),
    ],
)
def test_only_permission_and_transient_list_errors_are_skippable(status, skippable):
    # Act and assert
    assert is_skippable_list_error(ApiException(status=status)) is skippable


@pytest.mark.parametrize(
    "sync",
    [
        lambda client: services.sync_services(None, client, [], 1, {}),
        lambda client: ingress.sync_ingress(None, client, 1, {}),
        lambda client: nodes.sync_nodes(None, client, 1, {}),
    ],
    ids=["services", "ingress", "nodes"],
)
def test_sync_fails_on_a_list_error_it_cannot_skip(sync):
    # Arrange
    client = SimpleNamespace(
        name="example",
        core=SimpleNamespace(
            list_service_for_all_namespaces=_raiser(404), list_node=_raiser(404)
        ),
        networking=SimpleNamespace(list_ingress_for_all_namespaces=_raiser(404)),
    )

    # Act and assert
    with pytest.raises(ApiException):
        sync(client)


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
