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
import os
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


# Stages with no config gate at all: they always do work, so running them here would
# hit the network or Neo4j.
_UNGATED_STAGES = frozenset({"analysis", "create-indexes", "cve_metadata", "ontology"})

# Two stages still resolve something when unconfigured, for reasons that cannot be
# designed away:
#
# - aws: botocore's credential chain ends at the EC2 instance metadata service, which
#   cannot be probed without a network call. A file-and-environment pre-check would
#   silently skip AWS on any EC2 instance running with an instance profile, which is a
#   mainstream deployment, so paying boto3 to get the right answer is the better trade.
# - gcp: google.auth.default() pulls cryptography, and probing for Application Default
#   Credentials contacts the GCE metadata server, which makes this too slow to assert
#   on here. It no longer loads any GCP SDK, which was the expensive part.
#
# azure and oci used to be here too; they now pre-check the az CLI config directory and
# ~/.oci/config, which is exactly what their SDK call reads. This set is asserted
# exactly so it cannot quietly grow back.
_STAGES_THAT_RESOLVE_THEIR_SDK_AT_GATE_TIME = frozenset({"aws", "gcp"})

_RUNTIME_PROBE = """
import sys, json
from unittest.mock import MagicMock

from cartography.config import Config
from cartography.sync import TOP_LEVEL_MODULES

stage = TOP_LEVEL_MODULES[{stage_name!r}]
try:
    stage(MagicMock(), Config(neo4j_uri="bolt://localhost:7687", update_tag=1))
except BaseException:
    # An unconfigured module is allowed to raise; this probe is only about imports.
    pass
tops = sorted({{m.split('.')[0] for m in sys.modules
               if '.' not in m and not m.startswith('_')}})
print('@@' + json.dumps(tops))
"""


def _scrubbed_environment(home: str) -> dict[str, str]:
    """An environment with no ambient cloud credentials for the probe to find."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("AWS_", "AZURE_", "GOOGLE_", "OCI_"))
    }
    env.update(
        HOME=home,
        AWS_EC2_METADATA_DISABLED="true",
        AWS_CONFIG_FILE=os.path.join(home, "absent"),
        AWS_SHARED_CREDENTIALS_FILE=os.path.join(home, "absent"),
    )
    return env


def test_ambient_credential_stage_list_is_exact():
    """Pin both exclusion lists, so a new module cannot quietly join either.

    Adding a name to one of these sets removes it from the parametrize below, which
    would drop that module's coverage without failing anything. Comparing against
    literals makes growth a deliberate edit here.
    """
    assert _STAGES_THAT_RESOLVE_THEIR_SDK_AT_GATE_TIME <= set(TOP_LEVEL_MODULES)
    assert _UNGATED_STAGES <= set(TOP_LEVEL_MODULES)


@pytest.mark.parametrize(
    "stage_name",
    sorted(
        set(TOP_LEVEL_MODULES)
        - _UNGATED_STAGES
        - _STAGES_THAT_RESOLVE_THEIR_SDK_AT_GATE_TIME
    ),
)
def test_unconfigured_stage_does_not_load_its_sdk(stage_name, tmp_path):
    """Running an unconfigured stage must not load its provider SDK.

    Importing the entry point lazily is only half the job: without --selected-modules
    every stage is called, so the config gate has to reject the module before anything
    resolves a lazy binding. If this fails, something above the gate in
    `start_{stage_name}_ingestion` touches a lazily bound name.
    """
    result = subprocess.run(
        [sys.executable, "-c", _RUNTIME_PROBE.format(stage_name=stage_name)],
        capture_output=True,
        text=True,
        env=_scrubbed_environment(str(tmp_path)),
    )
    assert result.returncode == 0, f"probe for {stage_name} failed:\n{result.stderr}"
    pulled = next(
        set(json.loads(line[2:]))
        for line in result.stdout.splitlines()
        if line.startswith("@@")
    )
    provider_sdks = {
        name for name in (pulled - BASELINE) if name not in sys.stdlib_module_names
    }
    assert not provider_sdks, (
        f"running the unconfigured {stage_name} stage loaded {sorted(provider_sdks)}; "
        "the config gate must return before any lazy binding is touched"
    )


def _lazy_import_attribute_uses() -> dict[str, set[str]]:
    """Every third-party `lazy_import` target, mapped to the attributes read off it."""
    uses: dict[str, set[str]] = {}
    for path in sorted((REPOSITORY_ROOT / "cartography").rglob("*.py"), key=str):
        source = path.read_text()
        if "lazy_import(" not in source:
            continue
        tree = ast.parse(source)
        statements: list[ast.stmt] = list(tree.body)
        for statement in tree.body:
            if isinstance(statement, ast.If):
                statements.extend(statement.orelse)

        bound: dict[str, str] = {}
        for node in statements:
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "lazy_import"
                and node.value.args
                and isinstance(node.value.args[0], ast.Constant)
            ):
                target = node.value.args[0].value
                for name in node.targets:
                    if isinstance(name, ast.Name):
                        bound[name.id] = target
        if not bound:
            continue

        for element in ast.walk(tree):
            if not isinstance(element, ast.Attribute) or not isinstance(
                element.value, ast.Name
            ):
                continue
            target = bound.get(element.value.id)
            # Our own packages are covered by the rest of the suite.
            if target is None or target.startswith("cartography."):
                continue
            uses.setdefault(target, set()).add(element.attr)
    return uses


_ATTRIBUTE_PROBE = """
import importlib, json
module = importlib.import_module({target!r})
print('@@' + json.dumps([a for a in {attrs!r} if not hasattr(module, a)]))
"""


@pytest.mark.parametrize(
    "target, attrs",
    sorted((t, sorted(a)) for t, a in _lazy_import_attribute_uses().items()),
)
def test_lazy_import_target_exposes_the_attributes_it_is_used_for(target, attrs):
    """A `lazy_import` binding must name the module that actually holds the attribute.

    `import googleapiclient` does not bind its `discovery` submodule, so
    `lazy_import("googleapiclient").discovery` raises AttributeError at run time while
    passing every import-level check. Bind the submodule itself instead:
    `lazy_import("googleapiclient.discovery")`.

    This has to run in a subprocess importing nothing but the target: once anything
    else in the process has imported `pkg.sub`, Python sets `sub` on `pkg`, and an
    in-process check would pass for the wrong reason.
    """
    result = subprocess.run(
        [sys.executable, "-c", _ATTRIBUTE_PROBE.format(target=target, attrs=attrs)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"importing {target} failed:\n{result.stderr}"
    absent = next(
        json.loads(line[2:])
        for line in result.stdout.splitlines()
        if line.startswith("@@")
    )
    assert not absent, (
        f"`import {target}` does not expose {absent}; bind the submodule directly, "
        f'e.g. lazy_import("{target}.{absent[0]}")'
    )
