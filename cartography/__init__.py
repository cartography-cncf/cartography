import sys
import warnings

_MIN_PYTHON = (3, 13)
_MIN_PYTHON_STR = ".".join(map(str, _MIN_PYTHON))

if sys.version_info < _MIN_PYTHON:
    warnings.warn(
        f"Cartography is tested on Python {_MIN_PYTHON_STR}+ only. "
        "Backward compatibility with Python 3.11 and 3.12 is not guaranteed. "
        "Python 3.10 and older are not supported.",
        DeprecationWarning,
        stacklevel=2,
    )
