import sys, json
sys.path.insert(0, "/tmp/claude-0/-home-user/37aff224-c556-5296-83b1-8cd62a1687e0/scratchpad")
import np_setup as b
fg = b.fg; R = b.R
for item in sys.argv[1:]:
    n, seed, name = item.split(":"); n, seed = int(n), int(seed)
    sc, decks, pilots = b.setup(n, seed)
    r = fg.XmageFullGameRunner(cwd=R.ROOT).run(scenario=sc, decks=decks, pilots=pilots)
    json.dump(fg.XmageFullGameRunner.semantic_transcript(r.result_payload), open(name, "w"), indent=1, sort_keys=True, default=str)
    print(item, r.semantic_transcript_sha256, flush=True)
