#!/usr/bin/env python3
"""C14 synthetic input-integrity controls; no Rules/card-behavior credit."""
import argparse
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zipfile

import mtgjson_reference as m


class ReferenceControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.meta = {"version": "5.3.0+20261004", "date": "2026-10-04"}
        for name in m.FILES:
            self.archive(name)
        self.pin_path = self.root / "pin.json"
        m.cmd_pin(argparse.Namespace(dir=str(self.root), repo="moeendres-png/mage", out=str(self.pin_path)))
        self.pin = json.loads(self.pin_path.read_text())
        self.receipt = self.root / "receipt.json"
        self.args = argparse.Namespace(pin=str(self.pin_path), dir=str(self.root), receipt=str(self.receipt))

    def archive(self, name, meta=None, member=None):
        with zipfile.ZipFile(self.root / name, "w") as z:
            z.writestr(member or name.removesuffix(".zip"), json.dumps({"meta": meta or self.meta, "data": {}}))

    def test_exact_cached_bytes_are_verified_without_network(self):
        with patch.object(m.urllib.request, "urlopen", side_effect=AssertionError("network")):
            self.assertEqual(m.cmd_fetch(self.args), 0)
        result = json.loads(self.receipt.read_text())
        self.assertEqual(result["status"], "INPUT_BOUND")
        self.assertFalse(result["qualification_credit"])
        self.assertEqual(result["pin_sha256"], m.sha256(self.pin_path))

    def test_fetch_uses_pinned_release_and_rechecks_downloaded_bytes(self):
        payloads = {name: (self.root / name).read_bytes() for name in m.FILES}
        for name in m.FILES:
            (self.root / name).unlink()
        seen = []
        def fetch(url, **kwargs):
            seen.append(url)
            return io.BytesIO(payloads[url.rsplit("/", 1)[1]])
        with patch.object(m.urllib.request, "urlopen", side_effect=fetch):
            self.assertEqual(m.cmd_fetch(self.args), 0)
        self.assertEqual(len(seen), 2)
        self.assertTrue(all("/releases/download/" + self.pin["release"] + "/" in u for u in seen))

    def test_failed_download_replaces_stale_success_receipt(self):
        self.assertEqual(m.cmd_fetch(self.args), 0)
        (self.root / m.FILES[0]).write_bytes(b"tampered")
        with patch.object(m.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline")):
            self.assertEqual(m.cmd_fetch(self.args), 1)
        result = json.loads(self.receipt.read_text())
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["qualification_credit"])

    def test_tampered_download_cannot_become_bound(self):
        (self.root / m.FILES[0]).unlink()
        with patch.object(m.urllib.request, "urlopen", return_value=io.BytesIO(b"wrong")):
            self.assertEqual(m.cmd_fetch(self.args), 1)
        self.assertEqual(json.loads(self.receipt.read_text())["status"], "FAIL")

    def test_atomic_metadata_mismatch_is_refused_even_with_matching_hash(self):
        self.archive("AtomicCards.json.zip", {"version": "older", "date": "2026-10-03"})
        self.pin["files"]["AtomicCards.json.zip"] = {"sha256": m.sha256(self.root / "AtomicCards.json.zip"), "bytes": (self.root / "AtomicCards.json.zip").stat().st_size}
        self.pin_path.write_text(json.dumps(self.pin))
        self.assertEqual(m.cmd_fetch(self.args), 1)
        self.assertEqual(json.loads(self.receipt.read_text())["status"], "FAIL")

    def test_pin_rejects_mixed_epochs(self):
        self.archive("AtomicCards.json.zip", {"version": "older", "date": "2026-10-03"})
        with self.assertRaises(ValueError):
            m.cmd_pin(argparse.Namespace(dir=str(self.root), repo="moeendres-png/mage", out=str(self.pin_path)))

    def test_archive_layout_must_match_expected_file(self):
        self.archive("AtomicCards.json.zip", member="wrong.json")
        with self.assertRaises(SystemExit):
            m.read_meta(self.root / "AtomicCards.json.zip")

    def test_non_regular_target_refused(self):
        target = self.root / m.FILES[0]
        target.unlink()
        target.symlink_to(self.pin_path)
        self.assertEqual(m.cmd_fetch(self.args), 1)

    def test_malformed_pin_fields_fail_closed(self):
        for mutate in (
            lambda p: p.update(repository="owner/repo?query"),
            lambda p: p.update(release="../outside"),
            lambda p: p.update(meta={"date": "not-a-date", "version": "5"}),
            lambda p: p["files"][m.FILES[0]].update(bytes=True),
            lambda p: p["files"][m.FILES[0]].update(bytes=-1),
            lambda p: p["files"][m.FILES[0]].update(sha256="not-a-hash"),
            lambda p: p["files"].update(extra={}),
        ):
            p = copy.deepcopy(self.pin)
            mutate(p)
            with self.subTest(pin=p), self.assertRaises(ValueError):
                m.validate_pin(p)

    def test_same_version_different_bytes_produce_different_release_identity(self):
        old = self.pin["release"]
        with zipfile.ZipFile(self.root / m.FILES[0], "w") as z:
            z.writestr(m.FILES[0].removesuffix(".zip"), json.dumps({"meta": self.meta, "data": {"changed": True}}))
        m.cmd_pin(argparse.Namespace(dir=str(self.root), repo="moeendres-png/mage", out=str(self.pin_path)))
        self.assertNotEqual(old, json.loads(self.pin_path.read_text())["release"])


if __name__ == "__main__":
    unittest.main()
