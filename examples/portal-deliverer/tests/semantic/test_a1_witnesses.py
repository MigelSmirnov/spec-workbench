"""Witnesses derived from A1, 02_rules.md; see review/SEMANTIC_HANDOFF.md."""
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





def test_deliverer_a01_no_operation_changes_the_source_folder(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    seed(r, "sub/notes.txt", b"notes")
    before = r.source.snapshot()
    scan(r)
    place(r, sid)
    place(r, sid)
    mark(r, sid)
    assert r.source.snapshot() == before



def test_deliverer_a01_a_name_a_scan_would_not_report_is_not_delivered(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    seed(r, "sub/a.jpg")
    for name in [".hidden.jpg", ".stversions/a.jpg", "a.jpg.tmp", "sub/.hidden/a.jpg"]:
        seed(r, name)
    r.source.symlink("linked.jpg", "a.jpg")
    r.source.symlink("linked_folder", "sub")
    for name in ["", "/etc/passwd", "../a.jpg", "sub/../a.jpg", "./a.jpg", "sub//a.jpg", "sub/", ".hidden.jpg", ".stversions/a.jpg", "sub/.hidden/a.jpg", "a.jpg.tmp", "linked.jpg", "linked_folder/a.jpg", "sub", "nul\0.jpg"]:
        before = r.durable_snapshot()
        with r.trace_source_opens() as trace:
            answer = place(r, sid, name)
        assert (answer["status"], answer["reason"]) == ("failed", "not_ready_or_absent")
        assert not trace.forbidden_opens(name)
        assert r.durable_snapshot() == before



def test_deliverer_a01_a_syncthing_conflict_copy_is_neither_offered_nor_placed(semantic_runtime):
    r = semantic_runtime
    seed(r)
    for prefix in ["", "sub/"]:
        for flag in ["sync-conflict", "SYNC-CONFLICT", "SyNc-CoNfLiCt"]:
            seed(r, prefix + "a." + flag + "-20261118-120000-ABCDEF1.jpg")
    ordinary = "a.ſync-conflict-20261118-120000-ABCDEF1.jpg"
    seed(r, ordinary)
    assert set(scan(r)) == {"a.jpg", ordinary}

