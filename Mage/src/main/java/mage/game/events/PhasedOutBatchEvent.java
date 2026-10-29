package mage.game.events;

/**
 * All PHASED_OUT events of permanents that phased out at the same time.
 */
public class PhasedOutBatchEvent extends BatchEvent<GameEvent> {

    public PhasedOutBatchEvent(GameEvent firstEvent) {
        super(EventType.PHASED_OUT_BATCH, false, false, false, firstEvent);
    }

}
