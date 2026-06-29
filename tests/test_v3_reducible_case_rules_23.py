from __future__ import annotations

import json
from pathlib import Path

import pytest

from opengalois.verify import verify_certificate

FIXTURE_DIR = Path('fixtures/v3/le5-core@1')

OK = [
    FIXTURE_DIR / 'ok' / 'galois_group.QQ.reducible.quadratic_cubic.C6@1_001.json',
    FIXTURE_DIR / 'ok' / 'galois_group.QQ.reducible.quadratic_cubic.S3@1_001.json',
    FIXTURE_DIR / 'ok' / 'galois_group.QQ.reducible.quadratic_cubic.D6@1_001.json',
    FIXTURE_DIR / 'ok' / 'galois_group.QQ.reducible.quadratic_cubic.S3@2_001.json',
    FIXTURE_DIR / 'ok' / 'galois_group.QQ.reducible.quadratic_cubic.D6@2_001.json',
]

BAD = [
    FIXTURE_DIR / 'bad' / 'galois_group.QQ.reducible.quadratic_cubic.C6@1_fail_001.json',
    FIXTURE_DIR / 'bad' / 'galois_group.QQ.reducible.quadratic_cubic.C6@1_fail_002.json',
    FIXTURE_DIR / 'bad' / 'galois_group.QQ.reducible.quadratic_cubic.S3@1_fail_001.json',
    FIXTURE_DIR / 'bad' / 'galois_group.QQ.reducible.quadratic_cubic.S3@1_fail_002.json',
    FIXTURE_DIR / 'bad' / 'galois_group.QQ.reducible.quadratic_cubic.D6@1_fail_001.json',
    FIXTURE_DIR / 'bad' / 'galois_group.QQ.reducible.quadratic_cubic.D6@1_fail_002.json',
    FIXTURE_DIR / 'bad' / 'galois_group.QQ.reducible.quadratic_cubic.D6@2_fail_001.json',
    FIXTURE_DIR / 'bad' / 'galois_group.QQ.reducible.quadratic_cubic.S3@2_fail_001.json',
]


@pytest.mark.parametrize('path', OK)
def test_ok(path: Path) -> None:
    cert = json.loads(path.read_text(encoding='utf-8'))
    vr = verify_certificate(cert)
    for c in vr.checks:
        if not c.ok:
            print(f"check failed: {c.name}\n{c.details}")
    assert vr.verified, path.as_posix()


@pytest.mark.parametrize('path', BAD)
def test_bad(path: Path) -> None:
    cert = json.loads(path.read_text(encoding='utf-8'))
    vr = verify_certificate(cert)
    assert not vr.verified, path.as_posix()
