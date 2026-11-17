"""Run: python -I -m pytest -q experiments/registry/upload_framing_proto
(from the worktree root; -p no:cacheprovider keeps the tree clean)."""
from __future__ import annotations

import io
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from upload_framing import (BodyStream, MultipartFileBody, NO_HEAD, UploadStreamError,  # noqa: E402
                            read_upload_head)
from sessions_proto import Refused, Session, SessionsA, SessionsB  # noqa: E402

CSRF = "q" * 43  # 32 random bytes, base64url


# ---------------------------------------------------------------- helpers
def encode_urllib3(fields):
    from urllib3 import encode_multipart_formdata
    body, content_type = encode_multipart_formdata(fields)
    return body, content_type


def browser_like(csrf: str, content: bytes, boundary="----WebKitFormBoundaryAbC123xyz"):
    """The byte layout Chromium and Firefox send for <form enctype=multipart>."""
    b = boundary.encode()
    body = (b"--" + b + b"\r\n"
            b'Content-Disposition: form-data; name="csrf"\r\n\r\n' + csrf.encode() + b"\r\n"
            b"--" + b + b"\r\n"
            b'Content-Disposition: form-data; name="file"; filename="export.json"\r\n'
            b"Content-Type: application/json\r\n\r\n" + content + b"\r\n"
            b"--" + b + b"--\r\n")
    return body, f"multipart/form-data; boundary={boundary}"


def read_bounded(body, declared, limit):
    """migration_import._read_bounded as A19 rule 4 states it."""
    if declared is not None and declared > limit:
        return "refused_declared"
    data = bytearray()
    while len(data) <= limit:
        chunk = body.read(min(65536, limit + 1 - len(data)))
        if not chunk:
            break
        data += chunk
    if len(data) > limit:
        return "refused_read"
    return bytes(data)


def frame(body: bytes, content_type: str, declared=True):
    stream = io.BufferedReader(io.BytesIO(body))
    head = read_upload_head(stream, content_type, len(body) if declared else None)
    return stream, head


# ---------------------------------------------------------------- encoders
@pytest.mark.parametrize("encoder", ["browser", "urllib3"])
def test_real_encoders_give_csrf_file_and_exact_length(encoder):
    content = b'{"projects": [], "rooms": [], "pointers": []}\r\n--not-a-boundary'
    if encoder == "browser":
        body, ctype = browser_like(CSRF, content)
    else:
        body, ctype = encode_urllib3([("csrf", CSRF),
                                      ("file", ("export.json", content, "application/json"))])
    stream, head = frame(body, ctype)
    assert head.csrf_value == CSRF
    assert head.file_declared_length == len(content)
    file_body = MultipartFileBody(stream, head.delimiter)
    assert read_bounded(file_body, head.file_declared_length, 10**6) == content


def test_head_reads_no_byte_of_the_file():
    content = b"X" * 5000
    body, ctype = browser_like(CSRF, content)
    stream = io.BytesIO(body)
    head = read_upload_head(stream, ctype, len(body))
    assert body[stream.tell():].startswith(b"XXXX")
    assert stream.tell() < 400


# ------------------------------------------------------------ A19 rule 4
LIMIT = 50 * 1024 * 1024


def test_a19_exactly_the_limit_is_read_and_one_more_refused():
    exact = b"a" * LIMIT
    body, ctype = browser_like(CSRF, exact)
    stream, head = frame(body, ctype)
    assert len(body) > LIMIT                      # the whole body is over the limit
    assert head.file_declared_length == LIMIT     # the file part is not
    got = read_bounded(MultipartFileBody(stream, head.delimiter), head.file_declared_length, LIMIT)
    assert got == exact
    body, ctype = browser_like(CSRF, exact + b"a")
    stream, head = frame(body, ctype)
    assert read_bounded(MultipartFileBody(stream, head.delimiter),
                        head.file_declared_length, LIMIT) == "refused_declared"


def test_a19_one_more_without_declared_length_refused_by_counting():
    body, ctype = browser_like(CSRF, b"a" * 1001)
    stream, head = frame(body, ctype, declared=False)
    assert head.file_declared_length is None
    assert read_bounded(MultipartFileBody(stream, head.delimiter), None, 1000) == "refused_read"


def test_lookahead_is_bounded_by_the_delimiter():
    body, ctype = browser_like(CSRF, b"z" * 300_000)
    stream, head = frame(body, ctype)
    fb = MultipartFileBody(stream, head.delimiter)
    while fb.read(4096):
        pass
    assert fb.max_buffered <= 4096 + len(head.delimiter)


# ---------------------------------------------------- malformed framing
def test_missing_closing_delimiter_fails_the_stream():
    body, ctype = browser_like(CSRF, b"data")
    truncated = body[: body.rindex(b"\r\n--")]
    stream, head = frame(truncated, ctype, declared=False)
    with pytest.raises(UploadStreamError):
        read_bounded(MultipartFileBody(stream, head.delimiter), None, 10**6)


