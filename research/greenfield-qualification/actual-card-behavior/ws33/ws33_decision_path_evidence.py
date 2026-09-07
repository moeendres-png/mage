"""Strict reader for the inherited WS31/WS33 path-attributed decision wire format.

The path and decision kind are Base64 UTF-8, not cleartext. Setup uses the explicit
decoded string `null`. Parsing never grants behavior or coverage qualification.
"""
from __future__ import annotations

import base64
import binascii
from collections import Counter


def decode_field(value: str) -> str:
    try:
        raw = base64.b64decode(value, validate=True)
        decoded = raw.decode('utf-8')
    except (ValueError, UnicodeError, binascii.Error) as exc:
        raise ValueError('invalid Base64 UTF-8 field') from exc
    if base64.b64encode(raw).decode('ascii') != value:
        raise ValueError('noncanonical Base64 field')
    return decoded


def decision_path_counts(text: str, expected: set[str]) -> Counter[str]:
    if not expected or 'null' in expected or '' in expected:
        raise ValueError('invalid expected path set')
    counts: Counter[str] = Counter()
    seen: set[tuple[int, int]] = set()
    for number, line in enumerate(text.splitlines(), 1):
        if not line:
            continue
        fields = line.split('\t')
        if len(fields) != 7:
            raise ValueError(f'row {number}: expected seven columns')
        path, kind, error = (decode_field(fields[i]) for i in (0, 2, 6))
        event, actor, principal = (int(fields[i]) for i in (1, 3, 4))
        if event < 1 or actor < 0 or principal < 0 or actor != principal:
            raise ValueError(f'row {number}: invalid event/actor/principal')
        key = principal, event
        if key in seen:
            raise ValueError(f'row {number}: duplicate principal/event')
        seen.add(key)
        if not kind or fields[5] != 'ACCEPTED' or error != 'null':
            raise ValueError(f'row {number}: missing kind or unsuccessful decision')
        if path == 'null':
            if kind not in {'STARTING_PLAYER', 'MULLIGAN'}:
                raise ValueError(f'row {number}: unattributed non-setup decision')
            continue
        if path not in expected:
            raise ValueError(f'row {number}: foreign path')
        counts[path] += 1
    if set(counts) != expected:
        raise ValueError('decision path coverage mismatch')
    return counts
