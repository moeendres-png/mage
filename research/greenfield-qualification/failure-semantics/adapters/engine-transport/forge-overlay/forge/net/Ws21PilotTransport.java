package forge.net;

import forge.gamemodes.match.input.ExternalDecisionProvider;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTransportException;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.concurrent.atomic.AtomicLong;

/** Actual loopback external-pilot request/response channel for WS21. */
public final class Ws21PilotTransport implements ExternalDecisionProvider {
    private static final AtomicLong requestsWritten = new AtomicLong();
    private static final AtomicLong responsesDecoded = new AtomicLong();

    private final String host;
    private final int port;

    public Ws21PilotTransport(final String host, final int port) {
        this.host = host;
        this.port = port;
    }

    public static void resetProbe() {
        requestsWritten.set(0L);
        responsesDecoded.set(0L);
    }

    public static long requestsWritten() { return requestsWritten.get(); }
    public static long responsesDecoded() { return responsesDecoded.get(); }

    @Override
    public ExternalDecisionResponse decide(final ExternalDecisionRequest request) {
        ExternalDecisionTransportException.Stage stage = ExternalDecisionTransportException.Stage.CONNECT;
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, port), 5000);
            socket.setSoTimeout(5000);
            stage = ExternalDecisionTransportException.Stage.WRITE_REQUEST;
            final DataOutputStream out = new DataOutputStream(new BufferedOutputStream(socket.getOutputStream()));
            Ws21PilotWire.writeRequest(out, request);
            out.flush();
            requestsWritten.incrementAndGet();

            stage = ExternalDecisionTransportException.Stage.DECODE_RESPONSE;
            final DataInputStream in = new DataInputStream(new BufferedInputStream(socket.getInputStream()));
            final ExternalDecisionResponse response = Ws21PilotWire.readResponse(in);
            responsesDecoded.incrementAndGet();
            return response;
        } catch (IOException failure) {
            throw new ExternalDecisionTransportException(stage, request.getDecisionId(), request.getPrincipalId());
        }
    }
}
