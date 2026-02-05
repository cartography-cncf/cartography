import sys
import warnings

_MIN_PYTHON = (3, 13)
_MIN_PYTHON_STR = ".".join(map(str, _MIN_PYTHON))

if sys.version_info < _MIN_PYTHON:
    warnings.warn(
        f"Cartography is tested on Python {_MIN_PYTHON_STR}+ only. "
        f"Backward compatibility with Python 3.10-3.12 is not guaranteed. "
        f"Python 3.10 support will be removed in October 2026. "
        "See: https://github.com/cartography-cncf/cartography/issues/2205",
        FutureWarning,
        stacklevel=2,
    )
