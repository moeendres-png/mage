package forge.gamesimulationtests;

import forge.game.card.CardFactory;
import forge.gamesimulationtests.util.CardDatabaseHelper;
import forge.item.PaperCard;
import org.testng.annotations.Test;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

/**
 * WS10 batch CardDb/ability-construction probe.
 *
 * This proves exact-name CardDb loadability and records whether CardFactory can
 * build the card's runtime object/abilities in a no-game parse context. It does
 * not claim that any spell/ability was legally activated or semantically
 * resolved; the Python closeout deliberately keeps EXECUTABLE fail-closed.
 */
public final class Ws10ActualCardLoadabilityTest {
    private static String esc(String s) {
        if (s == null) return "";
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '\\': b.append("\\\\"); break;
                case '"': b.append("\\\""); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) b.append(String.format("\\u%04x", (int)c));
                    else b.append(c);
            }
        }
        return b.toString();
    }

    @Test
    public void batchLoadRequirementIdentities() throws Exception {
        String namesArg = System.getProperty("ws10.names");
        String outArg = System.getProperty("ws10.out");
        if (namesArg == null || outArg == null) {
            throw new IllegalStateException("ws10.names and ws10.out system properties are required");
        }
        Path names = Paths.get(namesArg);
        Path out = Paths.get(outArg);
        Files.createDirectories(out.getParent());
        List<String> lines = Files.readAllLines(names, StandardCharsets.UTF_8);
        try (BufferedWriter w = Files.newBufferedWriter(out, StandardCharsets.UTF_8)) {
            for (String line : lines) {
                if (line.isBlank()) continue;
                int tab = line.indexOf('\t');
                if (tab <= 0) throw new IllegalArgumentException("invalid WS10 TSV row");
                String oid = line.substring(0, tab);
                String name = line.substring(tab + 1);
                boolean loadable = false;
                boolean constructable = false;
                String errorClass = null;
                String error = null;
                try {
                    PaperCard pc = CardDatabaseHelper.getCard(name);
                    loadable = pc != null && pc.getRules() != null;
                    if (loadable) {
                        try {
                            CardFactory.getCard(pc, null, null);
                            constructable = true;
                        } catch (Throwable t) {
                            errorClass = t.getClass().getName();
                            error = String.valueOf(t.getMessage());
                        }
                    }
                } catch (Throwable t) {
                    errorClass = t.getClass().getName();
                    error = String.valueOf(t.getMessage());
                }
                w.write("{\"oracle_id\":\"" + esc(oid)
                        + "\",\"oracle_name\":\"" + esc(name)
                        + "\",\"loadable\":" + loadable
                        + ",\"runtime_constructable\":" + constructable
                        + ",\"error_class\":" + (errorClass == null ? "null" : "\"" + esc(errorClass) + "\"")
                        + ",\"error\":" + (error == null ? "null" : "\"" + esc(error) + "\"")
                        + "}\n");
            }
        }
    }
}
