#!/usr/bin/env python3
"""Prepare the remaining WS33H actual-card harness without direct resolution/target injection.

The historical WS30 source remains metadata/test-fixture input only. First reuse the
already-qualified Generation-2 compatibility transformations, including canonical
rule-relation trace serialization, then replace historical qualification shortcuts
that are not admissible for the H remainder.

The custom controller is fail-closed: every targeted choice must have an explicit
scripted expected entity in record mode or an exact recorded response in replay mode;
there is no AI/default/random/cancel fallback.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_H_REST_HARNESS_PREP=FAIL " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    base_preparer = Path(__file__).with_name("ws33_prepare_h_state_harness.py")
    require(base_preparer.is_file(), "missing Generation-2 H-state preparer")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(base_preparer), "--source", str(args.source), "--out", str(args.out)],
        check=True,
    )
    s = args.out.read_text(encoding="utf-8")
    s = replace_once(s, "import forge.game.ability.AbilityUtils;\n", "", "obsolete AbilityUtils import")

    # AttackRestriction/AttackRequirement do not define semantic toString() methods at
    # the pinned Forge revision. Serializing the objects directly therefore embeds
    # per-JVM identity hashes (Class@hex) and makes a semantically identical replay look
    # different. Read only Forge-owned public constraint state and serialize it
    # deterministically; do not infer or reimplement combat legality here.
    old_constraints = '''    private static String restrictionsRequirements(Combat combat) {\n        List<String> out=new ArrayList<>();\n        combat.getAttackConstraints().getRestrictions().entrySet().stream().sorted(Comparator.comparing(e->e.getKey().getName())).forEach(e->out.add("R:"+e.getKey().getName()+"="+e.getValue()));\n        combat.getAttackConstraints().getRequirements().entrySet().stream().sorted(Comparator.comparing(e->e.getKey().getName())).forEach(e->out.add("Q:"+e.getKey().getName()+"="+e.getValue()));\n        return String.join("|",out);\n    }\n'''
    canonical_constraints = '''    private static String restrictionsRequirements(Combat combat) {\n        List<String> out=new ArrayList<>();\n        combat.getAttackConstraints().getRestrictions().entrySet().stream().sorted(Comparator.comparing(e->e.getKey().getName())).forEach(e->{\n            List<String> types=new ArrayList<>();\n            for (var type:e.getValue().getTypes()) types.add(type.name());\n            types.sort(String::compareTo);\n            out.add("R:"+e.getKey().getName()+"=types["+String.join(",",types)+"]");\n        });\n        combat.getAttackConstraints().getRequirements().entrySet().stream().sorted(Comparator.comparing(e->e.getKey().getName())).forEach(e->\n            out.add("Q:"+e.getKey().getName()+"=hasRequirement="+e.getValue().hasRequirement()));\n        return String.join("|",out);\n    }\n'''
    s = replace_once(s, old_constraints, canonical_constraints, "canonical combat constraint serialization")

    anchor = '''        void expectEntityChoice(GameEntity entity) {\n            if (expectedEntityChoice != null) throw new IllegalStateException("unconsumed expected entity choice");\n            expectedEntityChoice = entity;\n        }\n'''
    target_boundary = anchor + '''        private final java.util.Deque<GameEntity> expectedTargets = new java.util.ArrayDeque<>();\n        private String decisionPath;\n        private int decisionIndex;\n        void setDecisionPath(String path) {\n            if (!expectedTargets.isEmpty()) throw new IllegalStateException("unconsumed target expectation before decision path");\n            decisionPath = path; decisionIndex = 0;\n        }\n        void expectTarget(GameEntity entity) {\n            if (entity == null) throw new IllegalArgumentException("null expected target");\n            expectedTargets.addLast(entity);\n        }\n        void finishDecisionPath() {\n            if (!expectedTargets.isEmpty()) throw new IllegalStateException("unconsumed expected targets: " + expectedTargets.size());\n            decisionPath = null; decisionIndex = 0;\n        }\n        private static String semanticEntity(GameEntity entity) {\n            if (entity instanceof Player) return "PLAYER:" + entity.getName();\n            if (entity instanceof Card) {\n                Card c=(Card)entity;\n                String owner=c.getOwner()==null?"":c.getOwner().getName();\n                String controller=c.getController()==null?"":c.getController().getName();\n                return "CARD:"+c.getName()+":OWNER="+owner+":CONTROLLER="+controller;\n            }\n            return entity.getClass().getSimpleName().toUpperCase()+":"+entity.getName();\n        }\n        private String replayResponse(String path, int index) {\n            String replay=System.getProperty("ws33.h.replay.decisions");\n            if (replay==null || replay.isBlank()) return null;\n            try {\n                for (String line:Files.readAllLines(Path.of(replay),StandardCharsets.UTF_8)) {\n                    if (line.isBlank()) continue;\n                    String[] parts=line.split("\\t",3);\n                    if (parts.length!=3) throw new IllegalStateException("malformed replay decision line");\n                    if (parts[0].equals(path) && Integer.parseInt(parts[1])==index)\n                        return new String(java.util.Base64.getDecoder().decode(parts[2]),StandardCharsets.UTF_8);\n                }\n            } catch(IOException e) { throw new RuntimeException(e); }\n            throw new IllegalStateException("missing replay response for "+path+"#"+index);\n        }\n        private void appendDecision(String path, int index, List<GameEntity> legal, String response) {\n            if (path==null) return;\n            String output=System.getProperty("ws33.h.decision.path");\n            if (output==null || output.isBlank()) throw new IllegalStateException("decision evidence path not configured");\n            List<String> options=new ArrayList<>(); for(GameEntity e:legal) options.add(semanticEntity(e)); options.sort(String::compareTo);\n            StringBuilder arr=new StringBuilder("["); for(int i=0;i<options.size();i++){if(i>0)arr.append(',');arr.append('\\"').append(esc(options.get(i))).append('\\"');} arr.append(']');\n            String json="{\\"path_id\\":\\""+esc(path)+"\\",\\"decision_index\\":"+index+",\\"decision_kind\\":\\"TARGET_SELECTION\\",\\"actor\\":\\""+esc(player.getName())+"\\",\\"principal\\":\\""+esc(player.getName())+"\\",\\"visibility_scope\\":\\"PRINCIPAL_ONLY\\",\\"legal_options\\":"+arr+",\\"response_semantic_value\\":\\""+esc(response)+"\\",\\"validation_result\\":\\"ACCEPTED\\",\\"fallback_used\\":false}"+System.lineSeparator();\n            try { Path p=Path.of(output); if(p.getParent()!=null)Files.createDirectories(p.getParent()); Files.writeString(p,json,StandardCharsets.UTF_8,StandardOpenOption.CREATE,StandardOpenOption.APPEND); }\n            catch(IOException e){throw new RuntimeException(e);}\n        }\n        @Override public boolean chooseTargetsFor(SpellAbility currentAbility) {\n            forge.game.spellability.TargetRestrictions tgt=currentAbility.getTargetRestrictions();\n            if (tgt==null) return true;\n            if (!currentAbility.getTargets().isEmpty()) throw new IllegalStateException("pre-populated targets are forbidden in WS33 H-rest");\n            int min=tgt.getMinTargets(currentAbility.getHostCard(),currentAbility);\n            int max=tgt.getMaxTargets(currentAbility.getHostCard(),currentAbility);\n            if (min>1 || max<1) throw new IllegalStateException("H-rest scripted one-target choice is outside Forge bounds: min="+min+" max="+max);\n            List<GameEntity> legal=new ArrayList<>(tgt.getAllCandidates(currentAbility));\n            legal.sort(Comparator.comparing(Ws30Controller::semanticEntity));\n            if (legal.isEmpty()) throw new IllegalStateException("Forge emitted no legal targets");\n            GameEntity scripted=expectedTargets.pollFirst();\n            if (scripted==null) throw new IllegalStateException("unexpected discretionary target choice for "+decisionPath);\n            String expected=semanticEntity(scripted);\n            String replay=decisionPath==null?null:replayResponse(decisionPath,decisionIndex);\n            String response=replay==null?expected:replay;\n            if (replay!=null && !expected.equals(replay)) throw new IllegalStateException("replay response disagrees with fixture expectation: expected="+expected+" replay="+replay);\n            GameEntity chosen=null; int matches=0;\n            for(GameEntity candidate:legal) if(semanticEntity(candidate).equals(response)){chosen=candidate;matches++;}\n            if(matches!=1) throw new IllegalStateException("recorded/scripted target not uniquely Forge-legal: "+response+" matches="+matches);\n            currentAbility.getTargets().add(chosen);\n            if(!currentAbility.isTargetNumberValid()) throw new IllegalStateException("Forge target count invalid after authoritative selection");\n            appendDecision(decisionPath,decisionIndex,legal,response);\n            decisionIndex++;\n            return true;\n        }\n'''
    s = replace_once(s, anchor, target_boundary, "controller target boundary")

    old_from_svar = '''        SpellAbility sa=AbilityFactory.getAbility(definition,host); sa.setActivatingPlayer(activator);\n        if (targets!=null) for (GameEntity target:targets) sa.getTargets().add(target); return sa;\n'''
    new_from_svar = '''        SpellAbility sa=AbilityFactory.getAbility(definition,host); sa.setActivatingPlayer(activator);\n        if (targets!=null) for (GameEntity target:targets) ((Ws30Controller)activator.getController()).expectTarget(target); return sa;\n'''
    s = replace_once(s, old_from_svar, new_from_svar, "SVar target expectation")

    old_resolve = '''    private void resolve(Fixture f,SpellAbility sa) { AbilityUtils.resolve(sa); f.game.getAction().checkStateEffects(true); resolvePending(f); }\n'''
    new_resolve = '''    private void resolve(Fixture f,SpellAbility sa) {\n        Ws30Controller ctl=(Ws30Controller)sa.getActivatingPlayer().getController();\n        SpellAbility cur=sa;\n        while(cur!=null){\n            if(cur.getActivatingPlayer()==null)cur.setActivatingPlayer(sa.getActivatingPlayer());\n            if(cur.getTargetRestrictions()!=null){\n                if(!cur.getActivatingPlayer().getController().chooseTargetsFor(cur))throw new IllegalStateException("authoritative target selection rejected");\n            }\n            cur=cur.getSubAbility();\n        }\n        ctl.finishDecisionPath();\n        f.game.getStack().add(sa);\n        while(!f.game.getStack().isEmpty())f.game.getStack().resolveStack();\n        f.game.getAction().checkStateEffects(true); resolvePending(f);\n    }\n'''
    s = replace_once(s, old_resolve, new_resolve, "normal stack resolution")

    goad_anchor = '''        Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card target=putPermanent(f,p0,p0,"Grizzly Bears"); target.setSickness(false);\n        Card source=rootApi?looseCard(p1,sourceName):putPermanent(f,p1,p1,sourceName); SpellAbility sa;\n'''
    goad_new = '''        Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card target=putPermanent(f,p0,p0,"Grizzly Bears"); target.setSickness(false);\n        ((Ws30Controller)p1.getController()).setDecisionPath(path);\n        Card source=rootApi?looseCard(p1,sourceName):putPermanent(f,p1,p1,sourceName); SpellAbility sa;\n'''
    s = replace_once(s, goad_anchor, goad_new, "Goad decision-path binding")

    hydra_old = '''{ Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card h=putPermanent(f,p0,p0,"Voracious Hydra"),b=putPermanent(f,p1,p1,"Grizzly Bears"); resolve(f,fromSVar(h,"DBFight",p0,b)); Assert.assertEquals(h.getZone().getZoneType(),ZoneType.Graveyard);'''
    hydra_new = '''{ Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card h=putPermanent(f,p0,p0,"Voracious Hydra"),b=putPermanent(f,p1,p1,"Grizzly Bears"); ((Ws30Controller)p0.getController()).setDecisionPath("forge-behavior-v2:554fc179d6b92c7929aaf32b42866ef9ebfbb865"); resolve(f,fromSVar(h,"DBFight",p0,b)); Assert.assertEquals(h.getZone().getZoneType(),ZoneType.Graveyard);'''
    s = replace_once(s, hydra_old, hydra_new, "Voracious Hydra decision-path binding")

    throne_old = '''{ Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card cmd=commanderOnBattlefield(f,p0),victim=putPermanent(f,p1,p1,"Memnite"),spell=looseCard(p0,"Fight for the Throne"); SpellAbility root=topLevel(spell,ApiType.PutCounter,p0); root.getTargets().add(cmd); Assert.assertNotNull(root.getSubAbility()); root.getSubAbility().getTargets().add(victim); resolve(f,root); resolvePending(f);'''
    throne_new = '''{ Fixture f=fixture(); Player p0=f.p(0),p1=f.p(1); Card cmd=commanderOnBattlefield(f,p0),victim=putPermanent(f,p1,p1,"Memnite"),spell=looseCard(p0,"Fight for the Throne"); SpellAbility root=topLevel(spell,ApiType.PutCounter,p0); Ws30Controller ctl=(Ws30Controller)p0.getController(); ctl.setDecisionPath("forge-behavior-v2:945cb309bfe37e292fbecc172efa4789ff1156d1"); ctl.expectTarget(cmd); Assert.assertNotNull(root.getSubAbility()); ctl.expectTarget(victim); resolve(f,root); resolvePending(f);'''
    s = replace_once(s, throne_old, throne_new, "Fight for the Throne authoritative targets")

    require("AbilityUtils.resolve(" not in s, "direct AbilityUtils.resolve remains")
    forbidden = [
        line.strip() for line in s.splitlines()
        if ".getTargets().add(" in line and "currentAbility.getTargets().add(chosen)" not in line
    ]
    require(not forbidden, "manual target injection remains: " + " | ".join(forbidden[:4]))
    require(s.count("currentAbility.getTargets().add(chosen)") == 1, "authoritative controller assignment marker missing/duplicated")
    require("f.game.getStack().add(sa);" in s and "f.game.getStack().resolveStack();" in s, "normal stack route missing")
    require("AttackRestriction@" not in s and "AttackRequirement@" not in s, "identity-based combat constraint serialization remains")
    require("=types[" in s and "=hasRequirement=" in s, "canonical combat constraint markers missing")

    args.out.write_text(s, encoding="utf-8")
    print("WS33_H_REST_HARNESS_PREP=PASS direct_resolution=0 manual_test_target_injection=0 target_source=TargetRestrictions#getAllCandidates replay_mode=TAPE_DRIVEN combat_constraint_trace=CANONICAL_FORGE_STATE")


if __name__ == "__main__":
    main()
