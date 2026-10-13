import sys, json, time
sys.path.insert(0, "/home/user/commander-playtest-lab/scripts")
import run_real_4p_full_game_smoke as R
from commander_lab.engine.rules import full_game as fg
from commander_lab.engine.rules.project import load_rules_deck_snapshot
D="/tmp/claude-0/-home-user/37aff224-c556-5296-83b1-8cd62a1687e0/scratchpad/coll_decks/"
def setup(seed, slugs):
    base, _d, _p, _ = R.build_real_4p_setup(R.ROOT)
    decks = tuple(R._ensure_deck_hash(load_rules_deck_snapshot(D + s + ".json"))[0] for s in slugs)
    n = len(decks)
    pilots = tuple(R._binding(s, decks[s - 1]) for s in range(1, n + 1))
    scenario = base.model_copy(update={"seed": seed, "player_count": n, "candidate_id": decks[0].deck_id, "deck_hash": decks[0].deck_hash,
        "opponent_deck_ids": tuple(d.deck_id for d in decks[1:]), "scenario_id": f"scratch-coll-{n}p-{seed}"})
    return scenario, decks, pilots
out = open(sys.argv[1], "a")
for spec in sys.argv[2:]:
    seed, pod = spec.split(":"); seed = int(seed); slugs = pod.split(",")
    res = []
    for twin in (1, 2):
        sc, decks, pilots = setup(seed, slugs)
        t = time.time()
        try:
            r = fg.XmageFullGameRunner(cwd=R.ROOT).run(scenario=sc, decks=decks, pilots=pilots)
            res.append({"ok": True, "turn": r.result_payload.get("turn_number"), "winners": list(r.winner_seats), "decisions": r.decision_count,
                        "sem": r.semantic_transcript_sha256, "raw": r.raw_result_sha256, "secs": round(time.time()-t)})
        except Exception as e:
            res.append({"ok": False, "err": str(e)[:600], "secs": round(time.time()-t)})
        if not res[-1]["ok"]: break
    row = {"players": len(slugs), "seed": seed, "pod": slugs, "runs": res,
           "twin_semantic_match": len(res) == 2 and res[0]["ok"] and res[1]["ok"] and res[0]["sem"] == res[1]["sem"]}
    out.write(json.dumps(row) + "\n"); out.flush(); print(json.dumps(row)[:500], flush=True)
