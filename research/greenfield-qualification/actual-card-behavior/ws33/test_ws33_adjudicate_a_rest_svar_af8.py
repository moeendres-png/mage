"""Fail-closed regression tests for the A-rest AF8 adjudicator.

Builds synthetic but schema-exact Record/Replay evidence for the eight-path AF8 shape
(seven ChangeZone-to-Hand children, one Pump/Fear child on an Announce-X Charm parent)
and checks the PASS baseline plus one focused negative per fail-closed rule. No Forge,
network, card-name production logic, or canonical coverage mutation is involved.
"""
import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ws33_adjudicate_a_rest_svar_af8 import main as adjudicate_main  # noqa: E402


def enc(s):
    return base64.b64encode(s.encode()).decode()


PATHS = [f"forge-behavior-v2:path-{i}" for i in range(8)]
X_PATH = PATHS[6]
NON_CHARM_PATH = PATHS[3]


def script_for(pid):
    if pid == X_PATH:
        return "SP$ Charm | Announce$ X | Choices$ DBLose,DBWeaken | CharmNum$ 2"
    if pid == NON_CHARM_PATH:
        return "SP$ ChangeZone | Origin$ Battlefield | Destination$ Hand | SubAbility$ DBChange"
    return "SP$ Charm | MinCharmNum$ 1 | CharmNum$ 2 | Choices$ ChangeCreature,ChangeLand"


def target_for(pid):
    if pid == X_PATH:
        return "DB$ Pump | ValidTgts$ Creature | TargetMax$ X | KW$ Fear"
    return "DB$ ChangeZone | Origin$ Graveyard | Destination$ Hand | ValidTgts$ Land.YouCtrl"


def dispatch_for(pid):
    return "ChangeZone" if pid == NON_CHARM_PATH else "Charm"


def case_row(i, pid):
    f = [""] * 19
    f[0] = str(i)
    f[1] = pid
    f[2] = f"oracle-{i}"
    f[3] = f"Card-{i}"
    f[4] = dispatch_for(pid)
    f[5] = "forge.game.spellability.TargetRestrictions"
    f[6] = f"src/path-{i}.txt"
    f[7] = str(10 + i)
    f[8] = "ABILITY"
    f[9] = "SP$"
    f[10] = "1"
    f[11] = "0"
    f[12] = "1"
    f[13] = "1"
    f[14] = enc(script_for(pid))
    f[15] = ""
    f[16] = ""
    f[17] = "ChangeZone" if pid != X_PATH else "Pump"
    f[18] = enc(target_for(pid))
    return "\t".join(f)


def summary_row(pid, status="PASS"):
    f = [""] * 22
    f[0] = pid
    f[1] = "7"
    f[4] = status
    f[5] = "digest-before"
    f[6] = "digest-after"
    f[7] = "2"
    f[8] = "0"
    f[9] = "0"
    f[10] = "0"
    f[14] = ""
    f[15] = ""
    f[18] = "1"
    f[19] = "1"
    f[20] = "1"
    f[21] = "1"
    return "\t".join(f)


def decision_row(pid, event):
    return "\t".join((enc(pid), str(event), enc("TARGET_SELECTION"), "1", "1", "ACCEPTED", enc("null")))


def effect_row(pid):
    kind = "KEYWORD" if pid == X_PATH else "ZONE"
    expected = "Fear" if pid == X_PATH else "Hand"
    return "\t".join((pid, kind, enc(expected), "1", "1", "1"))


def target_row(pid, **over):
    zone = "Battlefield" if pid == X_PATH else "Graveyard"
    r = {
        "card": "101", "name": enc("Runeclaw Bear"), "types": enc("Creature"),
        "creature": "true" if pid == X_PATH else "false",
        "before": zone, "after": "Battlefield" if pid == X_PATH else "Hand",
        "bkw": "false", "akw": "true" if pid == X_PATH else "false",
        "src": "11", "root": "22", "child": "33", "actor": "1",
    }
    r.update(over)
    return "\t".join((pid, r["card"], r["name"], r["types"], r["creature"], r["before"],
                       r["after"], r["bkw"], r["akw"], r["src"], r["root"], r["child"], r["actor"]))


