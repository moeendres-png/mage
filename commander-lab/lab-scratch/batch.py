import sys, json, time
sys.path.insert(0, "/home/user/commander-playtest-lab/scripts")
import run_real_4p_full_game_smoke as R
from commander_lab.engine.rules import full_game as fg
def setup(n, seed):
    scenario, decks, pilots, _ = R.build_real_4p_setup(R.ROOT)
    extra = [R._ensure_deck_hash(d.model_copy(update={'deck_id': d.deck_id + '-copy', 'deck_hash': None}))[0] for d in (decks[2], decks[3])][: n - 4]
    decks = tuple(decks) + tuple(extra)
    pilots = tuple(R._binding(s, decks[s - 1]) for s in range(1, n + 1))
    scenario = scenario.model_copy(update={"seed": seed, "player_count": n,
        "opponent_deck_ids": tuple(d.deck_id for d in decks[1:]), "scenario_id": f"scratch-real-{n}p-{seed}"})
    return scenario, decks, pilots
out = open(sys.argv[1], "a")
for spec in sys.argv[2:]:
    n, seed = map(int, spec.split(":"))
    res = []
    for twin in (1, 2):
        sc, decks, pilots = setup(n, seed)
        t = time.time()
        try:
            r = fg.XmageFullGameRunner(cwd=R.ROOT).run(scenario=sc, decks=decks, pilots=pilots)
            res.append({"ok": True, "turn": r.result_payload.get("turn_number"), "winners": list(r.winner_seats), "decisions": r.decision_count,
                        "sem": r.semantic_transcript_sha256, "raw": r.raw_result_sha256, "secs": round(time.time()-t)})
        except Exception as e:
            res.append({"ok": False, "err": str(e)[:300], "secs": round(time.time()-t)})
        if not res[-1]["ok"]: break
    row = {"players": n, "seed": seed, "runs": res,
           "twin_semantic_match": len(res) == 2 and res[0]["ok"] and res[1]["ok"] and res[0]["sem"] == res[1]["sem"],
           "twin_raw_match": len(res) == 2 and res[0]["ok"] and res[1]["ok"] and res[0]["raw"] == res[1]["raw"]}
    out.write(json.dumps(row) + "\n"); out.flush(); print(json.dumps(row)[:400], flush=True)
