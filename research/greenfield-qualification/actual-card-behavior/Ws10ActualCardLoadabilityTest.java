package forge.gamesimulationtests;

import forge.StaticData;
import forge.card.CardRules;
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
 * Forge's canonical DB key differs from Scryfall's `front // back` Oracle name
 * for several non-combine two-face layouts. The optional fallback alias in the
 * input is derived from Scryfall's pinned front face. It is accepted only when
 * Forge CardRules reports the exact ordered front/back face names supplied by
 * that same Oracle identity. No card-name exception table exists here.
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

    private static boolean matchesExpectedFaces(PaperCard pc, String expectedFront, String expectedBack) {
        if (pc == null || pc.getRules() == null || expectedFront.isEmpty() || expectedBack.isEmpty()) {
            return false;
        }
        CardRules rules = pc.getRules();
        if (rules.getMainPart() == null || rules.getOtherPart() == null) {
            return false;
        }
        return expectedFront.equals(rules.getMainPart().getName())
                && expectedBack.equals(rules.getOtherPart().getName());
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
                String[] cols = line.split("\\t", -1);
                if (cols.length != 5 || cols[0].isEmpty() || cols[1].isEmpty()) {
                    throw new IllegalArgumentException("invalid WS10 TSV row; expected oid, canonical, alias, expected-front, expected-back");
                }
                String oid = cols[0];
                String canonical = cols[1];
                String alias = cols[2];
                String expectedFront = cols[3];
                String expectedBack = cols[4];

                boolean loadable = false;
                boolean identityMatch = false;
                boolean constructable = false;
                boolean usedAlias = false;
                String lookupName = canonical;
                String resolvedName = null;
                String rulesName = null;
                String resolvedFront = null;
                String resolvedBack = null;
                String errorClass = null;
                String error = null;
                try {
                    PaperCard pc = StaticData.instance().getCommonCards().getCard(canonical);
                    if (pc != null && pc.getRules() != null) {
                        identityMatch = true;
                    } else if (!alias.isEmpty()) {
                        lookupName = alias;
                        pc = StaticData.instance().getCommonCards().getCard(alias);
                        usedAlias = pc != null;
                        identityMatch = matchesExpectedFaces(pc, expectedFront, expectedBack);
                    }
                    if (pc != null && pc.getRules() != null) {
                        resolvedName = pc.getName();
                        rulesName = pc.getRules().getName();
                        if (pc.getRules().getMainPart() != null) resolvedFront = pc.getRules().getMainPart().getName();
                        if (pc.getRules().getOtherPart() != null) resolvedBack = pc.getRules().getOtherPart().getName();
                    }
                    loadable = pc != null && pc.getRules() != null && identityMatch;
                    if (loadable) {
                        try {
                            CardFactory.getCard(pc, null, null);
                            constructable = true;
                        } catch (Throwable t) {
                            errorClass = t.getClass().getName();
                            error = throwableSummary(t);
                        }
                    } else if (pc == null) {
                        errorClass = "CARD_NOT_FOUND";
                        error = "CardDb returned no canonical card and no Oracle-derived front-face alias match";
                    } else if (!identityMatch) {
                        errorClass = "ORACLE_FACE_IDENTITY_MISMATCH";
                        error = "Front-face alias resolved, but Forge CardRules did not match the expected Oracle face-name tuple";
                    }
                } catch (Throwable t) {
                    errorClass = t.getClass().getName();
                    error = throwableSummary(t);
                }
                w.write("{\"oracle_id\":\"" + esc(oid)
                        + "\",\"oracle_name\":\"" + esc(canonical)
                        + "\",\"lookup_name\":\"" + esc(lookupName)
                        + "\",\"used_alias\":" + usedAlias
                        + ",\"identity_match\":" + identityMatch
                        + ",\"resolved_name\":" + (resolvedName == null ? "null" : "\"" + esc(resolvedName) + "\"")
                        + ",\"rules_name\":" + (rulesName == null ? "null" : "\"" + esc(rulesName) + "\"")
                        + ",\"resolved_front\":" + (resolvedFront == null ? "null" : "\"" + esc(resolvedFront) + "\"")
                        + ",\"resolved_back\":" + (resolvedBack == null ? "null" : "\"" + esc(resolvedBack) + "\"")
                        + ",\"loadable\":" + loadable
                        + ",\"runtime_constructable\":" + constructable
                        + ",\"error_class\":" + (errorClass == null ? "null" : "\"" + esc(errorClass) + "\"")
                        + ",\"error\":" + (error == null ? "null" : "\"" + esc(error) + "\"")
                        + "}\n");
            }
        }
    }
}
