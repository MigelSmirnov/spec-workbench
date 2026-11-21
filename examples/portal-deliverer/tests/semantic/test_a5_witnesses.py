"""Witnesses derived from A5, 02_rules.md; see review/SEMANTIC_HANDOFF.md."""
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





def test_deliverer_a05_every_route_except_health_requires_the_token(semantic_runtime):
    r = semantic_runtime
    routes = [("GET", f"/v1/projects/{PROJECT}/photos"), ("POST", f"/v1/projects/{PROJECT}/photos/deliver"), ("POST", f"/v1/projects/{PROJECT}/photos/{'0'*64}/published")]
    for method, path in routes:
        for token in [None, "wrong"]:
            assert r.request(method, path, body={}, token=token).status_code == 401
    assert r.request("GET", "/v1/projects/not-a-uuid/photos", token=None).status_code == 401
    assert r.request("GET", "/health", token=None).status_code == 200



def test_deliverer_a05_an_unconfirmed_connection_delivers_nothing(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    r.connection.set_confirmed(False)
    before = r.durable_snapshot()
    for action in [lambda: scan(r), lambda: place(r, sid), lambda: mark(r, sid)]:
        refused(action, "connection_not_confirmed")
    assert r.durable_snapshot() == before



def test_deliverer_a05_the_api_scans_and_places_without_showing_server_paths(semantic_runtime):
    r = semantic_runtime
    sid = seed(r)
    paths = [("GET", f"/v1/projects/{PROJECT}/photos", None), ("POST", f"/v1/projects/{PROJECT}/photos/deliver", {"name":"a.jpg", "source_id":sid}), ("POST", f"/v1/projects/{PROJECT}/photos/{sid}/published", {"photo_id":PHOTO}), ("POST", f"/v1/projects/{PROJECT}/photos/{'1'*64}/published", {"photo_id":PHOTO})]
    with r.trap_outbound_connections() as attempts:
        for method, path, body in paths:
            response = r.request(method, path, body=body)
            for private in r.private_paths:
                assert private not in response.text
    assert attempts == []

