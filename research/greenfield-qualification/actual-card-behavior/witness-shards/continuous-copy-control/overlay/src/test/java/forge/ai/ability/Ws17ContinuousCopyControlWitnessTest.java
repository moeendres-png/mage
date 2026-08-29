package forge.ai.ability;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.ability.AbilityFactory;
import forge.game.ability.AbilityUtils;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.zone.ZoneType;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.testng.AssertJUnit.assertEquals;
import static org.testng.AssertJUnit.assertFalse;
import static org.testng.AssertJUnit.assertSame;
import static org.testng.AssertJUnit.assertTrue;

/**
 * WS17 runtime witnesses.  This file is copied into the exact pinned Forge checkout by the
 * WS17 workflow; it is not a replacement implementation and does not select game actions.
 * Each effect is resolved by Forge's own AbilityFactory/AbilityUtils path and the test records
 * state observed from the live Game/Card model only after TestNG state assertions have passed.
 */
public class Ws17ContinuousCopyControlWitnessTest extends AITest {
    private static final String TRACE_PROPERTY = "ws17.trace";

    private void resolve(final String definition, final Card host, final Player activator, final Card target) {
        final SpellAbility ability = AbilityFactory.getAbility(definition, host);
        ability.setActivatingPlayer(activator);
        if (target != null) {
            ability.getTargets().add(target);
        }
        AbilityUtils.resolve(ability);
        activator.getGame().getAction().checkStateEffects(true);
    }

    private void trace(final String primitive, final String scenario, final String before, final String after) {
        String destination = System.getProperty(TRACE_PROPERTY);
        if (destination == null || destination.isBlank()) {
            destination = System.getenv("WS17_TRACE");
        }
        if (destination == null || destination.isBlank()) {
            throw new IllegalStateException("WS17 trace destination was not supplied");
        }
        final String row = primitive + "\t" + scenario + "\t" + before + "\t" + after + System.lineSeparator();
        try {
            final Path path = Path.of(destination);
            Files.createDirectories(path.getParent());
            Files.writeString(path, row, java.nio.file.StandardOpenOption.CREATE,
                    java.nio.file.StandardOpenOption.APPEND);
        } catch (IOException e) {
            throw new AssertionError("unable to retain WS17 runtime state trace", e);
        }
    }

    @Test
    public void pumpAndPumpAllChangeLivePowerAndToughness() {
        final Game game = initAndCreateGame();
        final Player me = game.getPlayers().get(0);
        final Card first = addCard("Runeclaw Bear", me);
        final Card second = addCard("Grizzly Bears", me);

        resolve("DB$ Pump | ValidTgts$ Creature | NumAtt$ 2 | NumDef$ 3 | Duration$ Permanent", first, me, first);
        assertEquals("single-target Pump updates power", 4, first.getNetPower());
        assertEquals("single-target Pump updates toughness", 5, first.getNetToughness());
        trace("forge-primitive-v1:3126d017fe3342b01e782181bcdc5321", "pump-permanent",
                "RuneclawBear=2/2;GrizzlyBears=2/2", "RuneclawBear=4/5;GrizzlyBears=2/2");

        resolve("DB$ PumpAll | ValidCards$ Creature.YouCtrl | NumAtt$ 1 | NumDef$ 1 | Duration$ Permanent", first, me, null);
        assertEquals("PumpAll includes the first controlled creature", 5, first.getNetPower());
        assertEquals("PumpAll includes every matching controlled creature", 3, second.getNetPower());
        trace("forge-primitive-v1:f36f56f508ff41c3e2cce08420d518a1", "pumpall-controller-filter",
                "RuneclawBear=4/5;GrizzlyBears=2/2", "RuneclawBear=5/6;GrizzlyBears=3/3");
    }

    @Test
    public void animateAndAnimateAllCreateCreatureStateOnLivePermanents() {
        final Game game = initAndCreateGame();
        final Player me = game.getPlayers().get(0);
        final Card citadel = addCard("Darksteel Citadel", me);
        final Card island = addCard("Island", me);

        resolve("DB$ Animate | ValidTgts$ Land | Power$ 3 | Toughness$ 3 | Types$ Artifact,Creature | Duration$ Permanent", citadel, me, citadel);
        assertTrue("Animate adds creature type", citadel.isCreature());
        assertEquals("Animate sets base power", 3, citadel.getNetPower());
        assertEquals("Animate sets base toughness", 3, citadel.getNetToughness());
        trace("forge-primitive-v1:08424e768e141eda321218cb0567c839", "animate-single-land",
                "DarksteelCitadel=land,not-creature", "DarksteelCitadel=artifact-land-creature,3/3");

        resolve("DB$ AnimateAll | ValidCards$ Land.YouCtrl | Power$ 2 | Toughness$ 2 | Types$ Creature | Duration$ Permanent", citadel, me, null);
        assertTrue("AnimateAll changes the second matching land", island.isCreature());
        assertEquals("AnimateAll uses the asserted P/T on the matching land", 2, island.getNetPower());
        trace("forge-primitive-v1:6bd2cce628a9be72e542ddba5488c1fd", "animateall-controller-filter",
                "Island=land,not-creature", "Island=land-creature,2/2");
    }

