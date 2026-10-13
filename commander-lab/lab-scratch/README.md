# Scratch runners for real-deck full games (lab repo, not production code)

Run from a commander-playtest-lab checkout with the bridge jar built
(`COMMANDER_LAB_XMAGE_FULL_GAME_BRIDGE_CMD="java -jar $PWD/engine-bridge/target/xmage-engine-bridge-0.1.0-SNAPSHOT.jar full-game"`).
- `batch.py out.jsonl n:seed ...`: twin full games with the 4 repo decks (4P/5P/6P), checks TERMINAL + semantic twin match.
- `batch_coll.py out.jsonl seed:slug,slug,...`: same with the collection coverage decks (data/coverage_decks/collection/).
- `seq.py n:seed:outfile`: saves semantic transcripts; `np_setup.py`/`fg.py`: shared setup helpers.
Run games one at a time (parallel JVMs caused contention); ~2-11 min per game.
After a repin, rerun these batches with decks that contain the new fork cards.
