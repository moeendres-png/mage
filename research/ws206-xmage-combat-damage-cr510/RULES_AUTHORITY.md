# WS206 Rules Authority (binding)

Official source: https://magic.wizards.com/en/rules (Wizards of the Coast).

Bound document (fetched live during execution):

- TXT: https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt
- File label: 20260819; document header: "These rules are effective as of August 7, 2026."
- The TXT edition is newer than the at-issuance August 7 DOCX/PDF pair and states
  the same August 7, 2026 effective date. Fresh official authority outranks the
  work-order summary; excerpts below are verbatim from the bound TXT.

## CR 510.1c (blocked attacker, multiple blockers)

> "If two or more creatures are blocking it, it assigns its combat damage to those
> creatures divided as its controller chooses among them."

Example in the rules (Elvish Regrower 4/3 vs 2/3 + 1/1) expressly permits all-to-either
and any split. No lethal ordering. No assignment order.

## CR 510.1d (blocker, multiple attackers)

> "If it's blocking two or more creatures, it assigns its combat damage divided as
> its controller chooses among them."

## CR 510.1e (complete-assignment legality)

> "Once a player has assigned combat damage from each attacking or blocking creature
> they control, the total damage assignment (not solely the damage assignment of any
> individual attacking or blocking creature) is checked to see if it complies with the
> above rules. If it doesn't, the combat damage assignment is illegal; the game returns
> to the moment before that player began to assign combat damage. (See rule 733,
> 'Handling Illegal Actions.')"

## CR 702.19b (trample)

> "The controller of an attacking creature with trample first assigns damage to the
> creature(s) blocking it. Once all those blocking creatures are assigned lethal damage,
> any excess damage is assigned as its controller chooses among those blocking creatures
> and the player, planeswalker, or battle the creature is attacking. When checking for
> assigned lethal damage, take into account damage already marked on the creature and
> damage from other creatures that's being assigned during the same combat damage step,
> but not any abilities or effects that might change the amount of damage that's actually
> dealt. The attacking creature's controller need not assign lethal damage to all those
> blocking creatures but in that case can't assign any damage to the player or planeswalker
> it's attacking."

Plus the two printed examples (shared-blocker split across two attackers; 6/6 green
trample vs 2/2 protection-from-green must assign at least 2 to the blocker).

## CR 702.2c (deathtouch)

> "Any nonzero amount of combat damage assigned to a creature by a source with deathtouch
> is considered to be lethal damage for the purposes of determining if excess damage
> is being dealt."

## CR 702.22j/k (banding controller exceptions)

- 702.22j: attacker blocked by a banding blocker (or qualifying bands-with-other pair)
  => defending player chooses the attacker's damage division (exception to 510.1c).
- 702.22k: blocker blocking a banding attacker (or qualifying pair) => active player
  chooses the blocker's damage division (exception to 510.1d).

## CR 510.4 / 702.4 / 702.7 (first/double strike)

Two combat damage steps when any first/double striker exists at step begin; only
first/double strikers assign in the first step; the rest (plus current double strikers)
assign in the second. Giving/removing first/double strike mid-step follows 702.7c/702.4c-d.

## CR 104.3a (concession)

> "A player can concede the game at any time."

Recorded for scope only. CONCESSION = OUT_OF_SCOPE (no implementation in WS206).

CURRENT_OFFICIAL_RULES_VERSION = TXT 20260819, effective August 7, 2026, via the
official Magic Rules page.
