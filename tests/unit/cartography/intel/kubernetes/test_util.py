import pytest
from kubernetes.client.exceptions import ApiException

from cartography.intel.kubernetes.util import k8s_paginate


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
