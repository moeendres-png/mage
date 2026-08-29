package forge.net;

import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/** Minimal framed wire used by the WS21 external-pilot transport witness. */
final class Ws21PilotWire {
    static final String REQUEST_MAGIC = "WS21_REQUEST_V1";
    static final String RESPONSE_MAGIC = "WS21_RESPONSE_V1";
    private static final int MAX_OPTIONS = 10000;

    private Ws21PilotWire() { }

    static void writeRequest(final DataOutput out, final ExternalDecisionRequest request) throws IOException {
        out.writeUTF(REQUEST_MAGIC);
        out.writeLong(request.getDecisionId());
        out.writeLong(request.getToken());
        out.writeUTF(request.getDecisionKind());
        out.writeInt(request.getActorId());
        out.writeInt(request.getPrincipalId());
        out.writeUTF(request.getVisibilityScope());
        out.writeUTF(request.getResponseSchema());
        out.writeInt(request.getMinimumSelection());
        out.writeInt(request.getMaximumSelection());
        out.writeBoolean(request.isCancelAllowed());
        out.writeInt(request.getOptions().size());
        for (final ExternalDecisionRequest.Option option : request.getOptions()) {
            out.writeUTF(option.getOptionId());
            out.writeUTF(option.getEntityKind());
            out.writeInt(option.getEntityId());
            out.writeBoolean(option.isEntityBacked());
            out.writeUTF(option.getSemanticValue());
        }
    }

    static RequestFrame readRequest(final DataInput in) throws IOException {
        if (!REQUEST_MAGIC.equals(in.readUTF())) {
            throw new IOException("invalid request frame");
        }
        final long decisionId = in.readLong();
        final long token = in.readLong();
        final String decisionKind = in.readUTF();
        final int actorId = in.readInt();
        final int principalId = in.readInt();
        final String visibilityScope = in.readUTF();
        final String responseSchema = in.readUTF();
        final int min = in.readInt();
        final int max = in.readInt();
        final boolean cancelAllowed = in.readBoolean();
        final int count = in.readInt();
        if (count < 0 || count > MAX_OPTIONS) {
            throw new IOException("invalid request option count");
        }
        final List<String> optionIds = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            optionIds.add(in.readUTF());
            in.readUTF();
            in.readInt();
            in.readBoolean();
            in.readUTF();
        }
        return new RequestFrame(decisionId, token, decisionKind, actorId, principalId,
                visibilityScope, responseSchema, min, max, cancelAllowed, optionIds);
    }

    static void writeResponse(final DataOutput out, final RequestFrame request,
                              final String responseSchema, final List<String> selected,
                              final boolean cancel) throws IOException {
        out.writeUTF(RESPONSE_MAGIC);
        out.writeLong(request.decisionId);
        out.writeLong(request.token);
        out.writeInt(request.actorId);
        out.writeInt(request.principalId);
        out.writeUTF(responseSchema);
        out.writeBoolean(cancel);
        out.writeInt(selected.size());
        for (final String optionId : selected) {
            out.writeUTF(optionId);
        }
    }

    static ExternalDecisionResponse readResponse(final DataInput in) throws IOException {
        if (!RESPONSE_MAGIC.equals(in.readUTF())) {
            throw new IOException("invalid response frame");
        }
        final long decisionId = in.readLong();
        final long token = in.readLong();
        final int actorId = in.readInt();
        final int principalId = in.readInt();
        final String schema = in.readUTF();
        final boolean cancel = in.readBoolean();
        final int count = in.readInt();
        if (count < 0 || count > MAX_OPTIONS) {
            throw new IOException("invalid response option count");
        }
        final List<String> selected = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            selected.add(in.readUTF());
        }
        return new ExternalDecisionResponse(decisionId, token, actorId, principalId, schema, selected, cancel);
    }

    static final class RequestFrame {
        final long decisionId;
        final long token;
        final String decisionKind;
        final int actorId;
        final int principalId;
        final String visibilityScope;
        final String responseSchema;
        final int min;
        final int max;
        final boolean cancelAllowed;
        final List<String> optionIds;

        RequestFrame(final long decisionId, final long token, final String decisionKind,
                     final int actorId, final int principalId, final String visibilityScope,
                     final String responseSchema, final int min, final int max,
                     final boolean cancelAllowed, final List<String> optionIds) {
            this.decisionId = decisionId;
            this.token = token;
            this.decisionKind = decisionKind;
            this.actorId = actorId;
            this.principalId = principalId;
            this.visibilityScope = visibilityScope;
            this.responseSchema = responseSchema;
            this.min = min;
            this.max = max;
            this.cancelAllowed = cancelAllowed;
            this.optionIds = List.copyOf(optionIds);
        }
    }
}
