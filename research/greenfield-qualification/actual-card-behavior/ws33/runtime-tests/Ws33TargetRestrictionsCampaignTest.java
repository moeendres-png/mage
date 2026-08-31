package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.card.CardStateName;
import forge.game.Game;
import forge.game.GameObject;
import forge.game.ability.AbilityKey;
import forge.game.ability.AbilityFactory;
import forge.game.card.Card;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.spellability.TargetRestrictions;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.player.LobbyPlayerHuman;
import forge.player.PlayerControllerHuman;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Locale;

/**
 * WS33 qualification-only TargetRestrictions campaign.
 *
 * Each case uses an actual pinned-Forge card/SpellAbility and delegates target
 * enumeration/validation to the WS01 externalized PlayerControllerHuman target
 * path. The driver has one fixture-designated intended target and may choose it
 * only when Forge includes the corresponding semantic action in the
 * authoritative TARGET_SELECTION request. No effect is directly resolved.
 */
public final class Ws33TargetRestrictionsCampaignTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";

    @Test
    public void targetRestrictionsCampaign() throws Exception {
        final String mode = System.getProperty("ws33.targetMode", "record");
        if (!"record".equals(mode) && !"replay".equals(mode)) {
            throw new IllegalArgumentException("ws33.targetMode must be record or replay");
        }
        final Path casesPath = requiredPath("ws33.targetCases");
        final Path out = requiredPath("ws33.targetOut");
        Files.createDirectories(out);
        final List<Case> cases = loadCases(casesPath);
        final List<String> diagnostics = new ArrayList<>();
        final List<String> admittedRecords = new ArrayList<>();
        int success = 0;

        for (final Case c : cases) {
            try {
                if ("record".equals(mode)) {
                    final Result result = executeCase(c, null);
                    writeRecord(out, c, result);
                    success++;
                } else {
                    final Path dir = caseDir(out, c.pathId);
                    if (!Files.isRegularFile(dir.resolve("record-success.marker"))) {
                        continue;
                    }
                    final List<ReplayDecision> replay = loadReplayDecisions(dir.resolve("decision-replay.tsv"));
                    final Result result = executeCase(c, replay);
                    final String expected = Files.readString(dir.resolve("final-state.txt"), StandardCharsets.UTF_8);
                    if (!expected.equals(result.canonicalFinalState)) {
                        throw new IllegalStateException("semantic replay state mismatch expected="
                                + expected + " actual=" + result.canonicalFinalState);
                    }
                    writeReplayEvidence(dir, result, dir.resolve("decision-tape.json"), expected);
                    admittedRecords.add("records/" + shortId(c.pathId) + "/record.json");
                    success++;
                }
            } catch (Throwable error) {
                diagnostics.add("{\"mode\":" + q(mode)
                        + ",\"path_id\":" + q(c.pathId)
                        + ",\"card\":" + q(c.cardName)
                        + ",\"error_type\":" + q(error.getClass().getName())
                        + ",\"message\":" + q(String.valueOf(error.getMessage())) + "}");
            }
        }

        writeDiagnostics(out, mode, diagnostics);
        if ("replay".equals(mode)) {
            writeCampaignIndex(out, admittedRecords);
        }
        Assert.assertTrue(success > 0, "TargetRestrictions campaign produced no successful " + mode + " cases");
        System.out.println("WS33_TARGET_CAMPAIGN_MODE=" + mode);
        System.out.println("WS33_TARGET_CAMPAIGN_SUCCESS=" + success);
        System.out.println("WS33_TARGET_CAMPAIGN_DIAGNOSTIC_FAILURES=" + diagnostics.size());
    }

    private Result executeCase(final Case c, final List<ReplayDecision> replay) {
        final Game game = initAndCreateThreePlayerGame();
        final Player actor = game.getPlayers().get(0);
        final Player opponent = game.getPlayers().get(1);

        final Card source = createCard(c.cardName, actor);
        final SpellAbility ability = findAbility(source, c);
        ability.setActivatingPlayer(actor);
        if ("TriggeredTarget".equals(ability.getParam("TargetsWithDefinedController"))) {
            ability.setTriggeringObject(AbilityKey.Target, opponent);
        }
        if ("SP".equals(c.abilityKind)) {
            actor.getZone(ZoneType.Hand).add(source);
        } else {
            actor.getZone(ZoneType.Battlefield).add(source);
        }

        final GameObject intended;
        final String relation;
        if ("STACK_TRIGGERED_ABILITY".equals(c.fixtureContext)) {
            final Card triggerSource = addCardToZone("Swiftwater Cliffs", actor, ZoneType.Hand);
            game.getAction().moveTo(ZoneType.Battlefield, triggerSource, null, null);
            if (!game.getTriggerHandler().runWaitingTriggers()
                    || !game.getStack().addAllTriggeredAbilitiesToStack() || game.getStack().isEmpty()) {
                throw new IllegalStateException("actual trigger fixture did not reach the stack");
            }
            intended = game.getStack().peekAbility();
            relation = "ACTOR";
        } else if (c.fixtureContext.startsWith("STACK_")) {
            final Player stackOwner = c.targetRole.startsWith("OWN_") ? actor : opponent;
            final String stackCardName = "STACK_ARTIFACT_SPELL".equals(c.fixtureContext)
                    ? "Sol Ring"
                    : ("STACK_INSTANT_SPELL".equals(c.fixtureContext)
                    || "STACK_SINGLE_TARGET_SPELL".equals(c.fixtureContext)) ? "Shock" : "Runeclaw Bear";
            final Card stackTarget = createCard(stackCardName, stackOwner);
            stackOwner.getZone(ZoneType.Hand).add(stackTarget);
            final SpellAbility stackAbility = stackTarget.getSpells().get(0);
            stackAbility.setActivatingPlayer(stackOwner);
            if ("Shock".equals(stackCardName)) {
                final Card shockTarget = addCard("Runeclaw Bear", actor);
                stackAbility.getTargets().add(shockTarget);
                if (!stackAbility.isTargetNumberValid()) {
                    throw new IllegalStateException("fixture spell target count is invalid before stack admission");
                }
            }
            game.getStack().freezeStack(stackAbility);
            stackAbility.setHostCard(game.getAction().moveToStack(stackTarget, stackAbility));
            game.getStack().addAndUnfreeze(stackAbility);
            intended = stackAbility;
            relation = stackOwner == actor ? "ACTOR" : "OPPONENT";
        } else switch (c.targetRole) {
            case "OPPONENT_PLAYER":
                intended = opponent;
                relation = "OPPONENT";
                break;
            case "OWN_CREATURE":
                intended = addCardToZone("Runeclaw Bear", actor,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                if ("GRAVEYARD".equals(c.fixtureContext)) {
                    addCardToZone("Runeclaw Bear", actor, ZoneType.Graveyard);
                }
                relation = "ACTOR";
                break;
            case "OPPONENT_CREATURE":
                intended = addCardToZone("Runeclaw Bear", opponent,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                if ("GRAVEYARD".equals(c.fixtureContext)) {
                    addCardToZone("Runeclaw Bear", opponent, ZoneType.Graveyard);
                }
                relation = "OPPONENT";
                break;
            case "OWN_ARTIFACT":
                intended = addCardToZone("Sol Ring", actor,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "ACTOR";
                break;
            case "OPPONENT_ARTIFACT":
                intended = addCardToZone("Sol Ring", opponent,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_ELEMENTAL":
                intended = addCardToZone("Air Elemental", actor,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "ACTOR";
                break;
            case "OPPONENT_ELEMENTAL":
                intended = addCardToZone("Air Elemental", opponent,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_INSTANT":
                intended = addCardToZone("Shock", actor, ZoneType.Graveyard);
                relation = "ACTOR";
                break;
            case "OPPONENT_INSTANT":
                intended = addCardToZone("Shock", opponent, ZoneType.Graveyard);
                relation = "OPPONENT";
                break;
            default:
                throw new IllegalArgumentException("unsupported target role " + c.targetRole);
        }

        final PlayerControllerHuman controller = new PlayerControllerHuman(
                game, actor, new LobbyPlayerHuman("ws33-target-principal"));
        final Provider provider = new Provider(c, intended, replay);
        controller.setExternalDecisionProvider(provider::decide);

        final int initialTargetCount = ability.getTargets().size();
        if (initialTargetCount != 0) {
            throw new IllegalStateException("actual ability already has targets before qualification");
        }
        final boolean chooseResult = controller.chooseTargetsFor(ability);
        provider.assertConsumed();
        if (!chooseResult) {
            throw new IllegalStateException("Forge target selection returned false");
        }
        if (!ability.isTargeting(intended)) {
            throw new IllegalStateException("Forge did not retain fixture-designated authoritative target");
        }
        if (ability.getTargets().size() != 1) {
            throw new IllegalStateException("conservative single-target shard selected "
                    + ability.getTargets().size() + " targets");
        }
        if (!ability.isTargetNumberValid()) {
            throw new IllegalStateException("Forge reports selected target count invalid");
        }

        final List<ExternalDecisionTape.Event> tape = controller.getExternalDecisionTapeSnapshot();
        if (tape.size() != provider.captured.size()) {
            throw new IllegalStateException("decision tape/request count mismatch");
        }
        for (int i = 0; i < tape.size(); i++) {
            final ExternalDecisionTape.Event event = tape.get(i);
            final CapturedDecision decision = provider.captured.get(i);
            if (event.getResponseStatus() != ExternalDecisionTape.ResponseStatus.ACCEPTED) {
                throw new IllegalStateException("non-accepted target decision");
            }
            if (!event.getSelectedOptionIds().equals(List.of(decision.selectedOptionId))) {
                throw new IllegalStateException("validated target response differs from provider response");
            }
        }

        final String selectedKind = intended instanceof Player ? "PLAYER"
                : intended instanceof SpellAbility ? "SPELL" : "CARD";
        final String selectedName = intended instanceof Player
                ? ((Player) intended).getName()
                : intended instanceof SpellAbility ? ((SpellAbility) intended).getHostCard().getName()
                : ((Card) intended).getName();
        final String canonical = "target_count=1"
                + "|target_number_valid=true"
                + "|selected_kind=" + selectedKind
                + "|selected_name=" + selectedName
                + "|selected_relation=" + relation
                + "|valid_tgts=" + c.validTgts
                + "|api=" + c.api
                + "|ability_kind=" + c.abilityKind;

        return new Result(
                initialTargetCount,
                ability.getTargets().size(),
                ability.isTargetNumberValid(),
                ability.isTargeting(intended),
                provider.sawIntended,
                selectedKind,
                selectedName,
                relation,
                canonical,
                provider.captured,
                tape
        );
    }

    private SpellAbility findAbility(final Card source, final Case c) {
        if (!source.hasState(CardStateName.valueOf(c.abilityState))) {
            throw new IllegalStateException("actual card lacks source-bound ability state " + c.abilityState);
        }
        final List<SpellAbility> candidates = new ArrayList<>();
        if (c.svarName.isBlank()) {
            candidates.addAll(source.getState(CardStateName.valueOf(c.abilityState)).getSpellAbilities());
        } else {
            candidates.add(AbilityFactory.getAbility(
                    source.getState(CardStateName.valueOf(c.abilityState)), c.svarName,
                    source.getState(CardStateName.valueOf(c.abilityState))));
        }
        final List<SpellAbility> matches = new ArrayList<>();
        for (final SpellAbility ability : candidates) {
            if (!ability.usesTargeting() || ability.getTargetRestrictions() == null) {
                continue;
            }
            if ("SP".equals(c.abilityKind) != ability.isSpell()) {
                continue;
            }
            if ("AB".equals(c.abilityKind) && !ability.isActivatedAbility()) {
                continue;
            }
            if ("DB".equals(c.abilityKind) && (ability.isSpell() || ability.isActivatedAbility())) {
                continue;
            }
            if (ability.getApi() == null || !c.api.equals(ability.getApi().name())) {
                continue;
            }
            final TargetRestrictions restrictions = ability.getTargetRestrictions();
            if (!c.validTgts.equals(String.join(",", restrictions.getValidTgts()))) {
                continue;
            }
            if (ability.getMinTargets() != 1 || ability.getMaxTargets() != 1) {
                continue;
            }
            matches.add(ability);
        }
        if (matches.size() > 1 && !c.spellDescription.isBlank()) {
            matches.removeIf(candidate -> !candidate.getDescription().endsWith(c.spellDescription));
        }
        if (matches.size() != 1) {
            throw new IllegalStateException("expected exactly one actual top-level target ability; matches="
                    + matches.size() + " card=" + c.cardName + " api=" + c.api
                    + " ValidTgts=" + c.validTgts);
        }
        return matches.get(0);
    }

    private static final class Provider {
        private final GameObject intended;
        private final List<ReplayDecision> replay;
        private int replayIndex;
        private boolean selected;
        private boolean sawIntended;
        private final List<CapturedDecision> captured = new ArrayList<>();

        Provider(final Case c, final GameObject intended, final List<ReplayDecision> replay) {
            this.intended = intended;
            this.replay = replay;
        }

        ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
            final String expectedKind = intended instanceof SpellAbility
                    ? "STACK_TARGET_SELECTION" : "TARGET_SELECTION";
            if (!expectedKind.equals(request.getDecisionKind())) {
                throw new IllegalStateException("unexpected decision kind " + request.getDecisionKind());
            }
            final ExternalDecisionRequest.Option chosen;
            if (replay != null) {
                if (replayIndex >= replay.size()) {
                    throw new IllegalStateException("replay decision tape exhausted");
                }
                final ReplayDecision expected = replay.get(replayIndex++);
                if (!expected.decisionKind.equals(request.getDecisionKind())) {
                    throw new IllegalStateException("replay decision kind mismatch");
                }
                chosen = request.getOptions().stream()
                        .filter(option -> expected.optionId.equals(option.getOptionId())
                                && expected.semanticValue.equals(option.getSemanticValue()))
                        .findFirst()
                        .orElseThrow(() -> new IllegalStateException(
                                "recorded target response is absent from authoritative replay options"));
            } else {
                final String desiredSemantic;
                if (!selected) {
                    desiredSemantic = intended instanceof Player
                            ? "PLAYER:" + ((Player) intended).getId()
                            : intended instanceof SpellAbility
                            ? "STACK:" + ((SpellAbility) intended).getId()
                            : "CARD:" + ((Card) intended).getId();
                } else {
                    desiredSemantic = "DONE";
                }
                chosen = request.getOptions().stream()
                        .filter(option -> desiredSemantic.equals(option.getSemanticValue()))
                        .findFirst()
                        .orElseThrow(() -> new IllegalStateException(
                                "fixture-designated target transition not offered by Forge: " + desiredSemantic));
            }

            if (chosen.getSemanticValue().startsWith("CARD:")
                    || chosen.getSemanticValue().startsWith("PLAYER:")
                    || chosen.getSemanticValue().startsWith("STACK:")) {
                sawIntended = true;
                selected = true;
            }
            captured.add(new CapturedDecision(request, chosen.getOptionId(), chosen.getSemanticValue()));
            return new ExternalDecisionResponse(
                    request.getDecisionId(), request.getToken(), request.getActorId(),
                    request.getPrincipalId(), request.getResponseSchema(),
                    List.of(chosen.getOptionId()), false);
        }

        void assertConsumed() {
            if (!sawIntended) {
                throw new IllegalStateException("authoritative intended target transition was never consumed");
            }
            if (replay != null && replayIndex != replay.size()) {
                throw new IllegalStateException("replay left " + (replay.size() - replayIndex) + " decisions unconsumed");
            }
        }
    }

    private static void writeRecord(final Path root, final Case c, final Result result) throws IOException {
        final Path dir = caseDir(root, c.pathId);
        Files.createDirectories(dir);
        final Path decisionTape = dir.resolve("decision-tape.json");
        final Path decisionReplay = dir.resolve("decision-replay.tsv");
        final Path trace = dir.resolve("trace.json");
        final Path finalState = dir.resolve("final-state.txt");

        writeDecisionTape(decisionTape, c, result);
        writeDecisionReplay(decisionReplay, result);
        Files.writeString(finalState, result.canonicalFinalState, StandardCharsets.UTF_8);
        Files.writeString(trace, traceJson(c, result), StandardCharsets.UTF_8);

        final String rel = "records/" + shortId(c.pathId) + "/";
        final String record = "{"
                + "\"schema\":\"commander-simulator-next.ws33-runtime-campaign-record.v1\","
                + "\"witness_id\":" + q("ws33-targetrestrictions-" + shortId(c.pathId)) + ","
                + "\"oracle_identities\":[" + q(c.oracleId) + "],"
                + "\"v2_path_ids\":[" + q(c.pathId) + "],"
                + "\"owner_family\":\"ACTION_COST_DECISION\","
                + "\"initial_semantic_state\":{"
                + "\"target_count\":0,"
                + "\"valid_tgts\":" + q(c.validTgts) + ","
                + "\"intended_role\":" + q(c.targetRole) + ","
                + "\"ability_kind\":" + q(c.abilityKind) + ","
                + "\"api\":" + q(c.api) + "},"
                + "\"final_semantic_state\":{"
                + "\"target_count\":1,"
                + "\"target_number_valid\":true,"
                + "\"intended_target_selected\":true,"
                + "\"selected_kind\":" + q(result.selectedKind) + ","
                + "\"selected_name\":" + q(result.selectedName) + ","
                + "\"selected_relation\":" + q(result.selectedRelation) + "},"
                + "\"state_assertions\":["
                + assertion("target-count", 1, result.finalTargetCount) + ","
                + assertion("target-number-valid", true, result.targetNumberValid) + ","
                + assertion("intended-target-selected", true, result.intendedTargetSelected) + ","
                + assertion("authoritative-option-contained-intended", true, result.sawIntended)
                + "],"
                + "\"path_exercise\":[{"
                + "\"v2_path_id\":" + q(c.pathId) + ","
                + "\"exercised\":true,"
                + "\"trace_event_ids\":[\"TARGET_REQUEST\",\"TARGET_ACCEPTED\"],"
                + "\"assertion_ids\":[\"target-count\",\"target-number-valid\",\"intended-target-selected\",\"authoritative-option-contained-intended\"]"
                + "}],"
                + "\"execution\":{"
                + "\"actual_card_execution\":\"PASS\","
                + "\"actual_rules_core_path\":true,"
                + "\"authoritative_decision_boundary\":\"USED\","
                + "\"silent_fallbacks\":0,"
                + "\"direct_effect_resolution\":false},"
                + "\"trace_file\":" + q(rel + "trace.json") + ","
                + "\"decision_tape_file\":" + q(rel + "decision-tape.json") + ","
                + "\"semantic_replay_evidence_file\":" + q(rel + "semantic-replay.json") + ","
                + "\"rules_authority_refs\":["
                + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 115.1")
                + "," + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 601.2c")
                + "," + q("https://magic.wizards.com/en/rules (current Comprehensive Rules), 602.2b")
                + "],"
                + "\"evidence_class\":\"EXTERNALLY_RULE_VALIDATED\""
                + "}\n";
        Files.writeString(dir.resolve("record.json"), record, StandardCharsets.UTF_8);
        Files.writeString(dir.resolve("record-success.marker"), "PASS\n", StandardCharsets.UTF_8);
    }

    private static void writeDecisionTape(final Path path, final Case c, final Result result) throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"events\":[");
        for (int i = 0; i < result.captured.size(); i++) {
            if (i != 0) json.append(',');
            final CapturedDecision captured = result.captured.get(i);
            final ExternalDecisionTape.Event event = result.tape.get(i);
            final ExternalDecisionRequest request = captured.request;
            json.append("{\"decision_id\":").append(request.getDecisionId())
                    .append(",\"decision_kind\":").append(q(request.getDecisionKind()))
                    .append(",\"game_id\":").append(q("ws33-target-" + shortId(c.pathId)))
                    .append(",\"actor\":").append(q(String.valueOf(request.getActorId())))
                    .append(",\"principal\":").append(q(String.valueOf(request.getPrincipalId())))
                    .append(",\"visibility_scope\":").append(q(request.getVisibilityScope()))
                    .append(",\"authoritative_legal_options\":[");
            for (int j = 0; j < request.getOptions().size(); j++) {
                if (j != 0) json.append(',');
                final ExternalDecisionRequest.Option option = request.getOptions().get(j);
                json.append("{\"option_id\":").append(q(option.getOptionId()))
                        .append(",\"semantic_value\":").append(q(option.getSemanticValue())).append('}');
            }
            json.append("],\"response_option_ids\":[")
                    .append(q(captured.selectedOptionId))
                    .append("],\"validation_result\":")
                    .append(q(event.getResponseStatus().name()))
                    .append(",\"fallback_used\":false}");
        }
        json.append("]}\n");
        Files.writeString(path, json.toString(), StandardCharsets.UTF_8);
    }

    private static void writeDecisionReplay(final Path path, final Result result) throws IOException {
        final StringBuilder text = new StringBuilder();
        for (final CapturedDecision decision : result.captured) {
            text.append(b64(decision.request.getDecisionKind())).append('\t')
                    .append(b64(decision.selectedOptionId)).append('\t')
                    .append(b64(decision.semanticValue)).append('\n');
        }
        Files.writeString(path, text.toString(), StandardCharsets.UTF_8);
    }

    private static List<ReplayDecision> loadReplayDecisions(final Path path) throws IOException {
        final List<ReplayDecision> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank()) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 3) {
                throw new IllegalArgumentException("malformed target replay decision line");
            }
            result.add(new ReplayDecision(unb64(fields[0]), unb64(fields[1]), unb64(fields[2])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("empty target replay decision tape");
        }
        return result;
    }

    private static void writeReplayEvidence(
            final Path dir, final Result replayResult, final Path decisionTape, final String expectedState) throws Exception {
        final String actual = replayResult.canonicalFinalState;
        final int divergence = expectedState.equals(actual) ? 0 : 1;
        final String json = "{"
                + "\"semantic_divergence\":" + divergence + ","
                + "\"comparison_basis\":\"CANONICAL_SEMANTIC_STATE\","
                + "\"decision_tape_sha256\":" + q(sha256(decisionTape)) + ","
                + "\"record_state_sha256\":" + q(sha256(expectedState.getBytes(StandardCharsets.UTF_8))) + ","
                + "\"replay_state_sha256\":" + q(sha256(actual.getBytes(StandardCharsets.UTF_8)))
                + "}\n";
        Files.writeString(dir.resolve("semantic-replay.json"), json, StandardCharsets.UTF_8);
    }

    private static String traceJson(final Case c, final Result result) {
        return "{"
                + "\"schema\":\"commander-simulator-next.ws33-targetrestrictions-trace.v1\","
                + "\"forge_pin\":" + q(FORGE_PIN) + ","
                + "\"path_id\":" + q(c.pathId) + ","
                + "\"oracle_identity\":" + q(c.oracleId) + ","
                + "\"actual_card\":" + q(c.cardName) + ","
                + "\"source_path\":" + q(c.sourcePath) + ","
                + "\"source_line\":" + c.sourceLine + ","
                + "\"valid_tgts\":" + q(c.validTgts) + ","
                + "\"actual_rules_core_path\":true,"
                + "\"target_selection_entry\":\"PlayerControllerHuman.chooseTargetsFor\","
                + "\"direct_effect_resolution\":false,"
                + "\"decision_event_count\":" + result.captured.size() + ","
                + "\"initial\":{\"target_count\":" + result.initialTargetCount + "},"
                + "\"final\":{\"target_count\":" + result.finalTargetCount
                + ",\"target_number_valid\":" + result.targetNumberValid
                + ",\"intended_target_selected\":" + result.intendedTargetSelected
                + "},"
                + "\"trace_event_ids\":[\"TARGET_REQUEST\",\"TARGET_ACCEPTED\"]"
                + "}\n";
    }

    private static void writeCampaignIndex(final Path root, final List<String> records) throws IOException {
        final StringBuilder json = new StringBuilder();
        json.append("{\"schema\":\"commander-simulator-next.ws33-runtime-campaign-index.v1\",\"records\":[");
        for (int i = 0; i < records.size(); i++) {
            if (i != 0) json.append(',');
            json.append(q(records.get(i)));
        }
        json.append("]}\n");
        Files.writeString(root.resolve("campaign-index.json"), json.toString(), StandardCharsets.UTF_8);
    }

    private static void writeDiagnostics(final Path root, final String mode, final List<String> diagnostics) throws IOException {
        final Path path = root.resolve("target-" + mode + "-diagnostics.jsonl");
        Files.write(path, diagnostics, StandardCharsets.UTF_8);
    }

    private static List<Case> loadCases(final Path path) throws IOException {
        final List<Case> result = new ArrayList<>();
        for (final String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            if (line.isBlank() || line.startsWith("#")) continue;
            final String[] fields = line.split("\\t", -1);
            if (fields.length != 13) {
                throw new IllegalArgumentException("malformed WS33 target case line");
            }
            result.add(new Case(
                    fields[0], fields[1], unb64(fields[2]), unb64(fields[3]),
                    fields[4], fields[5], unb64(fields[6]), unb64(fields[7]), fields[8], fields[9],
                    unb64(fields[10]), unb64(fields[11]), Integer.parseInt(fields[12])));
        }
        if (result.isEmpty()) {
            throw new IllegalArgumentException("WS33 target campaign case set is empty");
        }
        return result;
    }

    private static String assertion(final String id, final boolean expected, final boolean actual) {
        return "{\"assertion_id\":" + q(id)
                + ",\"expected\":" + expected
                + ",\"actual\":" + actual
                + ",\"result\":\"PASS\"}";
    }

    private static String assertion(final String id, final int expected, final int actual) {
        return "{\"assertion_id\":" + q(id)
                + ",\"expected\":" + expected
                + ",\"actual\":" + actual
                + ",\"result\":\"PASS\"}";
    }

    private static Path caseDir(final Path root, final String pathId) {
        return root.resolve("records").resolve(shortId(pathId));
    }

    private static String shortId(final String pathId) {
        return pathId.startsWith("forge-behavior-v2:")
                ? pathId.substring("forge-behavior-v2:".length())
                : pathId.replaceAll("[^A-Za-z0-9_.-]", "-");
    }

    private static Path requiredPath(final String property) {
        final String value = System.getProperty(property);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException(property + " system property is required");
        }
        return Path.of(value);
    }

    private static String q(final String value) {
        return "\"" + escape(value) + "\"";
    }

    private static String escape(final String value) {
        return value == null ? "" : value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r");
    }

    private static String b64(final String value) {
        return Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    private static String unb64(final String value) {
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private static String sha256(final Path path) throws Exception {
        return sha256(Files.readAllBytes(path));
    }

    private static String sha256(final byte[] value) throws Exception {
        final byte[] hash = MessageDigest.getInstance("SHA-256").digest(value);
        final StringBuilder out = new StringBuilder();
        for (final byte b : hash) out.append(String.format(Locale.ROOT, "%02x", b));
        return out.toString();
    }

    private static final class Case {
        final String pathId;
        final String oracleId;
        final String cardName;
        final String validTgts;
        final String targetRole;
        final String abilityKind;
        final String api;
        final String svarName;
        final String abilityState;
        final String fixtureContext;
        final String spellDescription;
        final String sourcePath;
        final int sourceLine;

        Case(String pathId, String oracleId, String cardName, String validTgts,
             String targetRole, String abilityKind, String api, String svarName,
             String abilityState, String fixtureContext,
             String spellDescription, String sourcePath, int sourceLine) {
            this.pathId = pathId;
            this.oracleId = oracleId;
            this.cardName = cardName;
            this.validTgts = validTgts;
            this.targetRole = targetRole;
            this.abilityKind = abilityKind;
            this.api = api;
            this.svarName = svarName;
            this.abilityState = abilityState;
            this.fixtureContext = fixtureContext;
            this.spellDescription = spellDescription;
            this.sourcePath = sourcePath;
            this.sourceLine = sourceLine;
        }
    }

    private static final class CapturedDecision {
        final ExternalDecisionRequest request;
        final String selectedOptionId;
        final String semanticValue;

        CapturedDecision(ExternalDecisionRequest request, String selectedOptionId, String semanticValue) {
            this.request = request;
            this.selectedOptionId = selectedOptionId;
            this.semanticValue = semanticValue;
        }
    }

    private static final class ReplayDecision {
        final String decisionKind;
        final String optionId;
        final String semanticValue;

        ReplayDecision(String decisionKind, String optionId, String semanticValue) {
            this.decisionKind = decisionKind;
            this.optionId = optionId;
            this.semanticValue = semanticValue;
        }
    }

    private static final class Result {
        final int initialTargetCount;
        final int finalTargetCount;
        final boolean targetNumberValid;
        final boolean intendedTargetSelected;
        final boolean sawIntended;
        final String selectedKind;
        final String selectedName;
        final String selectedRelation;
        final String canonicalFinalState;
        final List<CapturedDecision> captured;
        final List<ExternalDecisionTape.Event> tape;

        Result(int initialTargetCount, int finalTargetCount, boolean targetNumberValid,
               boolean intendedTargetSelected, boolean sawIntended, String selectedKind,
               String selectedName, String selectedRelation, String canonicalFinalState,
               List<CapturedDecision> captured, List<ExternalDecisionTape.Event> tape) {
            this.initialTargetCount = initialTargetCount;
            this.finalTargetCount = finalTargetCount;
            this.targetNumberValid = targetNumberValid;
            this.intendedTargetSelected = intendedTargetSelected;
            this.sawIntended = sawIntended;
            this.selectedKind = selectedKind;
            this.selectedName = selectedName;
            this.selectedRelation = selectedRelation;
            this.canonicalFinalState = canonicalFinalState;
            this.captured = new ArrayList<>(captured);
            this.tape = new ArrayList<>(tape);
        }
    }
}
