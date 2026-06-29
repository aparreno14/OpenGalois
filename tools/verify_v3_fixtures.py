#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from opengalois.verify import verify_certificate


@dataclass(frozen=True)
class Failure:
    """Represents a failure in the verification process.

    Attributes:
        path (Path): The path to the fixture file.
        expected (bool): The expected verification result.
        got (bool): The actual verification result.
        details (str): Additional details about the failure.
    """

    path: Path
    expected: bool
    got: bool
    details: str


def _iter_json_files(p: Path) -> list[Path]:
    """Retrieve all JSON files in a given directory.

    Args:
        p (Path): The directory to search for JSON files.

    Returns:
        list[Path]: A sorted list of paths to JSON files in the directory.
    """
    if not p.is_dir():
        return []
    return sorted([x for x in p.glob("*.json") if x.is_file()])


def main(argv: list[str]) -> int:
    """Verify all v3 fixture certificates.

    This script checks that all certificates in the "ok" directory pass verification
    and all certificates in the "bad" directory fail verification.

    Args:
        argv (list[str]): Command-line arguments passed to the script.

    Returns:
        int: Exit code (0 if all fixtures pass expectations, 1 otherwise).
    """
    ap = argparse.ArgumentParser(
        description="Verify all v3 fixture certificates (ok must pass, bad must fail)."
    )
    ap.add_argument(
        "--repo-root", default=".", help="Repo root (default: current directory)."
    )
    ap.add_argument(
        "--ruleset",
        default=None,
        help="Optional ruleset id to restrict to (e.g. le5-core@1).",
    )
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    fixtures_root = repo_root / "fixtures" / "v3"

    failures: list[Failure] = []

    rulesets = []
    if args.ruleset:
        rulesets = [args.ruleset]
    else:
        if fixtures_root.is_dir():
            rulesets = sorted([p.name for p in fixtures_root.iterdir() if p.is_dir()])
        else:
            print(f"No fixtures directory: {fixtures_root}")
            return 1

    total = 0
    for rid in rulesets:
        ok_dir = fixtures_root / rid / "ok"
        bad_dir = fixtures_root / rid / "bad"

        for path in _iter_json_files(ok_dir):
            total += 1
            cert = json.loads(path.read_text(encoding="utf-8"))
            res = verify_certificate(cert)
            if res.verified is not True:
                details = ""
                if getattr(res, "checks", None):
                    # show first few failing checks
                    bads = [c for c in res.checks if not c.ok]
                    details = "; ".join(f"{c.name}: {c.details}" for c in bads[:5])
                failures.append(Failure(path, True, False, details))

        for path in _iter_json_files(bad_dir):
            total += 1
            cert = json.loads(path.read_text(encoding="utf-8"))
            res = verify_certificate(cert)
            if res.verified is not False:
                failures.append(Failure(path, False, True, "expected rejection"))

    if failures:
        print(f"[FAIL] fixture verification: {len(failures)}/{total} failures")
        for f in failures:
            print(f"  - {f.path}: expected={f.expected} got={f.got} {f.details}")
        return 1

    print(f"[OK] fixture verification: {total} fixtures passed expectations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