def test_third_part_fails_the_stream():
    body, ctype = browser_like(CSRF, b"data")
    b = ctype.split("boundary=")[1].encode()
    body = body.replace(b"--" + b + b"--\r\n",
                        b"--" + b + b'\r\nContent-Disposition: form-data; name="x"\r\n\r\ny\r\n--' + b + b"--\r\n")
    stream, head = frame(body, ctype)
    with pytest.raises(UploadStreamError):
        read_bounded(MultipartFileBody(stream, head.delimiter), None, 10**6)


def test_epilogue_is_ignored_and_only_overstates_the_declared_length():
    body, ctype = browser_like(CSRF, b"data")
    stream, head = frame(body + b"epilogue", ctype)
    assert head.file_declared_length == 4 + len(b"epilogue")
    assert read_bounded(MultipartFileBody(stream, head.delimiter), None, 10**6) == b"data"


@pytest.mark.parametrize("mutate", [
    lambda b, c: (b, "application/json"),                                  # not multipart
    lambda b, c: (b.replace(b'name="csrf"', b'name="other"', 1), c),        # CSRF not first
    lambda b, c: (b.replace(b'name="file"', b'name="upload"', 1), c),      # no file part
    lambda b, c: (b"preamble\r\n" + b, c),                                 # preamble
    lambda b, c: (b[:60], c),                                              # truncated head
])
def test_heads_of_another_form(mutate):
    body, ctype = browser_like(CSRF, b"data")
    body, ctype = mutate(body, ctype)
    assert read_upload_head(io.BytesIO(body), ctype, len(body)) == NO_HEAD


def test_head_over_the_bound_reads_at_most_the_bound():
    body, ctype = browser_like("c" * 20_000, b"data")
    stream = io.BytesIO(body)
    assert read_upload_head(stream, ctype, len(body)) == NO_HEAD
    assert stream.tell() == 8192


def test_declared_length_below_head_is_a_head_of_another_form():
    body, ctype = browser_like(CSRF, b"data")
    assert read_upload_head(io.BytesIO(body), ctype, 50) == NO_HEAD


def test_stream_failing_inside_the_head():
    class Broken(io.BytesIO):
        def read(self, size=-1):
            if self.tell() > 30:
                raise ConnectionResetError
            return super().read(size)
    body, ctype = browser_like(CSRF, b"data")
    assert read_upload_head(Broken(body), ctype, len(body)) == NO_HEAD


# ------------------------------------------------- a real HTTP server + curl
@pytest.mark.skipif(shutil.which("curl") is None, reason="no curl")
def test_curl_upload_through_a_real_http_server(tmp_path):
    content = b'{"projects": [{"project_id": "p1"}]}' * 1000
    export = tmp_path / "export.json"
    export.write_bytes(content)
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            declared = int(self.headers["Content-Length"])
            body = BodyStream(self.rfile, declared)
            head = read_upload_head(body, self.headers["Content-Type"], declared)
            seen["head"] = head
            seen["file"] = read_bounded(MultipartFileBody(body, head.delimiter),
                                        head.file_declared_length, LIMIT)
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        subprocess.run(["curl", "-sS", "-o", "/dev/null",
                        "-F", f"csrf={CSRF}", "-F", f"file=@{export};type=application/json",
                        f"http://127.0.0.1:{server.server_port}/import"],
                       check=True, timeout=30)
    finally:
        server.shutdown()
    assert seen["head"].csrf_value == CSRF
    assert seen["head"].file_declared_length == len(content)
    assert seen["file"] == content


# ------------------------------------------------- T7: arrival vs. admission
def timeline(design):
    """A session one second short of its 30 idle minutes; an upload whose
    headers arrive then; its head takes 2 s to read; the pass runs at 30:00."""
    sessions = design()
    sessions.sessions["s"] = Session(began=0.0, last_request=0.0, csrf=CSRF)
    arrival, pass_at, admission = 1799.0, 1800.0, 1801.0
    if isinstance(sessions, SessionsA):
        sessions.run_pass(pass_at)
        sessions.admit("s", CSRF, admission)
    else:
        ticket = sessions.arrive("s", arrival)
        sessions.run_pass(pass_at)
        sessions.admit(ticket, CSRF)
    return sessions


def test_t7_design_a_refuses_a_request_valid_when_its_headers_came():
    with pytest.raises(Refused):
        timeline(SessionsA)


def test_t7_design_b_admits_it_and_its_arrival_restarts_the_idle_time():
    sessions = timeline(SessionsB)
    # A13 rule 2: the arrival at 29:59 restarted the 30 minutes, so the pass
    # at 30:00 finds the session valid and the upload is admitted.
    assert sessions.sessions["s"].last_request == 1799.0
    assert sessions.sessions["s"].pending == 0


def test_t7_design_b_sign_out_during_the_head_waits_for_the_ticket():
    sessions = SessionsB()
    sessions.sessions["s"] = Session(began=0.0, last_request=0.0, csrf=CSRF)
    ticket = sessions.arrive("s", 10.0)
    sessions.sign_out("s")
    sessions.admit(ticket, CSRF)          # A13 rule 2: admitted before the sign-out
    with pytest.raises(Refused):
        sessions.arrive("s", 11.0)        # a later request is refused
