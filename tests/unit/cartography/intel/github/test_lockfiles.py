import json

from cartography.intel.github.lockfiles import parse_npm_lock
from cartography.intel.github.lockfiles import parse_uv_lock

UV_LOCK = """
version = 1
requires-python = ">=3.13"

[[package]]
name = "django"
version = "4.2.0"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "requests"
version = "2.31.0"
source = { registry = "https://pypi.org/simple" }
"""

NPM_LOCK_V3 = json.dumps(
    {
        "name": "my-app",
        "lockfileVersion": 3,
        "packages": {
            "": {"name": "my-app", "version": "1.0.0"},
            "node_modules/lodash": {"version": "4.17.21"},
            "node_modules/@babel/core": {"version": "7.24.0"},
            "node_modules/express/node_modules/cookie": {"version": "0.6.0"},
        },
    }
)

NPM_LOCK_V1 = json.dumps(
    {
        "name": "my-app",
        "lockfileVersion": 1,
        "dependencies": {
            "lodash": {"version": "4.17.21"},
            "express": {
                "version": "4.18.2",
                "dependencies": {
                    "cookie": {"version": "0.6.0"},
                },
            },
        },
    }
)


def test_parse_uv_lock_returns_exact_versions():
    assert parse_uv_lock(UV_LOCK) == {
        "django": "4.2.0",
        "requests": "2.31.0",
    }


def test_parse_uv_lock_drops_ambiguous_versions():
    # A name resolving to two distinct versions is ambiguous and must be dropped,
    # while unambiguous names are still returned.
    content = (
        '[[package]]\nname = "django"\nversion = "4.2.0"\n'
        '[[package]]\nname = "cffi"\nversion = "1.0.0"\n'
        '[[package]]\nname = "cffi"\nversion = "2.0.0"\n'
    )
    assert parse_uv_lock(content) == {"django": "4.2.0"}


def test_parse_uv_lock_invalid_content_returns_empty():
    assert parse_uv_lock("this is not = valid = toml [[[") == {}


def test_parse_uv_lock_skips_malformed_entries():
    # A package whose name/version is not a string (e.g. an array) must be
    # skipped rather than crashing on use as a dict key / set member.
    content = (
        '[[package]]\nname = [1, 2]\nversion = "9.9.9"\n'
        '[[package]]\nname = "good"\nversion = ["not", "a", "string"]\n'
        '[[package]]\nname = "django"\nversion = "4.2.0"\n'
    )
    assert parse_uv_lock(content) == {"django": "4.2.0"}


def test_parse_npm_lock_v3_returns_only_top_level():
    # The root package ("" key) and nested transitive installs are skipped;
    # only top-level node_modules/<name> installs (incl. scoped) are returned.
    assert parse_npm_lock(NPM_LOCK_V3) == {
        "lodash": "4.17.21",
        "@babel/core": "7.24.0",
    }


def test_parse_npm_lock_v3_top_level_wins_over_nested():
    # A direct top-level cookie@1.0.0 must not be overwritten by a nested
    # transitive cookie@0.6.0.
    content = json.dumps(
        {
            "lockfileVersion": 3,
            "packages": {
                "": {"name": "my-app", "version": "1.0.0"},
                "node_modules/cookie": {"version": "1.0.0"},
                "node_modules/express/node_modules/cookie": {"version": "0.6.0"},
            },
        }
    )
    assert parse_npm_lock(content) == {"cookie": "1.0.0"}


def test_parse_npm_lock_v1_returns_only_top_level():
    # Nested transitive cookie is not traversed; only direct deps are returned.
    assert parse_npm_lock(NPM_LOCK_V1) == {
        "lodash": "4.17.21",
        "express": "4.18.2",
    }


def test_parse_npm_lock_invalid_content_returns_empty():
    assert parse_npm_lock("{not valid json") == {}
