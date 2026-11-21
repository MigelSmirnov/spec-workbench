"""Witnesses derived from A4, 02_rules.md; see review/SEMANTIC_HANDOFF.md."""
import hashlib
from datetime import datetime, timezone
from io import BytesIO

import pytest
from PIL import Image

PROJECT = "b13c5547-fe49-439d-a7d8-0a02b2c19a7b"
PHOTO = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
OTHER = "52b132d7-0a94-44e7-9aab-63a77ca770f2"
MODIFIED = datetime(2026, 11, 18, 11, tzinfo=timezone.utc).timestamp()


def jpeg(color=(200, 30, 30), exif=None, **metadata):
    out = BytesIO()
    Image.new("RGB", (3000, 1500), color).save(out, "JPEG", exif=Image.Exif() if exif is None else exif, **metadata)
    return out.getvalue()


def seed(r, name="a.jpg", content=None):
    content = jpeg() if content is None else content
    r.source.put(name, content, mtime=MODIFIED)
    return hashlib.sha256(content).hexdigest()


def place(r, sid, name="a.jpg"):
    return r.deliver_project_photo(PROJECT, name, sid)


def mark(r, sid, photo=PHOTO):
    return r.mark_photo_published(PROJECT, sid, photo)


def scan(r):
    return {x["name"]: x for x in r.scan_project_photos(PROJECT)["items"]}


def refused(action, code):
    with pytest.raises(Exception) as error:
        action()
    assert error.value.code == code





def test_deliverer_a04_marking_again_changes_nothing_and_another_photo_is_refused(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    place(r, sid)
    first = mark(r, sid)
    before = r.durable_snapshot()
    r.clock.set("2026-11-20T13:00:00")
    again = mark(r, sid)
    assert again["status"] == "replayed" and again["marked_at"] == first["marked_at"]
    refused(lambda: mark(r, sid, OTHER), "publication_conflict")
    assert r.durable_snapshot() == before
    r.connection.add_confirmed(OTHER)
    refused(lambda: r.mark_photo_published(OTHER, sid, PHOTO), "not_placed")

