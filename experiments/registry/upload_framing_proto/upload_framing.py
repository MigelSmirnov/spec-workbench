"""Prototype of the `upload_framing` module (State 3, owner 2026-11-17).

An upload form sends its CSRF field as the first multipart part and the file
as the second. `read_upload_head` reads the head alone — the CSRF part and the
file part's headers, at most `head_max` bytes — and never a byte of the file.
`MultipartFileBody` gives the file part's bytes and ends before the closing
delimiter, looking ahead no further than the delimiter needs.

Not generated code: a throwaway experiment to test the design against real
multipart encoders (curl, urllib3/requests) and a real HTTP server.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

UPLOAD_FORM_HEAD_MAX_BYTES = 8192
CSRF_FIELD = "csrf"
FILE_FIELD = "file"


class ByteStream(Protocol):
    """The request's body, ending where the body ends (its declared length):
    a reader that looks ahead must never block on bytes the client will not
    send before it gets an answer."""

    def read(self, size: int) -> bytes: ...


class BodyStream:
    """What the listener (instance_lifecycle) must hand on as ByteStream:
    the socket's reader cut at the request's Content-Length."""

    def __init__(self, raw, length: int) -> None:
        self._raw, self._left = raw, length

    def read(self, size: int) -> bytes:
        if self._left <= 0 or size <= 0:
            return b""
        chunk = self._raw.read(min(size, self._left))
        self._left -= len(chunk)
        return chunk


@dataclass(frozen=True)
class UploadHead:
    csrf_value: str | None
    delimiter: str | None
    file_declared_length: int | None


NO_HEAD = UploadHead(None, None, None)


class UploadStreamError(Exception):
    """The file part's stream failed: it ended before the closing delimiter,
    or another part follows the file. read_import_mapping answers it
    `file_unreadable`, as any stream that fails."""


_BOUNDARY = re.compile(r'boundary=(?:"([^"]{1,70})"|([^\s;"]{1,70}))', re.I)
_DISPOSITION = re.compile(
    rb'^content-disposition:\s*form-data;\s*name="([^"]*)"', re.I | re.M)


def _boundary_of(content_type: str | None) -> str | None:
    if not content_type:
        return None
    if content_type.split(";", 1)[0].strip().lower() != "multipart/form-data":
        return None
    match = _BOUNDARY.search(content_type)
    if not match:
        return None
    return match.group(1) or match.group(2)


class _Head:
    """Reads the stream one byte at a time, never past what it is asked for,
    and never more than `limit` bytes in all."""

    def __init__(self, stream: ByteStream, limit: int) -> None:
        self.stream, self.limit, self.used = stream, limit, 0

    def until(self, marker: bytes) -> bytes | None:
        """The bytes up to and including `marker`, or None when the stream
        ends or the limit is reached first."""
        buffer = bytearray()
        while not buffer.endswith(marker):
            if self.used >= self.limit:
                return None
            byte = self.stream.read(1)
            if not byte:
                return None
            self.used += 1
            buffer += byte
        return bytes(buffer)


def read_upload_head(stream: ByteStream, content_type: str | None,
                     declared_length: int | None,
                     head_max: int = UPLOAD_FORM_HEAD_MAX_BYTES) -> UploadHead:
    boundary = _boundary_of(content_type)
    if boundary is None:
        return NO_HEAD
    dash = b"--" + boundary.encode("ascii")
    head = _Head(stream, head_max)
    try:
        # 1. the opening delimiter line (no preamble is accepted)
        if head.until(b"\r\n") != dash + b"\r\n":
            return NO_HEAD
        # 2. the first part: the CSRF field
        headers = head.until(b"\r\n\r\n")
        if headers is None or _field_name(headers) != CSRF_FIELD:
            return NO_HEAD
        value = head.until(b"\r\n" + dash + b"\r\n")
        if value is None:
            return NO_HEAD
        csrf = value[: -len(b"\r\n" + dash + b"\r\n")]
        # 3. the second part's headers: the file
        headers = head.until(b"\r\n\r\n")
        if headers is None or _field_name(headers) != FILE_FIELD:
            return NO_HEAD
    except OSError:
        # T25: the request's stream failing while the head is read is a head
        # of another form: no CSRF value, refused at stage (1).
        return NO_HEAD
    try:
        csrf_text = csrf.decode("ascii")
    except UnicodeDecodeError:
        return NO_HEAD
    delimiter = "\r\n" + dash.decode("ascii")
    file_length = None
    if declared_length is not None:
        closing = len(delimiter) + len("--\r\n")
        file_length = declared_length - head.used - closing
        if file_length < 0:
            return NO_HEAD
    return UploadHead(csrf_text, delimiter, file_length)


def _field_name(headers: bytes) -> str | None:
    match = _DISPOSITION.search(headers)
    return match.group(1).decode("latin-1") if match else None


class MultipartFileBody:
    """UploadBody over the request's stream: the file part's bytes, ending
    before `delimiter`. Holds at most len(delimiter) bytes of look-ahead
    beyond what it was asked for."""

    def __init__(self, stream: ByteStream, delimiter: str) -> None:
        self._stream = stream
        self._delimiter = delimiter.encode("ascii")
        self._buffer = bytearray()
        self._ended = False
        self.max_buffered = 0

    def read(self, size: int) -> bytes:
        if self._ended or size <= 0:
            return b""
        need = size + len(self._delimiter)
        while len(self._buffer) < need and self._buffer.find(self._delimiter) == -1:
            chunk = self._stream.read(need - len(self._buffer))
            if not chunk:
                break
            self._buffer += chunk
        self.max_buffered = max(self.max_buffered, len(self._buffer))
        at = self._buffer.find(self._delimiter)
        if at == -1:
            if len(self._buffer) < need:  # the stream ended first
                raise UploadStreamError("stream ended before the closing delimiter")
            out = bytes(self._buffer[:size])
            del self._buffer[:size]
            return out
        if at >= size:
            out = bytes(self._buffer[:size])
            del self._buffer[:size]
            return out
        out = bytes(self._buffer[:at])
        rest = self._buffer[at + len(self._delimiter):]
        self._ended = True
        self._finish(rest)
        return out

    def _finish(self, rest: bytearray) -> None:
        """After the delimiter: `--` closes the body; CRLF opens a third part,
        which the form never sends."""
        while len(rest) < 2:
            chunk = self._stream.read(2 - len(rest))
            if not chunk:
                break
            rest += chunk
        if rest[:2] != b"--":
            raise UploadStreamError("another part follows the file")
        self._buffer = bytearray()
