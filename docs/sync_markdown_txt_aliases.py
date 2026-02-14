#!/usr/bin/env python3
"""Sync `*.md.txt` aliases for docs markdown files.

Some docs consumers request raw markdown paths with a `.txt` suffix (for example,
`config.md.txt`). This script keeps `docs/root/**/*.md.txt` aliases in sync with
`docs/root/**/*.md` files.
"""

from __future__ import annotations

import argparse
from pathlib import Path

DOCS_ROOT = Path(__file__).parent / "root"


class AliasError(Exception):
    pass


def expected_alias_target(md_path: Path) -> str:
    return md_path.name


def sync_aliases(*, check: bool) -> list[str]:
    changes: list[str] = []
    errors: list[str] = []

    for md_path in sorted(DOCS_ROOT.rglob("*.md")):
        alias_path = md_path.with_name(f"{md_path.name}.txt")
        target = expected_alias_target(md_path)

        if not alias_path.exists() and not alias_path.is_symlink():
            if check:
                errors.append(f"Missing alias: {alias_path}")
            else:
                alias_path.symlink_to(target)
                changes.append(f"Created {alias_path} -> {target}")
            continue

        if not alias_path.is_symlink():
            errors.append(f"Alias exists but is not a symlink: {alias_path}")
            continue

        current_target = str(alias_path.readlink())
        if current_target != target:
            if check:
                errors.append(
                    f"Alias points to {current_target} but expected {target}: {alias_path}")
            else:
                alias_path.unlink()
                alias_path.symlink_to(target)
                changes.append(f"Updated {alias_path} -> {target}")

    if errors:
        raise AliasError("\n".join(errors))

    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate aliases only. Exit non-zero if aliases are missing/out of sync.",
    )
    args = parser.parse_args()

    try:
        changes = sync_aliases(check=args.check)
    except AliasError as e:
        print(e)
        return 1

    if args.check:
        print("All markdown .txt aliases are in sync.")
    else:
        if changes:
            print("\n".join(changes))
        else:
            print("No alias changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
