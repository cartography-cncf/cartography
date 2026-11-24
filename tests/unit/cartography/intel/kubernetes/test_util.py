import json
from types import SimpleNamespace

import pytest
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.util import get_gpu_quantity
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import k8s_paginate_pages
from cartography.intel.kubernetes.util import MAX_EXPIRED_CONTINUES


def _page(items: list[str], next_token: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(items=items, metadata=SimpleNamespace(_continue=next_token))


def _expired(resume_token: str | None = None) -> ApiException:
    error = ApiException(status=410, reason="Gone")
    metadata = {"continue": resume_token} if resume_token else {}
    error.body = json.dumps({"kind": "Status", "code": 410, "metadata": metadata})
    return error


def _scripted_list(responses: list, calls: list[tuple[int, str | None]]):
    script = iter(responses)

    def list_pod_for_all_namespaces(limit, _continue=None):
        calls.append((limit, _continue))
        response = next(script)
        if isinstance(response, ApiException):
            raise response
        return response

    return list_pod_for_all_namespaces


def test_k8s_paginate_pages_fetches_lazily():
    calls: list[tuple[int, str | None]] = []
    pages = k8s_paginate_pages(
        _scripted_list([_page(["a", "b"], "1"), _page(["c"])], calls)
    )

    assert calls == []
    assert next(pages) == ["a", "b"]
    # The next page is not requested until the caller is done with this one.
    assert calls == [(500, None)]
    assert next(pages) == ["c"]
    assert calls == [(500, None), (500, "1")]
    assert list(pages) == []


def test_k8s_paginate_yields_one_page_at_a_time():
    calls: list[tuple[int, str | None]] = []
    items = k8s_paginate(_scripted_list([_page(["a", "b"], "1"), _page(["c"])], calls))

    assert next(items) == "a"
    assert next(items) == "b"
    assert calls == [(500, None)]
    assert list(items) == ["c"]
    assert calls == [(500, None), (500, "1")]


@pytest.mark.parametrize(
    "responses,expected_items,expected_tokens",
    [
        pytest.param(
            [_page(["a"], "t1"), _expired("r1"), _page(["b"])],
            ["a", "b"],
            [None, "t1", "r1"],
            id="resumes-with-the-token-the-410-carries",
        ),
        pytest.param(
            [
                _page(["a"], "t1"),
                _expired("r1"),
                _page(["b"], "t2"),
                _expired("r2"),
                _page(["c"]),
            ],
            ["a", "b", "c"],
            [None, "t1", "r1", "t2", "r2"],
            id="resumes-each-time-a-token-expires",
        ),
    ],
)
def test_k8s_paginate_pages_resumes_an_expired_continue_token(
    responses, expected_items, expected_tokens
):
    calls: list[tuple[int, str | None]] = []

    items = list(k8s_paginate(_scripted_list(responses, calls)))

    assert items == expected_items
    assert [token for _, token in calls] == expected_tokens


@pytest.mark.parametrize(
    "responses",
    [
        pytest.param([ApiException(status=500)], id="server-error"),
        pytest.param([ApiException(status=403)], id="forbidden"),
        pytest.param(
            [_page(["a"], "t1"), ApiException(status=500)], id="error-after-a-page"
        ),
        pytest.param([_expired("r1")], id="410-on-the-first-request"),
        pytest.param([_page(["a"], "t1"), _expired()], id="410-without-a-token"),
        pytest.param(
            [_page(["a"], "t1")]
            + [_expired(f"r{n}") for n in range(MAX_EXPIRED_CONTINUES + 1)],
            id="more-expiries-than-the-resume-cap",
        ),
    ],
)
def test_k8s_paginate_pages_raises_instead_of_returning_a_partial_list(responses):
    calls: list[tuple[int, str | None]] = []

    with pytest.raises(ApiException):
        list(k8s_paginate_pages(_scripted_list(responses, calls)))

    # Pins the cap row to every allowed resume, not just the first expiry.
    assert len(calls) == len(responses)


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
