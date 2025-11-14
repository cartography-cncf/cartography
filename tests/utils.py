import logging

logger = logging.getLogger(__name__)


def unwrapper(func):
    """
    Unwraps a function to get past decorators to the original function.
    """
    if not hasattr(func, "__wrapped__"):
        return func
    return unwrapper(func.__wrapped__)
