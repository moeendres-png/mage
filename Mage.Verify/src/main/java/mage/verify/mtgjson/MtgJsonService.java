package mage.verify.mtgjson;

import com.google.gson.Gson;
import mage.client.remote.XmageURLConnection;
import org.apache.log4j.Logger;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.nio.file.StandardCopyOption;
import java.text.Normalizer;
import java.util.*;
import java.util.stream.Collectors;
import java.util.zip.ZipInputStream;
import java.util.concurrent.TimeUnit;

/**
 * MTGJSON v5: basic service to work with mtgjson data
 *
 * @author JayDi85
 */
public final class MtgJsonService {

    private static final boolean MTGJSON_OFFLINE_MODE = false; // enable to keep mtgjson files forever instead everyday update

    /*
     * Qualification binding (C14, commander-playtest-lab#495). With the reference
     * property set to a pin file, Mage.Verify reads MTGJSON only from the
     * directory property: nothing is downloaded or refreshed, every file's
     * SHA-256 must equal the pin, and AllPrintings' meta version/date must equal
     * the pin's. Any mismatch or missing file fails loading. Refreshing the
     * reference is a separate operation (the mtgjson-reference-refresh workflow
     * publishes immutable release assets; a reviewed change updates the pin).
     * Without the property, the developer behaviour below is unchanged.
     */
    public static final String REFERENCE_PROPERTY = "xmage.verify.mtgjson.reference";
    public static final String DIRECTORY_PROPERTY = "xmage.verify.mtgjson.dir";

    /** The pinned reference, as committed in the pin file. */
    public static final class Reference {
        public String schema;
        public String release;
        public Map<String, PinnedFile> files;
        public MtgJsonMetadata meta;
    }

    public static final class PinnedFile {
        public String sha256;
        public long bytes;
    }

    /** The bound reference, or null when Mage.Verify runs unpinned (developer refresh mode). */
    public static Reference boundReference() throws IOException {
        String pin = System.getProperty(REFERENCE_PROPERTY);
        if (pin == null || pin.trim().isEmpty()) {
            return null;
        }
        Reference reference = new Gson().fromJson(
                new String(Files.readAllBytes(Paths.get(pin)), StandardCharsets.UTF_8), Reference.class);
        if (reference == null || !"mage.verify.mtgjson-reference/1".equals(reference.schema)
                || reference.files == null || reference.meta == null
                || reference.meta.version == null || reference.meta.date == null) {
            throw new IOException("mtgjson reference: malformed pin file " + pin);
        }
        return reference;
    }

    /** Opens a pinned file after proving its bytes equal the pin; never downloads. */
    static InputStream openPinned(Reference reference, String filename) throws IOException {
        PinnedFile pinned = reference.files.get(filename);
        if (pinned == null || pinned.sha256 == null) {
            throw new IOException("mtgjson reference: " + filename + " is not pinned");
        }
        String directory = System.getProperty(DIRECTORY_PROPERTY);
        if (directory == null || directory.trim().isEmpty()) {
            throw new IOException("mtgjson reference: " + DIRECTORY_PROPERTY + " is not set");
        }
        Path file = Paths.get(directory, filename);
        if (!Files.isRegularFile(file)) {
            throw new IOException("mtgjson reference: missing pinned file " + file);
        }
        String actual = sha256(file);
        if (!actual.equals(pinned.sha256) || Files.size(file) != pinned.bytes) {
            throw new IOException("mtgjson reference: " + filename + " does not match the pin (sha256 "
                    + actual + ", " + Files.size(file) + " bytes; pinned " + pinned.sha256 + ", "
                    + pinned.bytes + " bytes)");
        }
        logger.info("mtgjson: bound reference " + reference.release + " " + filename + " sha256 " + actual);
        return Files.newInputStream(file);
    }

    static void requirePinnedMeta(Reference reference, MtgJsonMetadata meta) throws IOException {
        if (meta == null || !reference.meta.version.equals(meta.version) || !reference.meta.date.equals(meta.date)) {
            throw new IOException("mtgjson reference: AllPrintings meta " + (meta == null ? "missing"
                    : meta.version + " / " + meta.date) + " is not the pinned " + reference.meta.version
                    + " / " + reference.meta.date);
        }
    }

