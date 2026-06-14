"""Worked example: CRUD golden path + a 404 edge case."""


async def test_create_then_list_item(client):
    created = await client.post("/api/items", json={"name": "hello", "note": "hi"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "hello"
    assert body["id"] >= 1

    listed = await client.get("/api/items")
    assert listed.status_code == 200
    assert any(i["id"] == body["id"] for i in listed.json())


async def test_get_missing_item_is_404(client):
    r = await client.get("/api/items/999999")
    assert r.status_code == 404