def selection_rows(pid):
    rows = []
    if pid == X_PATH:
        rows.append("\t".join((pid, "GUI_GET_INTEGER", "1", "1", "6", "1", "1", "1",
                                "choice:2", enc("2"), "POSITIVE_X_ANNOUNCEMENT", "false")))
    if dispatch_for(pid) == "Charm":
        if pid == X_PATH:
            rows.append("\t".join((pid, "MODE_SELECTION", "1", "1", "4", "2", "2", "2",
                                    "choice:0,choice:1", enc("ability_sub:11") + "," + enc("ability_sub:22"),
                                    "SOURCE_PROVEN_DESIRED_PLUS_MINIMUM", "false")))
        else:
            rows.append("\t".join((pid, "MODE_SELECTION", "1", "1", "3", "1", "2", "1",
                                    "choice:0", enc("ability_sub:11"),
                                    "SOURCE_PROVEN_DESIRED_PLUS_MINIMUM", "false")))
    rows.append("\t".join((pid, "TARGET_SELECTION", "1", "1", "3", "1", "1", "1",
                            "", "", "AUTHORITATIVE_STABLE_ORDER", "false")))
    if pid == PATHS[0]:
        rows.append("\t".join((pid, "CONFIRM_ACTION", "1", "1", "2", "2", "2", "2",
                                "choice:0,choice:1", enc("true") + "," + enc("false"),
                                "AUTHORITATIVE_STABLE_ORDER", "true")))
    return rows


def client_row(pid):
    return "\t".join((pid, "2", "2", "1", "0"))


def stage_rows(pid):
    api = enc(dispatch_for(pid))
    out = []
    for stage in ("PLAY_SPELL_ENTRY", "PLAY_ABILITY_TRUE", "PREREQUISITES_MET", "SETUP_TARGETS"):
        out.append("\t".join((enc(pid), enc(stage), "true", api)))
    return out


class Fixture:
    def __init__(self, tmp):
        self.tmp = Path(tmp)
        self.record = self.tmp / "record"
        self.replay = self.tmp / "replay"
        self.record.mkdir()
        self.replay.mkdir()
        self.cases = self.tmp / "cases.tsv"
        self.cases.write_text("\n".join(case_row(i, p) for i, p in enumerate(PATHS)) + "\n")
        self.out = self.tmp / "GATE.json"
        self.write_all()

    def write_all(self):
        events = []
        event_id = 1
        for pid in PATHS:
            events.append(decision_row(pid, event_id))
            event_id += 1
            events.append(decision_row(pid, event_id))
            event_id += 1
        files = {
            "case-summary.tsv": [summary_row(p) for p in PATHS],
            "decision-events-with-path.tsv": events,
            "AF8_EFFECT_EVIDENCE.tsv": [effect_row(p) for p in PATHS],
            "AF8_TARGET_EVIDENCE.tsv": [target_row(p) for p in PATHS],
            "AF8_SELECTION_WITNESS.tsv": [r for p in PATHS for r in selection_rows(p)],
            "AF8_CLIENT_OBSERVATION_SAMPLES.tsv": [client_row(p) for p in PATHS],
            "play-stages.tsv": [r for p in PATHS for r in stage_rows(p)],
            "PRINCIPAL_OBSERVATIONS.jsonl": [],
        }
        for d in (self.record, self.replay):
            for name, rows in files.items():
                (d / name).write_text(("\n".join(rows) + "\n") if rows else "")

    def run(self):
        argv = ["x", "--cases", str(self.cases), "--record-dir", str(self.record),
                "--replay-dir", str(self.replay), "--out", str(self.out)]
        old = sys.argv
        sys.argv = argv
        try:
            try:
                adjudicate_main()
                code = 0
            except SystemExit as exc:
                code = exc.code
        finally:
            sys.argv = old
        gate = json.loads(self.out.read_text())
        return code, gate

    def rewrite(self, dirname, name, rows):
        (self.tmp / dirname / name).write_text(("\n".join(rows) + "\n") if rows else "")


class AdjudicatorTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.fx = Fixture(self._tmp.name)

    def assert_fail(self, fragment):
        code, gate = self.fx.run()
        self.assertNotEqual(code, 0)
        self.assertEqual(gate["status"], "FAIL_CLOSED")
        self.assertTrue(any(fragment in f for f in gate["failures"]), gate["failures"])

    def test_valid_baseline_pass(self):
        code, gate = self.fx.run()
        self.assertEqual(code, 0, gate.get("failures"))
        self.assertEqual(gate["status"], "PASS")
        self.assertTrue(gate["identity_bound_evidence_required"])
        self.assertTrue(gate["forced_selection_classification_required"])
        self.assertFalse(gate["coverage_mutated"])
        self.assertFalse(gate["coverage_promotion"])

    def test_wrong_target_postcondition(self):
        self.fx.rewrite("record", "AF8_TARGET_EVIDENCE.tsv",
                        [target_row(p, after="Graveyard") if p == PATHS[0] else target_row(p) for p in PATHS])
        self.assert_fail("exact_zone_movement_missing")

    def test_keyword_not_observed(self):
        self.fx.rewrite("record", "AF8_TARGET_EVIDENCE.tsv",
                        [target_row(p, akw="false") if p == X_PATH else target_row(p) for p in PATHS])
        self.assert_fail("keyword_not_observed")

    def test_selected_creature_gain_missing(self):
        self.fx.rewrite("record", "AF8_TARGET_EVIDENCE.tsv",
                        [target_row(p, creature="false") if p == X_PATH else target_row(p) for p in PATHS])
        self.assert_fail("selected_creature_gain_missing")

    def test_chain_split(self):
        rows = [target_row(p, src="99") if p == PATHS[1] else target_row(p) for p in PATHS]
        rows.append(target_row(PATHS[1], card="102"))
        self.fx.rewrite("record", "AF8_TARGET_EVIDENCE.tsv", rows)
        self.assert_fail("source_root_actor_chain_split")

    def test_duplicate_target_card(self):
        rows = [target_row(p) for p in PATHS] + [target_row(PATHS[2])]
        self.fx.rewrite("record", "AF8_TARGET_EVIDENCE.tsv", rows)
        self.assert_fail("duplicate_target_card")

    def test_foreign_target_path(self):
        rows = [target_row(p) for p in PATHS] + [target_row("forge-behavior-v2:foreign")]
        self.fx.rewrite("record", "AF8_TARGET_EVIDENCE.tsv", rows)
        self.assert_fail("unknown_target_path")

    def test_x_wrong_kind(self):
        rows = []
        for p in PATHS:
            for r in selection_rows(p):
                if p == X_PATH and r.split("\t")[1] == "GUI_GET_INTEGER":
                    r = r.replace("GUI_GET_INTEGER", "NUMBER", 1)
                rows.append(r)
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("x_announcement_selection_missing")

    def test_x_not_positive(self):
        rows = []
        for p in PATHS:
            for r in selection_rows(p):
                if p == X_PATH and "POSITIVE_X_ANNOUNCEMENT" in r:
                    r = r.replace(enc("2"), enc("0"))
                rows.append(r)
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("x_not_positive")

    def test_mode_selection_missing(self):
        rows = [r for p in PATHS for r in selection_rows(p)
                if not (p == PATHS[1] and r.split("\t")[1] == "MODE_SELECTION")]
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("mode_selection_missing")

    def test_mode_cardinality(self):
        rows = []
        for p in PATHS:
            for r in selection_rows(p):
                if p == PATHS[1] and r.split("\t")[1] == "MODE_SELECTION":
                    r = "\t".join((p, "MODE_SELECTION", "1", "1", "3", "1", "2", "2",
                                    "choice:0,choice:1",
                                    enc("ability_sub:11") + "," + enc("ability_sub:22"),
                                    "SOURCE_PROVEN_DESIRED_PLUS_MINIMUM", "false"))
                rows.append(r)
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("mode_cardinality")

    def test_forced_misclassified(self):
        rows = []
        for p in PATHS:
            for r in selection_rows(p):
                if p == PATHS[0] and "CONFIRM_ACTION" in r:
                    r = r.rsplit("\t", 1)[0] + "\tfalse"
                rows.append(r)
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("forced_misclassified")

    def test_single_option_not_forced_selection(self):
        bad = "\t".join((PATHS[2], "TARGET_SELECTION", "1", "1", "1", "0", "1", "1",
                          "", "", "AUTHORITATIVE_STABLE_ORDER", "true"))
        rows = [r for p in PATHS for r in selection_rows(p)] + [bad]
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("forced_misclassified")

    def test_unknown_basis_rejected(self):
        rows = [r.replace("AUTHORITATIVE_STABLE_ORDER", "SMART_FALLBACK", 1)
                if (p == PATHS[2] and "TARGET_SELECTION" in r) else r
                for p in PATHS for r in selection_rows(p)]
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("unknown_selection_basis")

    def test_wrong_principal_scope(self):
        rows = [r.replace("\t1\t1\t3\t1\t1\t1\t", "\t1\t2\t3\t1\t1\t1\t", 1)
                if (p == PATHS[2] and "TARGET_SELECTION" in r) else r
                for p in PATHS for r in selection_rows(p)]
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("selection_principal_scope")

    def test_illegal_cardinality(self):
        rows = []
        for p in PATHS:
            for r in selection_rows(p):
                if p == PATHS[2] and "TARGET_SELECTION" in r:
                    f = r.split("\t")
                    f[7] = "2"
                    r = "\t".join(f)
                rows.append(r)
        self.fx.rewrite("record", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("selection_cardinality")

    def test_altered_replay_rejected(self):
        self.fx.rewrite("replay", "AF8_TARGET_EVIDENCE.tsv",
                        [target_row(p, child="34") if p == PATHS[4] else target_row(p) for p in PATHS])
        self.assert_fail("target_replay_mismatch")

    def test_empty_replay_witness_pass(self):
        self.fx.rewrite("replay", "AF8_SELECTION_WITNESS.tsv", [])
        code, gate = self.fx.run()
        self.assertEqual(code, 0, gate.get("failures"))
        self.assertEqual(gate["status"], "PASS")

    def test_replay_novel_live_decision_rejected(self):
        novel = "\t".join((PATHS[0], "NEVER_SEEN", "1", "1", "2", "1", "1", "1",
                            "choice:0", enc("x"), "AUTHORITATIVE_STABLE_ORDER", "false"))
        rows = [r for p in PATHS for r in selection_rows(p)] + [novel]
        self.fx.rewrite("replay", "AF8_SELECTION_WITNESS.tsv", rows)
        self.assert_fail("selection_unexpected_live_decision")

    def test_production_stage_success_required(self):
        rows = []
        for line in (self.fx.record / "play-stages.tsv").read_text().splitlines():
            f = line.split("\t")
            import base64 as _b64
            if _b64.b64decode(f[1]).decode() == "PREREQUISITES_MET":
                f[2] = "false"
            rows.append("\t".join(f))
        self.fx.rewrite("record", "play-stages.tsv", rows)
        self.assert_fail("production_stage_success_missing")

    def test_terminal_play_stage_failure(self):
        rows = (self.fx.record / "play-stages.tsv").read_text().splitlines()
        rows.append("\t".join((enc(PATHS[5]), enc("PLAY_ABILITY_FALSE"), "false", enc("Charm"))))
        self.fx.rewrite("record", "play-stages.tsv", rows)
        self.assert_fail("terminal_play_stage_failure")

    def test_source_stage_success_required(self):
        rows = []
        for line in (self.fx.record / "play-stages.tsv").read_text().splitlines():
            f = line.split("\t")
            import base64 as _b64
            if _b64.b64decode(f[0]).decode() == PATHS[7]:
                f[2] = "false"
            rows.append("\t".join(f))
        self.fx.rewrite("record", "play-stages.tsv", rows)
        self.assert_fail("source_play_stage_success_missing")

    def test_absent_client_samples(self):
        self.fx.rewrite("record", "AF8_CLIENT_OBSERVATION_SAMPLES.tsv",
                        ["\t".join((p, "0", "0", "0", "0")) if p == PATHS[0] else client_row(p) for p in PATHS])
        self.assert_fail("missing_real_remote_sample")

    def test_missing_observer_evidence(self):
        (self.fx.record / "play-stages.tsv").unlink()
        code, gate = self.fx.run()
        self.assertNotEqual(code, 0)
        self.assertTrue(any("play_stages_missing" in f for f in gate["failures"]), gate["failures"])

    def test_summary_failure_closed(self):
        self.fx.rewrite("record", "case-summary.tsv",
                        [summary_row(p, status="FAIL" if p == PATHS[0] else "PASS") for p in PATHS])
        self.assert_fail("record:status=FAIL")

    def test_forged_decision_attribution(self):
        rows = (self.fx.record / "decision-events-with-path.tsv").read_text().splitlines()
        rows.append(decision_row("forge-behavior-v2:forged", 999))
        self.fx.rewrite("record", "decision-events-with-path.tsv", rows)
        code, gate = self.fx.run()
        self.assertNotEqual(code, 0)
        self.assertTrue(any("decision_path_evidence" in f for f in gate["failures"]), gate["failures"])


if __name__ == "__main__":
    unittest.main()