    private static String sha256(Path file) throws IOException {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[1 << 16];
            try (InputStream in = new DigestInputStream(Files.newInputStream(file), digest)) {
                while (in.read(buffer) >= 0) {
                    // digest accumulates as the stream is read
                }
            }
            StringBuilder hex = new StringBuilder();
            for (byte b : digest.digest()) {
                hex.append(String.format("%02x", b & 0xff));
            }
            return hex.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IOException(e);
        }
    }

    private static final Logger logger = Logger.getLogger(MtgJsonService.class);

    public static Map<String, String> mtgJsonToXMageCodes = new HashMap<>();
    public static Map<String, String> xMageToMtgJsonCodes = new HashMap<>();

    static {
        //mtgJsonToXMageCodes.put("pPRE", "PPRE");

        // revert search
        for (Map.Entry<String, String> entry : mtgJsonToXMageCodes.entrySet()) {
            xMageToMtgJsonCodes.put(entry.getValue(), entry.getKey());
        }
    }

    private static Map<String, MtgJsonCard> loadAllCards() throws IOException {
        AtomicCardsModel json = readFromZip("AtomicCards.json.zip", AtomicCardsModel.class);
        return json.prepareIndex();
    }

    private static AllPrintingsModel loadAllSets() throws IOException {
        AllPrintingsModel model = readFromZip("AllPrintings.json.zip", AllPrintingsModel.class);
        Reference reference = boundReference();
        if (reference != null) {
            requirePinnedMeta(reference, model.meta);
        }
        return model;
    }

    private static <T> T readFromZip(String filename, Class<T> clazz) throws IOException {
        // qualification: only the pinned reference, never a download or a refresh
        Reference reference = boundReference();
        if (reference != null) {
            return readFromZip(openPinned(reference, filename), clazz);
        }

        // build-in file
        InputStream stream = MtgJsonService.class.getResourceAsStream(filename);
        if (stream != null) {
            logger.info("mtgjson: use build-in file " + filename);
            return readFromZip(stream, clazz);
        }

        // already downloaded file - can try to refresh it once per day for better verify results
        long maxFileAgeMs = TimeUnit.HOURS.toMillis(24);
        File file = new File(filename);
        boolean hasExistingFile = file.exists();
        if (hasExistingFile && (MTGJSON_OFFLINE_MODE || System.currentTimeMillis() - file.lastModified() < maxFileAgeMs)) {
            logger.info("mtgjson: use existing file " + filename + " from " + file.getAbsolutePath());
            return readFromZip(Files.newInputStream(file.toPath()), clazz);
        } else if (hasExistingFile) {
            logger.info("mtgjson: existing file " + filename + " is older than 24 hours, downloading fresh copy");
        }

        // new download
        String url = "https://mtgjson.com/api/v5/" + filename;
        logger.info("mtgjson: downloading new file " + url);
        // mtgjson site require user-agent in headers (otherwise it return 403)
        // XmageURLConnection done all the work (headers, error processing and other)
        stream = XmageURLConnection.downloadBinary(url);
        if (stream != null) {
            Files.copy(stream, file.toPath(), StandardCopyOption.REPLACE_EXISTING);
            logger.info("mtgjson: download DONE, saved to " + file.getAbsolutePath());
            hasExistingFile = true; // fall through and read it below
        } else {
            logger.warn("mtgjson: download failed for " + filename);
        }

        if (hasExistingFile) {
            logger.info("mtgjson: using existing file " + filename + " from " + file.getAbsolutePath());
            return readFromZip(Files.newInputStream(file.toPath()), clazz);
        }

        throw new IOException("mtgjson: can't found or download file, check your connection " + filename);
    }

    private static <T> T readFromZip(InputStream stream, Class<T> clazz) throws IOException {
        try (ZipInputStream zipInputStream = new ZipInputStream(stream)) {
            zipInputStream.getNextEntry();
            return new Gson().fromJson(new InputStreamReader(zipInputStream), clazz);
        }
    }

    public static Map<String, MtgJsonSet> sets() {
        return SetHolder.sets;
    }

    public static Map<String, MtgJsonCard> cards() {
        return CardHolder.cards;
    }

    public static MtgJsonMetadata meta() {
        return SetHolder.meta;
    }

    public static MtgJsonCard card(String name) {
        return findReference(CardHolder.cards, name);
    }

    public static MtgJsonCard cardByClassName(String classFullName) {
        String shortName = classFullName.replaceAll(".*\\.", "").toLowerCase(Locale.ENGLISH);
        return findReference(CardHolder.cardsByClasses, shortName);
    }

    public static List<MtgJsonCard> cardsFromSet(String setCode, String name) {
        MtgJsonSet set = findReference(SetHolder.sets, setCode);
        if (set == null) {
            return new ArrayList<>();
        }

        // for a double faced cards each side goes here as one card, so must search by face name
        String needName = convertXmageToMtgJsonCardName(name);
        return set.cards.stream()
                .filter(c -> needName.equals(c.getNameAsFace()))
                .collect(Collectors.toList());
    }

    public static MtgJsonCard cardFromSet(String setCode, String name, String number) {
        String jsonSetCode = xMageToMtgJsonCodes.getOrDefault(setCode, setCode);
        List<MtgJsonCard> list = cardsFromSet(jsonSetCode, name);
        return list.stream()
                .filter(c -> convertMtgJsonToXmageCardNumber(c.number).equals(number))
                .findFirst().orElse(null);
    }

    private static <T> T findReference(Map<String, T> reference, String name) {
        T ref = reference.get(name);
        if (ref == null) {
            name = convertXmageToMtgJsonCardName(name);
            ref = reference.get(name);
        }
        return ref;
    }

    private static String convertXmageToMtgJsonCardName(String cardName) {
        return cardName;
        //.replaceFirst("Aether", "Æther")
        //.replace("'", "\""); // for Kongming, "Sleeping Dragon" & Pang Tong, "Young Phoenix"
    }

    private static String convertMtgJsonToXmageCardNumber(String number) {
        // card number notation must be same for all sets (replace non-ascii symbols)
        // so your set generation tools must use same replaces
        return number
                .replace("★", "*")
                .replace("†", "+")
                .replace("Φ", "Ph");
    }

    private static <T> void addAliases(Map<String, T> reference) {
        Map<String, String> aliases = new HashMap<>();
        for (String name : reference.keySet()) {
            String unaccented = stripAccents(name);
            if (!name.equals(unaccented)) {
                aliases.put(name, unaccented);
            }
        }
        for (Map.Entry<String, String> mapping : aliases.entrySet()) {
            reference.put(mapping.getValue(), reference.get(mapping.getKey()));
        }
    }

    private static String stripAccents(String str) {
        String decomposed = Normalizer.normalize(str, Normalizer.Form.NFKD);
        return decomposed.replaceAll("[\\p{InCombiningDiacriticalMarks}]", "");
    }

    private static final class AtomicCardsModel {

        // list by card names, each name can have multiple cards (two faces, different cards with same name from un-sets)
        public Map<String, ArrayList<MtgJsonCard>> data;

        private boolean containsSameNames(ArrayList<MtgJsonCard> list) {
            Set<String> names = list.stream().map(MtgJsonCard::getNameAsFace).collect(Collectors.toSet());
            return names.size() == 1;
        }

        public Map<String, MtgJsonCard> prepareIndex() {
            HashMap<String, MtgJsonCard> index = new HashMap<>();
            for (Map.Entry<String, ArrayList<MtgJsonCard>> rec : data.entrySet()) {
                if (rec.getValue().size() == 1) {
                    // normal card
                    index.put(rec.getKey(), rec.getValue().get(0));
                } else {
                    if (containsSameNames(rec.getValue())) {
                        // un-set cards - same name, but different cards (must be ignored)
                    } else {
                        // multi-faces cards
                        MtgJsonCard mainCard = rec.getValue().stream().filter(c -> c.side.equals("a")).findAny().orElse(null);
                        if (mainCard != null) {
                            index.put(mainCard.faceName, mainCard);
                            for (MtgJsonCard card : rec.getValue()) {
                                if (card == mainCard) continue;
                                index.put(card.faceName, card);
                            }
                        }
                    }
                }
            }
            return index;
        }
    }

    private static final class AllPrintingsModel {
        public Map<String, MtgJsonSet> data;
        public MtgJsonMetadata meta;
    }

    private static final class CardHolder {
        private static final Map<String, MtgJsonCard> cards; // key: card name like Grizzly Bears
        private static final Map<String, MtgJsonCard> cardsByClasses; // key: short class name in lower case like grizzlybears

        static {
            try {
                cards = loadAllCards();

                List<String> keysToDelete = new ArrayList<>();

                // fix names
                Map<String, MtgJsonCard> newKeys = new HashMap<>();
                for (String key : cards.keySet()) {
                    if (key.contains("(")) {
                        newKeys.put(key.replaceAll("\\(.*\\)", "").trim(), cards.get(key));
                        keysToDelete.add(key);
                    }
                }
                cards.putAll(newKeys);
                cards.keySet().removeAll(keysToDelete);

                // remove wrong data (tokens)
                keysToDelete.clear();
                for (Map.Entry<String, MtgJsonCard> record : cards.entrySet()) {
                    if (record.getValue().layout.equals("token") || record.getValue().layout.equals("double_faced_token")) {
                        keysToDelete.add(record.getKey());
                    }
                }
                cards.keySet().removeAll(keysToDelete);

                addAliases(cards);

                // create index for class names searching
                // lower case with ascii symbols without space
                cardsByClasses = new HashMap<>(cards.size());
                cards.forEach((name, card) -> {
                    String className = name.replaceAll("[^ -~]|[ ]", "").toLowerCase(Locale.ENGLISH);
                    cardsByClasses.put(className, card);
                });
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }

    private static final class SetHolder {
        private static final Map<String, MtgJsonSet> sets;
        private static final MtgJsonMetadata meta;

        static {
            try {
                AllPrintingsModel model = loadAllSets();
                sets = model.data;
                meta = model.meta;
                System.out.println("MTGJSON version " + meta.version + ", release date " + meta.date);
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }
}
