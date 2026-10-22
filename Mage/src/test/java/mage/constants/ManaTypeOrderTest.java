package mage.constants;

import mage.Mana;
import org.junit.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

import static org.junit.Assert.assertEquals;

/**
 * An enum has no hashCode of its own, so a HashSet of mana types iterates in an order that depends
 * on the JVM's identity hashes. The sets that feed "choose a color" prompts and mana lists follow
 * the declaration order of the enum instead.
 */
public class ManaTypeOrderTest {

    @Test
    public void testManaTypesOfAManaListFollowTheDeclarationOrder() {
        List<Mana> produced = Arrays.asList(
                Mana.WhiteMana(1),
                Mana.GreenMana(1),
                Mana.ColorlessMana(1),
                Mana.RedMana(1),
                Mana.BlackMana(1),
                Mana.BlueMana(1)
        );
        List<ManaType> types = new ArrayList<>(ManaType.getManaTypesFromManaList(produced));
        List<ManaType> declared = new ArrayList<>(types);
        declared.sort(Comparator.naturalOrder());
        assertEquals(6, types.size());
        assertEquals(declared, types);
    }
}
