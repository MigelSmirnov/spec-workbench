"""Witnesses derived from A2, 02_rules.md; see review/SEMANTIC_HANDOFF.md."""
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





def test_deliverer_a02_a_placed_photo_keeps_no_metadata_and_the_source_is_untouched(semantic_runtime):
    r = semantic_runtime
    exif = Image.Exif()
    exif.get_ifd(0x8825)[1] = "N"
    raw = jpeg(exif=exif, comment=b"secret-comment", xmp=b"secret-xmp")
    sid = seed(r, content=raw)
    result = place(r, sid)["placement"]
    stored = r.read_binary(result["file_ref"])
    assert b"Exif" not in stored and b"secret-comment" not in stored and b"secret-xmp" not in stored
    with Image.open(BytesIO(stored)) as image:
        assert not image.getexif() and "comment" not in image.info



def test_deliverer_a02_the_photo_date_is_naive_utc(semantic_runtime):
    r = semantic_runtime
    cases = [("2026:11:04 00:02:25", "+01:00", "2026-11-03T23:02:25"), ("2026:07:04 12:00:00", None, "2026-07-04T10:00:00"), ("2026:07:04 12:00:00", "+25:00", "2026-07-04T10:00:00"), ("1980:01:01 00:00:00", None, "2026-11-18T11:00:00"), (None, None, "2026-11-18T11:00:00")]
    for i, (date, offset, expected) in enumerate(cases):
        exif = Image.Exif()
        detail = exif.get_ifd(0x8769)
        if date is not None:
            detail[0x9003] = date
        if offset is not None:
            detail[0x9011] = offset
        name = f"{i}.jpg"
        sid = seed(r, name, jpeg(exif=exif))
        assert place(r, sid, name)["placement"]["publication"]["photo_date"] == expected



def test_deliverer_a02_publication_body_is_not_client_visible(semantic_runtime):
    r = semantic_runtime
    publication = place(r, seed(r))["placement"]["publication"]
    assert publication["client_visible"] is False

