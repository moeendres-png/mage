# WS16 — Trigger / Replacement / Zone / SBA witness shard

This shard is deliberately fail-closed. It contains one executable, actual-card
pinned-Forge witness for `Replacement/Moved` and `Trigger/ChangesZone`, using
Jwar Isle Refuge's real script. Its state assertions distinguish the replacement
entry modification from later trigger stack placement and resolution.

The remaining WS14-owned primitives are listed as `PARTIAL` with an exact
absence-of-witness blocker. They are not inferred from the two exercised paths,
from parse/source presence, or from prior global qualification.
