"""Witnesses derived from A11, 02_rules.md; see review/SEMANTIC_HANDOFF.md."""
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





def test_deliverer_a11_an_offset_date_is_detected_before_delivery(semantic_runtime):
    # INV-17 and its Required test concern the preflight, not a successful upload.
    r = semantic_runtime
    seed(r)
    for date in ["2026-11-01T12:00:00+01:00", "2026-11-01T12:00:00-01:00", "2026-11-01T11:00:00Z"]:
        r.portal.replace_staff_photo_dates(PROJECT, [date])
        with r.trace_delivery_calls() as calls, r.portal.trace_publish_calls() as publications:
            result = r.calling_flow.deliver(PROJECT)
        assert result["preflight_passed"] is False
        assert calls == [] and publications == []
        assert result["repair_project_id"] == PROJECT
    r.portal.replace_staff_photo_dates(PROJECT, ["2026-11-01T11:00:00"])
    assert r.calling_flow.deliver(PROJECT)["preflight_passed"] is True