    @Test
    public void copyPermanentAndCloneRetainDistinctObjectAndCopiedCharacteristics() {
        final Game game = initAndCreateGame();
        final Player me = game.getPlayers().get(0);
        final Card host = addCard("Runeclaw Bear", me);
        final Card source = addCard("Serra Angel", me);
        final int beforeCopies = countCardsWithName(game, "Serra Angel", ZoneType.Battlefield);

        resolve("DB$ CopyPermanent | ValidTgts$ Creature | NumCopies$ 1", host, me, source);
        assertEquals("CopyPermanent creates one additional permanent", beforeCopies + 1,
                countCardsWithName(game, "Serra Angel", ZoneType.Battlefield));
        trace("forge-primitive-v1:447081d46292da4e992bbb87fbb05bc0", "copypermanent-token",
                "SerraAngelCount=" + beforeCopies, "SerraAngelCount=" + (beforeCopies + 1));

        final Card clone = addCard("Clone", me);
        resolve("DB$ Clone | ValidTgts$ Creature", clone, me, source);
        assertEquals("Clone receives the copied name from the selected live object", "Serra Angel", clone.getName());
        assertEquals("Clone receives copied power", 4, clone.getNetPower());
        trace("forge-primitive-v1:4c0f82de9018c96620bc5544355fbe7b", "clone-live-object",
                "Clone=name:Clone,power:0", "Clone=name:SerraAngel,power:4");
    }

    @Test
    public void controlAndControllerCleanupUseForgeControllerState() {
        final Game game = initAndCreateGame();
        final Player me = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);
        final Card host = addCard("Runeclaw Bear", me);
        final Card stolen = addCard("Grizzly Bears", opponent);

        resolve("DB$ GainControl | ValidTgts$ Creature | LoseControl$ EOT", host, me, stolen);
        assertSame("GainControl changes controller in the live game", me, stolen.getController());
        trace("forge-primitive-v1:9b511df4b453a3c484754ff1e8246b48", "gain-control",
                "GrizzlyBears.controller=opponent", "GrizzlyBears.controller=me");

        resolve("DB$ GainControlVariant | AllValid$ Card | ChangeController$ CardOwner", host, me, null);
        assertSame("owner-return variant restores the owner controller", opponent, stolen.getController());
        trace("forge-primitive-v1:760a97962673030b6d8646e6183bfc92", "gain-control-owner-cleanup",
                "GrizzlyBears.owner=opponent,controller=me", "GrizzlyBears.owner=opponent,controller=opponent");
    }

    @Test
    public void continuousStaticEffectAndAttributeStateAreObservedOnEngineObjects() {
        final Game game = initAndCreateGame();
        final Player me = game.getPlayers().get(0);
        final Card bear = addCard("Runeclaw Bear", me);
        final Card anthem = addCard("Glorious Anthem", me);
        game.getAction().checkStateEffects(true);
        assertEquals("Continuous static ability contributes to derived power", 3, bear.getNetPower());
        assertEquals("Continuous static ability contributes to derived toughness", 3, bear.getNetToughness());
        trace("forge-primitive-v1:b885ed6f5df2929844ca4e1f69ebfaad", "continuous-static-layer",
                "RuneclawBear=2/2;GloriousAnthem=absent", "RuneclawBear=3/3;GloriousAnthem=present");

        resolve("DB$ AlterAttribute | ValidTgts$ Creature | Attributes$ Suspected", anthem, me, bear);
        assertTrue("AlterAttribute changes the engine's suspect flag", bear.isSuspected());
        trace("forge-primitive-v1:edd3340993f0e721a30ba4524a9eab76", "alter-attribute-suspected",
                "RuneclawBear.suspected=false", "RuneclawBear.suspected=true");

        game.getAction().moveTo(ZoneType.Graveyard, anthem, null, null);
        game.getAction().checkStateEffects(true);
        assertEquals("continuous effect is removed when its source leaves", 2, bear.getNetPower());
        assertFalse("the source is no longer a battlefield continuous effect", anthem.isInZone(ZoneType.Battlefield));
    }

    @Test
    public void transformUsesSetStateAndChangesTheLiveFace() {
        final Game game = initAndCreateGame();
        final Player me = game.getPlayers().get(0);
        final Card delver = addCard("Delver of Secrets", me);
        resolve("DB$ SetState | Mode$ Transform | ValidTgts$ Card", delver, me, delver);
        assertEquals("SetState transforms the object to its printed back face", "Insectile Aberration", delver.getName());
        assertTrue("transformed face retains creature identity", delver.isCreature());
        trace("forge-primitive-v1:f82456491a192bf8c75c2174a572a2bc", "setstate-transform",
                "DelverOfSecrets.face=front", "InsectileAberration.face=back,creature=true");
    }
}
