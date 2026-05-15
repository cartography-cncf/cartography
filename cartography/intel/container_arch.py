from __future__ import annotations

import re

# Canonical architecture source values for runtime containers.
ARCH_SOURCE_RUNTIME_API_EXACT = "runtime_api_exact"
ARCH_SOURCE_TASK_DEFINITION_HINT = "task_definition_hint"
ARCH_SOURCE_PLATFORM_REQUIREMENT = "platform_requirement"


_CANONICAL_BY_ALIAS = {
    "amd64": "amd64",
    "x86_64": "amd64",
    "x64": "amd64",
    "x86-64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
    "arm64/v8": "arm64",
    "arm": "arm",
    "arm/v7": "arm",
    "armv7": "arm",
    "armv7l": "arm",
    "386": "386",
    "i386": "386",
    "x86": "386",
    "ppc64le": "ppc64le",
    "s390x": "s390x",
    "riscv64": "riscv64",
}

_CANONICAL_VALUES = {
    "amd64",
    "arm64",
    "arm",
    "386",
    "ppc64le",
    "s390x",
    "riscv64",
    "unknown",
}

_ARMV7_PATTERN = re.compile(r"armv7[a-z0-9]*", re.IGNORECASE)


def normalize_architecture(raw: str | None) -> str:
    if raw is None:
        return "unknown"
    value = raw.strip()
    if not value:
        return "unknown"

    lowered = value.lower()
    if lowered in _CANONICAL_BY_ALIAS:
        return _CANONICAL_BY_ALIAS[lowered]
    if lowered in _CANONICAL_VALUES:
        return lowered
    if _ARMV7_PATTERN.fullmatch(lowered):
        return "arm"
    return "unknown"
