"""Lazy import helpers.

An intel module must not pay for a provider SDK it is not going to use. These
helpers let an entrypoint keep its imports at the top of the file while the actual
import happens after the module's config gate has decided to run.
"""

import importlib
from types import ModuleType
from typing import Any


# TODO: translate a ModuleNotFoundError raised by these helpers into an actionable
# error naming the missing pip extra, e.g. "cartography[gcp] is not installed, run
# pip install 'cartography[gcp]'". Blocked on the extras split; see the packaging
# migration. Two constraints that a first attempt got wrong:
#   - Only translate when exc.name does not start with "cartography.", otherwise a typo
#     in one of our own imports gets reported as a missing extra.
#   - Never downgrade this to a silent skip of the stage. "boto3 is missing" and "boto3
#     is installed but one of its dependencies is broken" are indistinguishable from
#     the exception alone, so skipping would drop the ingestion of a stage the operator
#     did configure while the job still reports success. The extra declared for the
#     stage is what makes the two cases separable, which is why this waits for extras.
#
# TODO: drop lazy_import() and lazy_callable() once the minimum supported Python is
# 3.15 and PEP 810 (https://peps.python.org/pep-0810/) is available. Both helpers are
# then replaced by a native `lazy import x` / `lazy from x import y` statement, and no
# call site changes: every binding produced here already behaves like the real object.
class _LazyModule:
    """Proxy that imports the module it stands for on first attribute access."""

    __slots__ = ("_name", "_module")

    _name: str
    _module: ModuleType | None

    def __init__(self, name: str) -> None:
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_module", None)

    @property
    def __name__(self) -> str:
        # A module's own name is known without running it, and callers that only want
        # to identify a module should not pay for importing it.
        return self._name

    def _resolve(self) -> ModuleType:
        module = self._module
        if module is None:
            module = importlib.import_module(self._name)
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._resolve(), attr)

    def __setattr__(self, attr: str, value: Any) -> None:
        # Writes go to the real module, so monkeypatching a lazily bound module works
        # exactly as it does for an eagerly imported one.
        if attr in _LazyModule.__slots__:
            object.__setattr__(self, attr, value)
            return
        setattr(self._resolve(), attr, value)

    def __delattr__(self, attr: str) -> None:
        delattr(self._resolve(), attr)

    def __repr__(self) -> str:
        return f"lazy_import({self._name})"


def lazy_import(name: str) -> Any:
    """
    Bind a module name without importing it, deferring the import to first use.

    Use this instead of a plain ``import`` when a module pulls a provider SDK that
    should only be paid for when the module is actually used, typically after an
    intel module's config gate has decided to run.

    Args:
        name: The fully qualified module name, e.g. "googleapiclient.discovery".

    Returns:
        A proxy that imports the real module on first attribute access and forwards
        every attribute to it. Any ImportError surfaces at that first access rather
        than at binding time.

    Examples:
        Deferring an SDK used inside an except clause:
        >>> discovery = lazy_import("googleapiclient.discovery")
        >>> # googleapiclient is not imported yet
        >>> try:  # doctest: +SKIP
        ...     resource.execute()
        ... except discovery.HttpError:
        ...     pass

    Note:
        Nothing at all happens at binding time, not even a filesystem lookup. That
        matters twice over: importlib.util.find_spec() would import the parent
        package (google.api_core costs 0.3s on its own), and it would also raise for
        an SDK that is not installed, which is exactly the case a module gated off by
        its config must survive.
    """
    return _LazyModule(name)


class _LazyCallable:
    """Callable that defers `from <module> import <attr>` until first invocation."""

    __slots__ = ("_name", "_attr", "_module")

    _name: str
    _attr: str
    _module: ModuleType | None

    def __init__(self, module: str, attr: str) -> None:
        object.__setattr__(self, "_name", module)
        object.__setattr__(self, "_attr", attr)
        object.__setattr__(self, "_module", None)

    def _resolve(self) -> Any:
        module = self._module
        if module is None:
            module = importlib.import_module(self._name)
            object.__setattr__(self, "_module", module)
        # Looked up on every access rather than cached, so that patching the attribute
        # on the module keeps working the way it does for a plain attribute access.
        return getattr(module, self._attr)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._resolve()(*args, **kwargs)

    def __getattr__(self, attr: str) -> Any:
        # Bound names stand in for functions but also for classes, so reads and writes
        # of their own attributes have to reach the real object: patching a method with
        # `patch("pkg.SomeClass.method")` resolves it through here.
        return getattr(self._resolve(), attr)

    def __setattr__(self, attr: str, value: Any) -> None:
        if attr in _LazyCallable.__slots__:
            object.__setattr__(self, attr, value)
            return
        setattr(self._resolve(), attr, value)

    def __delattr__(self, attr: str) -> None:
        delattr(self._resolve(), attr)

    def __repr__(self) -> str:
        return f"lazy_callable({self._name}.{self._attr})"


def lazy_callable(module: str, attr: str) -> Any:
    """
    Defer ``from <module> import <attr>`` until the returned object is first called.

    This is the drop-in replacement for a top-level import of a function whose module
    pulls a provider SDK: the binding keeps the same name, so call sites do not change.

    Args:
        module: The fully qualified module name to import from.
        attr: The attribute to pull out of that module.

    Returns:
        A callable that imports the module and resolves the attribute on first call,
        then forwards every call to it and returns its result.

    Examples:
        Replacing a top-level import in an intel module entrypoint:
        >>> sync_gcp_instances = lazy_callable(
        ...     "cartography.intel.gcp.compute", "sync_gcp_instances"
        ... )
        >>> # cartography.intel.gcp.compute, and googleapiclient with it, load on the
        >>> # first sync_gcp_instances(...) call
    """
    return _LazyCallable(module, attr)
