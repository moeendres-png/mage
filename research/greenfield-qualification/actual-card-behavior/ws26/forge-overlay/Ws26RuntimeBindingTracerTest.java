package forge.gamesimulationtests;

import forge.StaticData;
import forge.game.card.Card;
import forge.game.card.CardFactory;
import forge.game.keyword.KeywordInterface;
import forge.item.PaperCard;
import forge.net.TestUtils;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * WS26 qualification-only runtime binding tracer.
 *
 * It constructs the exact pinned Forge card and observes KeywordInstance output.
 * It does not change production semantics, choose actions, or infer rules from card names.
 */
public final class Ws26RuntimeBindingTracerTest {
    private static String esc(final String s) {
        if (s == null) return "";
        return s.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t");
    }

    private static List<String> classes(final Iterable<?> xs) {
        final List<String> out = new ArrayList<>();
        for (final Object x : xs) out.add(x.getClass().getName());
        Collections.sort(out);
        return out;
    }

    private static String jsonArray(final List<String> xs) {
        final StringBuilder b = new StringBuilder("[");
        for (int i = 0; i < xs.size(); i++) {
            if (i > 0) b.append(',');
            b.append('\"').append(esc(xs.get(i))).append('\"');
        }
        return b.append(']').toString();
    }

    @Test
    public void traceKeywordGeneratedRuntimeObjects() throws Exception {
        final String inputArg = System.getProperty("ws26.bindingInput");
        final String outArg = System.getProperty("ws26.bindingOut");
        if (inputArg == null || outArg == null) {
            throw new IllegalStateException("ws26.bindingInput and ws26.bindingOut are required");
        }
        TestUtils.ensureFModelInitialized();
        Assert.assertNotNull(StaticData.instance(), "Forge StaticData must initialize");

        final List<String> rows = Files.readAllLines(Path.of(inputArg), StandardCharsets.UTF_8);
        final Path out = Path.of(outArg);
        Files.createDirectories(out.getParent());
        try (BufferedWriter w = Files.newBufferedWriter(out, StandardCharsets.UTF_8)) {
            // Forge treats negative IDs as view-only and omits intrinsic rules data.
            int runtimeCardId = 1;
            for (final String row : rows) {
                if (row.isBlank()) continue;
                final String[] c = row.split("\\t", -1);
                if (c.length != 6) throw new IllegalArgumentException("expected 6 TSV columns");
                final String occurrence = c[0];
                final String oracleId = c[1];
                final String forgeName = c[2];
                final String sourcePath = c[3];
                final String sourceLine = c[4];
                final String keywordText = c[5];

                final PaperCard pc = StaticData.instance().getCommonCards().getCard(forgeName);
                Assert.assertNotNull(pc, "exact Forge source Name must resolve: " + forgeName);
                final Card card = CardFactory.getCard(pc, null, runtimeCardId++, null);
                Assert.assertNotNull(card, "CardFactory must construct: " + forgeName);

                KeywordInterface hit = null;
                for (final KeywordInterface kw : card.getKeywords()) {
                    if (keywordText.equals(kw.getOriginal())) {
                        hit = kw;
                        break;
                    }
                }
                Assert.assertNotNull(hit, "exact source keyword must survive construction: " + keywordText + " / " + forgeName);

                w.write("{\"occurrence\":\"" + esc(occurrence)
                        + "\",\"oracle_identity\":\"" + esc(oracleId)
                        + "\",\"forge_source_path\":\"" + esc(sourcePath)
                        + "\",\"source_line\":" + sourceLine
                        + ",\"source_value\":\"" + esc(keywordText)
                        + "\",\"keyword_enum\":\"" + esc(hit.getKeyword().name())
                        + "\",\"keyword_instance_class\":\"" + esc(hit.getClass().getName())
                        + "\",\"has_generated_traits\":" + hit.hasTraits()
                        + ",\"generated_trigger_classes\":" + jsonArray(classes(hit.getTriggers()))
                        + ",\"generated_replacement_classes\":" + jsonArray(classes(hit.getReplacements()))
                        + ",\"generated_spellability_classes\":" + jsonArray(classes(hit.getAbilities()))
                        + ",\"generated_static_classes\":" + jsonArray(classes(hit.getStaticAbilities()))
                        + "}\n");
            }
        }
    }
}
