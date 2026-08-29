# WS17 official-rules adjudication

Rules citations are to the current official Magic: The Gathering Comprehensive Rules.  They
are semantic authority for these witnesses; Forge is only the pinned implementation under test.

- Continuous effects and layer ordering: CR 604.1, 611.2c, 613.1, 613.1d, 613.1f, 613.1g.
- Tokens and copies: CR 111.2, 707.2, 707.9.
- Control of permanents: CR 110.2 and CR 613.1f.
- Counters / altered status: CR 122.1 and 122.1b.
- Transforming double-faced cards: CR 701.28a and 712.8.

The test scenarios assert the live engine object state both before and after resolution.  No
Forge/XMage-majority inference is used.  A future discovered conflict must be recorded as a
rule-adjudicated divergence, not silently accepted from engine behavior.
