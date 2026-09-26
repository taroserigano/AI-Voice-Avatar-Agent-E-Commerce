from __future__ import annotations

from fastapi.testclient import TestClient


def test_signed_in_shoppers_see_ten_dallas_area_stores(alice: TestClient) -> None:
    resp = alice.get("/v1/stores")
    assert resp.status_code == 200
    stores = resp.json()
    assert len(stores) == 10
    for s in stores:
        assert s["state"] == "TX" and s["timezone"] == "America/Chicago"
        # Dallas-Fort Worth, roughly: nobody's pin lands in the Gulf.
        assert 32.5 < s["latitude"] < 33.4 and -97.4 < s["longitude"] < -96.4
        assert len(s["hours"]) == 7
        assert "555-01" in s["phone"]
        assert isinstance(s["open_now"], bool)


def test_stores_need_sign_in(client: TestClient) -> None:
    assert client.get("/v1/stores").status_code == 401
