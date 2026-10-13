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
