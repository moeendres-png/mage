#!/usr/bin/env python3
"""Port the historical WS30 witness harness to the exact pinned Forge API.

The transformations are the same generic compatibility corrections proven by the
historical WS30 workflow. They affect only the qualification harness; production
Forge sources are never modified here.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def must_replace(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    actual = text.count(old)
    if actual < count:
        raise SystemExit(f"WS33_H_HARNESS_PREP=FAIL missing {label}: expected >= {count}, got {actual}")
    return text.replace(old, new, count)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    s = args.source.read_text(encoding="utf-8")

    s = must_replace(s, "import forge.LobbyPlayer;\n", "import forge.LobbyPlayer;\nimport forge.GuiDesktop;\n", "GuiDesktop import")
    s = s.replace("import forge.game.card.CardCollectionView;\n", "")
    s = must_replace(s, "import forge.game.player.IGameEntitiesFactory;\n", "import forge.game.player.DelayedReveal;\nimport forge.game.player.IGameEntitiesFactory;\n", "DelayedReveal import")
    s = must_replace(s, "import forge.item.PaperCard;\n", "import forge.item.PaperCard;\nimport forge.gui.GuiBase;\nimport forge.model.FModel;\n", "GuiBase/FModel imports")
    s = must_replace(s, "import forge.util.Localizer;\n", "import forge.util.Localizer;\nimport forge.util.collect.FCollectionView;\n", "FCollectionView import")

    init = '            Localizer.getInstance().initialize("en-US", dir(res.resolve("languages")));\n'
    bootstrap = '''            Localizer.getInstance().initialize("en-US", dir(res.resolve("languages")));\n            if (GuiBase.getInterface() == null) GuiBase.setInterface(new GuiDesktop());\n            FModel.loadDynamicGamedata();\n            Assert.assertTrue(forge.card.CardType.Constant.LOADED.isSet(), "Forge dynamic type registry not loaded");\n'''
    s = must_replace(s, init, bootstrap, "Forge dynamic-data bootstrap")

    controller_ctor = '        Ws30Controller(Game game, Player player, LobbyPlayer lobbyPlayer) { super(game, player, lobbyPlayer); }\n'
    controller_choice = '''        private GameEntity expectedEntityChoice;\n        Ws30Controller(Game game, Player player, LobbyPlayer lobbyPlayer) { super(game, player, lobbyPlayer); }\n        void expectEntityChoice(GameEntity entity) {\n            if (expectedEntityChoice != null) throw new IllegalStateException("unconsumed expected entity choice");\n            expectedEntityChoice = entity;\n        }\n        @Override public <T extends GameEntity> T chooseSingleEntityForEffect(FCollectionView<T> optionList, DelayedReveal delayedReveal, SpellAbility sa, String title, boolean isOptional, Player relatedPlayer, Map<String,Object> params) {\n            if (delayedReveal != null) reveal(delayedReveal);\n            GameEntity expected = expectedEntityChoice;\n            if (expected == null) throw new IllegalStateException("unexpected discretionary entity choice: " + title);\n            expectedEntityChoice = null;\n            for (T option : optionList) if (option.equals(expected)) return option;\n            throw new IllegalStateException("expected entity is not Forge-legal: " + expected + " options=" + optionList);\n        }\n'''
    s = must_replace(s, controller_ctor, controller_choice, "entity-choice controller")

    old_put = '        controller.getZone(ZoneType.Battlefield).add(card); f.game.getTriggerHandler().registerActiveTrigger(card,false); return card;\n'
    new_put = '        f.game.getAction().changeZone(null,controller.getZone(ZoneType.Battlefield),card,null,null); return card;\n'
    s = must_replace(s, old_put, new_put, "rules-core permanent entry")

    force = '''    private void forceAttack(Fixture f,Player p,Card creature) {\n        Card aura=putPermanent(f,p,p,"Furor of the Bitten"); aura.attachToEntity(creature,null,true); creature.setSickness(false);\n    }\n'''
    aura_helper = '''    private Card putPermanentMaybeAura(Fixture f, Player owner, Player controller, String name, Card target) {\n        Card card=Card.fromPaperCard(paper(name),owner); card.setController(controller,0);\n        if (!card.isAura()) return putPermanent(f,owner,controller,name);\n        Assert.assertTrue(card.hasKeyword(forge.game.keyword.Keyword.ENCHANT), "Aura lacks Forge ENCHANT keyword: "+name);\n        Assert.assertNotNull(card.getCurrentState().getAuraSpell(), "Aura lacks Forge AuraSpell: "+name);\n        f.game.copyLastState();\n        boolean lkiLegal=f.game.getLastStateBattlefield().anyMatch(forge.game.card.CardPredicates.canBeAttached(card,null));\n        boolean currentLegal=f.game.getCardsIn(ZoneType.Battlefield).anyMatch(forge.game.card.CardPredicates.canBeAttached(card,null));\n        Assert.assertTrue(lkiLegal, "No Forge-legal LKI Aura attachment for "+name);\n        Assert.assertTrue(currentLegal, "No Forge-legal current Aura attachment for "+name);\n        ((Ws30Controller)controller.getController()).expectEntityChoice(target);\n        controller.getZone(ZoneType.Hand).add(card);\n        Card entered=f.game.getAction().changeZone(controller.getZone(ZoneType.Hand),controller.getZone(ZoneType.Battlefield),card,null,null);\n        Assert.assertNotNull(entered); Assert.assertTrue(entered.isAura()); Assert.assertEquals(entered.getEntityAttachedTo(),target);\n        f.game.getAction().checkStateEffects(true);\n        Assert.assertTrue(entered.isInPlay()); Assert.assertEquals(entered.getEntityAttachedTo(),target);\n        return entered;\n    }\n    private void forceAttack(Fixture f,Player p,Card creature) {\n        Card aura=putPermanentMaybeAura(f,p,p,"Furor of the Bitten",creature);\n        Assert.assertTrue(aura.isAura()); Assert.assertEquals(aura.getEntityAttachedTo(),creature); creature.setSickness(false);\n    }\n'''
    s = must_replace(s, force, aura_helper, "Aura rules-core placement")

    sca = 'Card source=putPermanent(f,p1,p1,sourceName); if(source.isAura()) source.attachToEntity(attacker,null,true);'
    s = must_replace(s, sca, 'Card source=putPermanentMaybeAura(f,p1,p1,sourceName,attacker);', "static Aura placement")

    marker = '    private Pair<Map<Card,GameEntity>,Integer> legal(Combat c){return c.getAttackConstraints().getLegalAttackers();}\n'
    helper = '''    private Combat beginCombat(Fixture f, Player attacker) {\n        f.game.getPhaseHandler().devModeSet(PhaseType.MAIN1, attacker);\n        f.game.getAction().checkStateEffects(true);\n        Assert.assertTrue(f.game.getPhaseHandler().devAdvanceToPhase(PhaseType.COMBAT_BEGIN));\n        Combat combat=f.game.getPhaseHandler().getCombat();\n        Assert.assertNotNull(combat);\n        return combat;\n    }\n'''
    s = must_replace(s, marker, helper + marker, "PhaseHandler combat helper")
    combat_count = s.count("new Combat(p0)")
    if combat_count < 1:
        raise SystemExit("WS33_H_HARNESS_PREP=FAIL no direct Combat constructor to normalize")
    s = s.replace("new Combat(p0)", "beginCombat(f,p0)")

    ghost = 'Cost cost=CombatUtil.getAttackCost(f.game,bear,p1); Assert.assertNotNull(cost); var e=legal(c); Assert.assertFalse(e.getLeft().containsKey(bear));'
    ghost_fixed = '''Cost cost=CombatUtil.getAttackCost(f.game,bear,p1); Assert.assertNotNull(cost); var e=legal(c);\n            Assert.assertTrue(e.getLeft().containsKey(bear));\n            GameEntity chosen=e.getLeft().get(bear);\n            Assert.assertNotEquals(chosen,p1);\n            Assert.assertNull(CombatUtil.getAttackCost(f.game,bear,chosen));'''
    s = must_replace(s, ghost, ghost_fixed, "multiplayer Ghostly Prison semantics")
    s = s.replace('"unpaid attacker omitted","not-applicable","no combat damage","Forge exposes attack cost and requirements do not bypass it"',
                  '"taxed defender excluded; attacker redirected by rules core","not-applicable","no combat damage","Forge exposes defender-scoped attack cost and selects an untaxed legal defender"', 1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(s, encoding="utf-8")
    print(f"WS33_H_HARNESS_PREP=PASS phase_handler_substitutions={combat_count}")


if __name__ == "__main__":
    main()
