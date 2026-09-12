# WS83 Source Lock

- repository: moeendres-png/mage
- worktree (FOUNDRY_WORKTREE): /home/moeen/code/ws83-xmage-cr61412-entry-applicability-remediation
- branch: ws83/xmage-cr61412-entry-applicability-remediation-20260912
- WS81 base evidence HEAD: aeaa7214ffc3e53ed132bd7078babf4a267d7c51
- WS81 base tree (HEAD^{tree}): d5bd67ab07c4f04b0923414b292636874c752208
- accepted XMage ancestor (unchanged pin): 7135d5e85ddb4c8aa4b49b4192ca51947c822704
- WS81 production engine changes: NONE (one test + four evidence files only)

Authority:

- CPL repository: moeendres-png/commander-playtest-lab
- CPL main merge: 79c5af1fcb858451726272b3774828f238ab6755
- CPL tree: 2026c4c33616fe95c9a8f50e3772193216f1b6d9
- artifacts: qualification/ws79-h01-authority-remediation/H01_CORRECTED_CASES.json,
  qualification/ws79-h01-authority-remediation/H01_RULES_ADJUDICATION.md
- old H01 oracle: SUPERSEDED

Verification (fresh, this workstream):

- `git rev-parse HEAD` => aeaa7214ffc3e53ed132bd7078babf4a267d7c51
- `git rev-parse HEAD^{tree}` => d5bd67ab07c4f04b0923414b292636874c752208
- `git branch --show-current` => ws83/xmage-cr61412-entry-applicability-remediation-20260912
- CPL `git fetch origin 79c5af1...` + `git rev-parse FETCH_HEAD` => 79c5af1...;
  `git rev-parse FETCH_HEAD^{tree}` => 2026c4c33616fe95c9a8f50e3772193216f1b6d9
- pre-fix `mvn -pl Mage.Tests test -Dtest=WS81H01CorrectedTest` => 3 run, 1 failure (A red, B/C green)

Verdicts: SOURCE_LOCK = PASS. AUTHORITY_LOCK = PASS. No engine pin change.
