# Card smoke harness (scratch prototype)

`CardSmoke.java` casts each card once in a prepared 2-player position through the lab's
engine bridge and writes one JSON row per card (~0.3 s/card). Inputs/results of the
2026-10-12 run: `all.txt`/`all.jsonl` (owner collection, 1176/1254 ok), `precon.txt`/
`precon.jsonl` (precons, 480/539 ok), German report `smoke_report_2026-10-12.md`.

Build (B = commander-playtest-lab `engine-bridge` module after `mvn test-compile`;
cp.txt from `mvn -o dependency:build-classpath -Dmdep.includeScope=test` there):

    javac -cp "$B/target/classes:$B/target/test-classes:$(cat cp.txt)" -d cls CardSmoke.java
    # run from a dir containing db/cards.h2.mv.db (XMage card DB of the jar under test)
    java -Xmx4g -cp "cls:$B/target/classes:$B/target/test-classes:$(cat cp.txt)" \
      org.commanderlab.xmage.CardSmoke cards.txt out.jsonl

Known gaps: no diacritic folding when restoring cards (4 false UNKNOWNs: Grishnákh,
Gríma, Lord of the Nazgûl, Troll of Khazad-dûm); no numeric target_amount, multi-select,
counterspell setup; only basic lands + no artifact mana in the prepared position.
To test the fork cards: build this branch's jars, regenerate the card DB, rerun precon.txt.
