"""Run: python -I -m pytest -q -p no:cacheprovider experiments/registry/listener_proto"""
from __future__ import annotations

import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from listener import Handler, Server, StreamFailure  # noqa: E402


def serve(surface, close="abrupt", timeout=2.0):
    handler = type("H", (Handler,), {"surface": staticmethod(surface),
                                     "CLOSE": close, "timeout": timeout})
    server = Server(handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def read_all(body):
    data = bytearray()
    while chunk := body.read(65536):
        data += chunk
    return bytes(data)


def echo(handler, body):
    try:
        return 200, read_all(body)
    except StreamFailure as failure:
        handler.server.events.append(("stream_failure", str(failure)))
        return 422, b"unreadable"


def refuse_unread(handler, body):
    return 422, b"refused before the body"


def raw(server, data: bytes, wait=1.0) -> bytes:
    with socket.create_connection(("127.0.0.1", server.server_port)) as s:
        s.sendall(data)
        s.settimeout(wait)
        out = bytearray()
        try:
            while chunk := s.recv(65536):
                out += chunk
        except socket.timeout:
            pass
        return bytes(out)


def statuses(reply: bytes) -> list[int]:
    return [int(m) for m in re.findall(rb"HTTP/1\.1 (\d{3}) ", reply)]


# ------------------------------------------------- framing from headers alone
@pytest.mark.parametrize("headers", [
    b"Content-Length: 5x\r\n",
    b"Content-Length: +5\r\n",
    b"Content-Length: 0x5\r\n",
    b"Content-Length: 5\r\nContent-Length: 6\r\n",
    b"Content-Length: 5\r\nTransfer-Encoding: chunked\r\n",
    b"Transfer-Encoding: gzip, chunked\r\n",
    b"Transfer-Encoding: chunked, identity\r\n",
])
def test_malformed_framing_is_refused_and_reaches_no_surface(headers):
    called = []
    server = serve(lambda h, b: called.append(1) or (200, b""))
    try:
        reply = raw(server, b"POST /x HTTP/1.1\r\nHost: a\r\n" + headers + b"\r\nhello"
                    + b"GET /second HTTP/1.1\r\nHost: a\r\n\r\n")
    finally:
        server.shutdown()
    assert statuses(reply) == [400]          # and not a second answer
    assert called == []


def test_chunked_body_is_read_to_its_last_chunk_and_the_connection_kept():
    server = serve(echo)
    try:
        reply = raw(server, b"POST /a HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n"
                    b"5\r\nhello\r\n6;ext=1\r\n world\r\n0\r\nTrailer: x\r\n\r\n"
                    b"GET /b HTTP/1.1\r\nHost: a\r\n\r\n")
    finally:
        server.shutdown()
    assert statuses(reply) == [200, 200]
    assert b"hello world" in reply


@pytest.mark.parametrize("chunks", [b"zz\r\nhello\r\n", b"5\r\nhelloXX", b"5\r\nhel"])
def test_malformed_or_cut_chunk_is_a_stream_failure_its_reader_sees(chunks):
    server = serve(echo, timeout=0.3)
    try:
        reply = raw(server, b"POST /a HTTP/1.1\r\nHost: a\r\nTransfer-Encoding: chunked\r\n\r\n"
                    + chunks)
    finally:
        server.shutdown()
    assert statuses(reply) == [422]
    assert server.events[0][0] == "stream_failure"


def test_short_content_length_body_is_a_stream_failure():
    server = serve(echo, timeout=0.3)
    try:
        reply = raw(server, b"POST /a HTTP/1.1\r\nHost: a\r\nContent-Length: 10\r\n\r\nabc")
    finally:
        server.shutdown()
    assert statuses(reply) == [422]
    assert server.events[0] == ("stream_failure", "read timeout")


# ------------------------------------------------- unread remainder: no smuggling
def test_answer_before_the_body_closes_and_no_body_byte_is_read_as_a_request():
    server = serve(refuse_unread)
    smuggled = b"GET /smuggled HTTP/1.1\r\nHost: a\r\n\r\n"
    try:
        reply = raw(server, b"POST /a HTTP/1.1\r\nHost: a\r\nContent-Length: %d\r\n\r\n"
                    % len(smuggled) + smuggled)
    finally:
        server.shutdown()
    assert statuses(reply) == [422]
    assert b"Connection: close" in reply
    assert [e[1] for e in server.events] == ["/a"]


# ------------------------------------------------- the per-read progress wait
def test_a_slow_client_that_keeps_sending_is_never_cut():
    server = serve(echo, timeout=0.3)
    body = b"x" * 12
    try:
        with socket.create_connection(("127.0.0.1", server.server_port)) as s:
            s.sendall(b"POST /a HTTP/1.1\r\nHost: a\r\nContent-Length: 12\r\n\r\n")
            for byte in body:                    # 12 x 0.15 s = 1.8 s > 6 timeouts
                time.sleep(0.15)
                s.sendall(bytes([byte]))
            s.settimeout(2)
            reply = b""
            while not reply.endswith(body):
                reply += s.recv(65536)
    finally:
        server.shutdown()
    assert statuses(reply) == [200]


def test_headers_that_stop_close_the_connection_and_reach_no_surface():
    called = []
    server = serve(lambda h, b: called.append(1) or (200, b""), timeout=0.3)
    try:
        with socket.create_connection(("127.0.0.1", server.server_port)) as s:
            s.sendall(b"POST /a HTTP/1.1\r\nHost: a\r\n")
            s.settimeout(2)
            started = time.monotonic()
            reply = s.recv(65536)
            waited = time.monotonic() - started
    finally:
        server.shutdown()
    assert reply == b"" and called == [] and 0.25 < waited < 1.5


# ------------------------------------------------- does the client see the answer?
BIG = 30 * 1024 * 1024


ANSWER = 200_000     # a rendered page; the loss starts near the client's
                     # receive window (~100 KB on loopback, far less over a WAN)


def early_answer_seen_whole(server) -> bool:
    """A browser-like client: sends the whole body without Expect, and reads
    the answer only once it has sent (or failed to send) everything."""
    s = socket.create_connection(("127.0.0.1", server.server_port))
    try:
        s.sendall(b"POST /upload HTTP/1.1\r\nHost: a\r\nContent-Length: %d\r\n\r\n" % BIG)
        try:
            for _ in range(BIG // 65536):
                s.sendall(b"a" * 65536)
        except OSError:
            pass
        s.settimeout(3)
        got = bytearray()
        try:
            while chunk := s.recv(1 << 20):
                got += chunk
        except OSError:
            pass
        return got.startswith(b"HTTP/1.1 422") and len(got) > ANSWER
    finally:
        s.close()


@pytest.mark.parametrize("close", ["abrupt", "lingering"])
def test_answer_before_a_large_body_reaches_a_browser_like_client(close):
    server = serve(lambda h, b: (422, b"r" * ANSWER), close=close)
    try:
        seen = sum(early_answer_seen_whole(server) for _ in range(4))
    finally:
        server.shutdown()
    print(f"\n{close}: whole answer seen {seen}/4")
    if close == "lingering":
        assert seen == 4
    else:
        # The finding: close() with unread bytes sends RST and drops what the
        # kernel had not yet sent; the client gets a cut answer or none.
        assert seen == 0


@pytest.mark.skipif(shutil.which("curl") is None, reason="no curl")
@pytest.mark.parametrize("close", ["abrupt", "lingering"])
def test_answer_before_a_large_body_reaches_curl(close, tmp_path):
    upload = tmp_path / "big.json"
    upload.write_bytes(b"a" * BIG)
    server = serve(refuse_unread, close=close)
    try:
        results = []
        for _ in range(3):
            run = subprocess.run(
                ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-H", "Expect:",
                 "--data-binary", f"@{upload}", f"http://127.0.0.1:{server.server_port}/upload"],
                capture_output=True, text=True, timeout=30)
            results.append((run.returncode, run.stdout, run.stderr.strip()))
    finally:
        server.shutdown()
    print(f"\ncurl {close}: {results}")
    if close == "lingering":
        assert all(r[1] == "422" for r in results)


# ------------------------------------------------- the carried State 7 question
def test_a_failed_body_answered_reaches_a_client_still_waiting():
    """Hand on without values: the client that stalled gets the refusal."""
    server = serve(echo, timeout=0.3)
    try:
        reply = raw(server, b"POST /a HTTP/1.1\r\nHost: a\r\nContent-Length: 100\r\n\r\npart",
                    wait=2)
    finally:
        server.shutdown()
    assert statuses(reply) == [422]
