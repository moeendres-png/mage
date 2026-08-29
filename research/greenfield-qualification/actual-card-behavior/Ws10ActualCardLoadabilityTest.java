package forge.gamesimulationtests;

import forge.StaticData;
import forge.game.card.CardFactory;
import forge.item.PaperCard;
import forge.net.TestUtils;
import org.testng.annotations.Test;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

/**
 * WS10 batch runtime CardDb/ability-construction probe.
 *
 * The probe uses Forge's pinned headless test bootstrap before touching
 * ForgeConstants/StaticData. CardDb loadability and CardFactory construction are
 * recorded independently; neither is promoted to semantic spell/ability
 * execution by the WS10 classifier.
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

    private static String throwableSummary(Throwable t) {
        StringBuilder b = new StringBuilder();
        Throwable cur = t;
        int depth = 0;
        while (cur != null && depth++ < 8) {
            if (b.length() > 0) b.append(" <- ");
            b.append(cur.getClass().getName()).append(": ").append(String.valueOf(cur.getMessage()));
            cur = cur.getCause();
        }
        return b.toString();
    }

    private static void writeBootstrap(Path path, boolean ok, String error) throws Exception {
        Files.createDirectories(path.getParent());
        String body = "{\"bootstrap_success\":" + ok
                + ",\"error\":" + (error == null ? "null" : "\"" + esc(error) + "\"")
                + "}\n";
        Files.writeString(path, body, StandardCharsets.UTF_8);
    }

    @Test
    public void batchLoadRequirementIdentities() throws Exception {
        String namesArg = System.getProperty("ws10.names");
        String outArg = System.getProperty("ws10.out");
        String bootstrapArg = System.getProperty("ws10.bootstrap");
        if (namesArg == null || outArg == null || bootstrapArg == null) {
            throw new IllegalStateException("ws10.names, ws10.out and ws10.bootstrap system properties are required");
        }
        Path names = Paths.get(namesArg);
        Path out = Paths.get(outArg);
        Path bootstrap = Paths.get(bootstrapArg);

        try {
            TestUtils.ensureFModelInitialized();
            if (StaticData.instance() == null) {
                throw new IllegalStateException("Forge StaticData.instance() is null after TestUtils bootstrap");
            }
            writeBootstrap(bootstrap, true, null);
        } catch (Throwable t) {
            writeBootstrap(bootstrap, false, throwableSummary(t));
            throw new RuntimeException("WS10 Forge bootstrap failed: " + throwableSummary(t), t);
        }

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
                String resolvedName = null;
                String errorClass = null;
                String error = null;
                try {
                    PaperCard pc = StaticData.instance().getCommonCards().getCard(name);
                    loadable = pc != null && pc.getRules() != null;
                    if (pc != null) {
                        resolvedName = pc.getName();
                    }
                    if (loadable) {
                        try {
                            CardFactory.getCard(pc, null, null);
                            constructable = true;
                        } catch (Throwable t) {
                            errorClass = t.getClass().getName();
                            error = throwableSummary(t);
                        }
                    } else {
                        errorClass = "CARD_NOT_FOUND";
                        error = "StaticData common CardDb returned no canonical-name card";
                    }
                } catch (Throwable t) {
                    errorClass = t.getClass().getName();
                    error = throwableSummary(t);
                }
                w.write("{\"oracle_id\":\"" + esc(oid)
                        + "\",\"oracle_name\":\"" + esc(name)
                        + "\",\"resolved_name\":" + (resolvedName == null ? "null" : "\"" + esc(resolvedName) + "\"")
                        + ",\"loadable\":" + loadable
                        + ",\"runtime_constructable\":" + constructable
                        + ",\"error_class\":" + (errorClass == null ? "null" : "\"" + esc(errorClass) + "\"")
                        + ",\"error\":" + (error == null ? "null" : "\"" + esc(error) + "\"")
                        + "}\n");
            }
        }
    }
}
