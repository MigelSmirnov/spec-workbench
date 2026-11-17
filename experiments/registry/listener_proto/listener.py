"""Prototype of `instance_lifecycle`'s listener (State 3/6, 2026-11-17).

What the spec says the listener does, and what this prototype tests:

- HTTP framing of both surfaces is one implementation. A request whose
  `Content-Length` or `Transfer-Encoding` header is malformed is refused from
  its headers alone, its connection closed; it reaches no surface.
- The body is handed on as a stream that ends where HTTP's framing ends it:
  after `Content-Length` bytes, or at a chunked body's last chunk. The
  listener never reads ahead; a short body or a malformed chunk is a failure
  of the stream that its reader sees.
- Each read of the socket waits at most `LISTENER_READ_TIMEOUT_SECONDS` for
  progress (the socket's own timeout), not a deadline for the request.
- A request answered before its body was read to its framed end has the
  remainder discarded unread and its connection closed.

`CLOSE` picks how that last close is made, which is the question the
prototype puts to real clients:
  "abrupt"    close() at once (what "discarded unread" says literally);
  "lingering" shutdown(SHUT_WR), then read and drop what the client still
              sends for a bounded time and size, then close().

Not generated code: a throwaway experiment.
"""
from __future__ import annotations

import re
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTENER_READ_TIMEOUT_SECONDS = 30.0


class StreamFailure(OSError):
    """The body's stream failed: it ended before its framing said, a chunk
    was malformed, or the socket's wait for progress ran out."""


class ContentLengthBody:
    def __init__(self, raw, length: int) -> None:
        self._raw, self.left = raw, length

    def read(self, size: int) -> bytes:
        if self.left <= 0 or size <= 0:
            return b""
        try:
            chunk = self._raw.read1(min(size, self.left))
        except (TimeoutError, socket.timeout) as error:
            raise StreamFailure("read timeout") from error
        if not chunk:
            raise StreamFailure("body ended before Content-Length")
        self.left -= len(chunk)
        return chunk

    @property
    def at_end(self) -> bool:
        return self.left <= 0


_CHUNK_SIZE = re.compile(rb"^([0-9A-Fa-f]{1,8})(?:;[^\r\n]*)?\r\n$")


class ChunkedBody:
    def __init__(self, raw) -> None:
        self._raw, self._left, self._done = raw, 0, False

    def _line(self) -> bytes:
        try:
            line = self._raw.readline(1024)
        except (TimeoutError, socket.timeout) as error:
            raise StreamFailure("read timeout") from error
        if not line.endswith(b"\r\n"):
            raise StreamFailure("malformed or cut chunk line")
        return line

    def read(self, size: int) -> bytes:
        if self._done or size <= 0:
            return b""
        if self._left == 0:
            match = _CHUNK_SIZE.match(self._line())
            if not match:
                raise StreamFailure("malformed chunk size")
            self._left = int(match.group(1), 16)
            if self._left == 0:
                while self._line() != b"\r\n":  # trailers, dropped
                    pass
                self._done = True
                return b""
        try:
            chunk = self._raw.read1(min(size, self._left))
        except (TimeoutError, socket.timeout) as error:
            raise StreamFailure("read timeout") from error
        if not chunk:
            raise StreamFailure("body ended inside a chunk")
        self._left -= len(chunk)
        if self._left == 0 and self._line() != b"\r\n":
            raise StreamFailure("chunk not followed by CRLF")
        return chunk

    @property
    def at_end(self) -> bool:
        return self._done


def framing_of(headers) -> tuple[str, int | None] | None:
    """('length', n) / ('chunked', None) / ('none', None), or None when the
    framing headers are malformed (refused from the headers alone)."""
    lengths = headers.get_all("Content-Length") or []
    encodings = headers.get_all("Transfer-Encoding") or []
    if encodings:
        if lengths:
            return None                      # both: request smuggling shape
        values = [v.strip().lower() for e in encodings for v in e.split(",")]
        if values != ["chunked"]:
            return None                      # only plain chunked is served
        return ("chunked", None)
    if not lengths:
        return ("none", None)
    if len(set(v.strip() for v in lengths)) != 1:
        return None
    text = lengths[0].strip()
    if not text.isdigit() or len(text) > 18:   # no sign, no spaces, no hex
        return None
    return ("length", int(text))


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = LISTENER_READ_TIMEOUT_SECONDS     # per read of the socket
    CLOSE = "abrupt"
    LINGER_SECONDS = 2.0
    LINGER_BYTES = 64 * 1024 * 1024
    surface = None                               # (handler, body) -> (status, bytes)

    def log_message(self, *args):
        pass

    def _serve(self):
        framing = framing_of(self.headers)
        if framing is None:
            self._answer(400, b"bad framing")
            self.close_connection = True
            self.server.events.append(("refused_framing", self.path))
            return
        kind, length = framing
        if kind == "length":
            body = ContentLengthBody(self.rfile, length)
        elif kind == "chunked":
            body = ChunkedBody(self.rfile)
        else:
            body = ContentLengthBody(self.rfile, 0)
        status, payload = type(self).surface(self, body)
        if not body.at_end:
            self.close_connection = True
        self._answer(status, payload)
        self.server.events.append(("answered", self.path, status, body.at_end))

    do_POST = do_PUT = do_GET = _serve

    def _answer(self, status: int, payload: bytes) -> None:
        try:
            self.send_response(status)
            self.send_header("Content-Length", str(len(payload)))
            if self.close_connection:
                self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
            self.wfile.flush()
        except OSError:
            pass

    def handle_expect_100(self):
        # A surface decides from the headers whether it wants the body; the
        # prototype always lets the client send it, as a browser does anyway.
        return super().handle_expect_100()


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, handler):
        super().__init__(("127.0.0.1", 0), handler)
        self.events = []

    def shutdown_request(self, request):
        if self.RequestHandlerClass.CLOSE == "lingering":
            try:
                request.shutdown(socket.SHUT_WR)
                request.settimeout(0.2)
                deadline = time.monotonic() + self.RequestHandlerClass.LINGER_SECONDS
                dropped = 0
                while (time.monotonic() < deadline
                       and dropped < self.RequestHandlerClass.LINGER_BYTES):
                    try:
                        data = request.recv(65536)
                    except socket.timeout:
                        continue
                    if not data:
                        break
                    dropped += len(data)
            except OSError:
                pass
            self.close_request(request)
        else:
            self.close_request(request)          # close() with bytes unread
