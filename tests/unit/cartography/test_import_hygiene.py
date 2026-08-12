"""Guard that importing an intel module does not pull its provider SDK.

Every intel entrypoint runs a config gate before doing any work. That gate is only
useful if it runs *before* the SDK loads, otherwise a sync with no credentials still
pays for boto3, the Azure SDK, googleapiclient and the rest. This is also the
precondition for splitting cartography into pip extras: a module whose SDK is not
installed must still be importable so it can skip itself.

The mechanism is `cartography.util.lazy`; these tests are what keeps it honest.
"""

import ast
import json
import pathlib
import subprocess
import sys

import pytest

from cartography.sync import TOP_LEVEL_MODULES

REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[3]

# Distributions the core package depends on regardless of which provider is synced.
# Anything outside this set belongs to a provider and must load lazily.
CORE_DISTRIBUTIONS = {
    "annotated_types",
    "attr",
    "backoff",
    "certifi",
    "charset_normalizer",
    "click",
    "colorsys",
    "dateutil",
    "idna",
    "importlib_metadata",
    "jmespath",
    "marshmallow",
    "neo4j",
    "packageurl",
    "packaging",
    "pydantic",
    "pydantic_core",
    "pygments",
    "requests",
    "rich",
    "six",
    "socks",
    "statsd",
    "stringprep",
    "typer",
    "typing_extensions",
    "typing_inspection",
    "urllib3",
    "wrapt",
    "yaml",
    "zipp",
}

_PROBE = (
    "import sys, json\n"
    "import {module}\n"
    "tops = sorted({{m.split('.')[0] for m in sys.modules "
    "if '.' not in m and not m.startswith('_')}})\n"
    "print('@@' + json.dumps(tops))\n"
)


def _top_level_imports(module: str) -> set[str]:
    """Import `module` in a fresh interpreter and return the top-level packages it pulled."""
    result = subprocess.run(
        [sys.executable, "-c", _PROBE.format(module=module)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"importing {module} failed:\n{result.stderr}"
    for line in result.stdout.splitlines():
        if line.startswith("@@"):
            return set(json.loads(line[2:]))
    raise AssertionError(f"probe produced no output for {module}:\n{result.stdout}")


def _entrypoint_module(stage_name: str) -> str:
    if stage_name == "create-indexes":
        return "cartography.intel.create_indexes"
    return f"cartography.intel.{stage_name}"


BASELINE = _top_level_imports("cartography.sync") | CORE_DISTRIBUTIONS


def test_sync_import_does_not_pull_boto3() -> None:
    """The core sync machinery must not depend on any provider SDK."""
    assert "boto3" not in _top_level_imports("cartography.sync")


@pytest.mark.parametrize("stage_name", sorted(TOP_LEVEL_MODULES))
def test_intel_entrypoint_is_import_light(stage_name):
    """Importing an intel entrypoint must not load anything provider-specific.

    If this fails, an import in `cartography/intel/<module>/__init__.py` reaches a
    provider SDK. Replace it with a `lazy_import` / `lazy_callable` binding from
    `cartography.util.lazy` so the SDK only loads once the config gate has passed.
    """
    pulled = _top_level_imports(_entrypoint_module(stage_name))
    provider_sdks = {
        name for name in (pulled - BASELINE) if name not in sys.stdlib_module_names
    }
    assert not provider_sdks, (
        f"importing cartography.intel.{stage_name} loaded {sorted(provider_sdks)}; "
        "bind those imports lazily with cartography.util.lazy"
    )


def _lazy_callable_names(tree: ast.Module) -> set[str]:
    """Names bound at module scope to a lazy_callable(...) proxy."""
    names: set[str] = set()
    statements = list(tree.body)
    for node in tree.body:
        # Bindings behind `if TYPE_CHECKING: ... else: ...` count too.
        if isinstance(node, ast.If):
            statements.extend(node.orelse)
    for node in statements:
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "lazy_callable"
        ):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def _names_needing_a_real_class(tree: ast.Module) -> set[str]:
    """Names used where a genuine class is required, not a callable proxy."""
    used: set[str] = set()

    def record(node: ast.expr | None) -> None:
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Tuple):
            for element in node.elts:
                record(element)

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            record(node.type)
        elif isinstance(node, ast.ClassDef):
            for base in node.bases:
                record(base)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in ("isinstance", "issubclass")
            and len(node.args) == 2
        ):
            record(node.args[1])
    return used


def test_lazy_callable_is_not_used_where_a_class_is_required() -> None:
    """`lazy_callable` returns a proxy, so it cannot stand in for a class.

    `except proxy:` raises TypeError, and so do isinstance, issubclass and subclassing.
    Bind the module with `lazy_import` and reach the class through it instead, e.g.
    `except errors.TransientError:`.
    """
    misuses: list[str] = []
    for path in sorted((REPOSITORY_ROOT / "cartography").rglob("*.py"), key=str):
        source = path.read_text()
        if "lazy_callable(" not in source:
            continue
        tree = ast.parse(source)
        misused = _lazy_callable_names(tree) & _names_needing_a_real_class(tree)
        if misused:
            relative = path.relative_to(REPOSITORY_ROOT)
            misuses.extend(f"{relative}: {name}" for name in sorted(misused))

    assert not misuses, (
        "these names are lazy_callable proxies but are used where a real class is "
        "required; bind the module with lazy_import and use module.ClassName instead:\n"
        + "\n".join(misuses)
    )
