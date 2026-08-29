from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


materializer = load_module("ws14_materialize", HERE / "ws14_materialize.py")
witness_validator = load_module("ws14_validate_witness", HERE / "ws14_validate_witness.py")


class PrimitiveContractTests(unittest.TestCase):
    def test_owner_family_is_unique_and_closed(self):
        samples = [
            ("ABILITY_API", "Shuffle"),
            ("ABILITY_API", "Fight"),
            ("ABILITY_API", "Clone"),
            ("ABILITY_API", "Destroy"),
            ("ABILITY_API", "Draw"),
            ("TRIGGER", "ChangesZone"),
            ("REPLACEMENT", "Moved"),
            ("STATIC_MODE", "Continuous"),
            ("STATIC_MODE", "CantAttack"),
            ("COST", "AbilityFactory.parseAbilityCost"),
            ("TARGETING", "ValidTgts"),
            ("ABILITY_RECORD", "SP"),
        ]
        for domain, token in samples:
            owner = materializer.owner_for(domain, token)
            self.assertIn(owner, materializer.OWNER_FAMILIES)
            self.assertIsInstance(owner, str)

    def test_primitive_id_is_deterministic_and_semantic_conflicts_fail(self):
        registry = {"path": "ApiType.java", "sha256_bytes": "a" * 64}
        desc = materializer.primitive_descriptor(
            "ABILITY_API",
            "Draw",
            "forge.game.ability.effects.DrawEffect",
            registry,
        )
        self.assertEqual(
            desc["primitive_id"],
            materializer.primitive_id(
                "ABILITY_API", "Draw", "forge.game.ability.effects.DrawEffect"
            ),
        )
        catalog = {}
        materializer.add_primitive(catalog, desc)
        materializer.add_primitive(catalog, dict(desc))
        conflicting = dict(desc)
        conflicting["owner_family"] = "HIDDEN_RNG_REPLAY"
        with self.assertRaises(ValueError):
            materializer.add_primitive(catalog, conflicting)

    def test_unknown_binding_is_explicit_and_never_owned(self):
        item = materializer.unknown(
            line_no=7,
            directive="KEYWORD",
            token="KEYWORD",
            value="Some Keyword",
            reason="no direct dispatch",
        )
        self.assertEqual(item["binding_status"], "UNKNOWN")
        self.assertEqual(item["evidence_class"], "UNKNOWN")
        self.assertIsNone(item["primitive_id"])
        self.assertIsNone(item["owner_family"])

    def test_extracts_engine_dispatch_not_card_name_similarity(self):
        registries = {
            "ABILITY_API": {"draw": "forge.game.ability.effects.DrawEffect"},
            "TRIGGER": {"changeszone": "forge.game.trigger.TriggerChangesZone"},
            "REPLACEMENT": {"moved": "forge.game.replacement.ReplaceMoved"},
            "STATIC_MODE": {"continuous": "forge.game.staticability.StaticAbilityMode#Continuous"},
        }
        meta = {
            key: {"path": f"{key}.java", "sha256_bytes": "a" * 64}
            for key in registries
        }
        ability_factory = {"path": "AbilityFactory.java", "sha256_bytes": "b" * 64}
        script = "\n".join(
            [
                "ManaCost:1 U",
                "A:SP$ Draw | ValidTgts$ Player | SpellDescription$ Draw a card.",
                "T:Mode$ ChangesZone | Destination$ Graveyard | Execute$ Trig",
                "R:Event$ Moved | Destination$ Exile | ReplaceWith$ Repl",
                "S:Mode$ Continuous | Affected$ Creature.YouCtrl | AddPower$ 1",
                "K:Flying",
            ]
        )
        catalog = {}
        resolved, unresolved = materializer.extract_bindings(
            script, registries, meta, ability_factory, catalog
        )
        resolved_domains = {catalog[item["primitive_id"]]["dispatch_domain"] for item in resolved}
        self.assertTrue({"ABILITY_API", "ABILITY_RECORD", "COST", "TARGETING", "TRIGGER", "REPLACEMENT", "STATIC_MODE"}.issubset(resolved_domains))
        self.assertTrue(any(item["source_directive"] == "KEYWORD" for item in unresolved))
        self.assertFalse(any("oracle_name" in json.dumps(item) for item in resolved))


class WitnessContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(
            (HERE.parent / "WS14_WITNESS_ABI.schema.json").read_text(encoding="utf-8")
        )

    def test_positive_fixture_validates(self):
        witness = json.loads(
            (HERE / "fixtures" / "witness-positive.json").read_text(encoding="utf-8")
        )
        witness_validator.validate_witness(self.schema, witness)

    def test_negative_fixture_is_rejected_semantically(self):
        witness = json.loads(
            (HERE / "fixtures" / "witness-negative-missing-exercise.json").read_text(encoding="utf-8")
        )
        with self.assertRaises(ValueError):
            witness_validator.validate_witness(self.schema, witness)


if __name__ == "__main__":
    unittest.main()
