"""Learning Core: structured topic blocks + bookmarks + notes (server-side)."""
import pytest


@pytest.mark.asyncio
async def test_topic_includes_structured_blocks(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.subject import Subject, Topic, TopicBlock

    async with AsyncSession(db_engine) as session:
        s = Subject(slug="anatomy", title="Anatomy", is_active=True)
        session.add(s)
        await session.flush()
        t = Topic(subject_id=s.id, slug="brachial-plexus", title="Brachial Plexus", is_published=True)
        session.add(t)
        await session.flush()
        for pos, (bt, ti) in enumerate([("overview", "Overview"), ("atlas", "Atlas"), ("mcq", "MCQs")]):
            session.add(TopicBlock(topic_id=t.id, position=pos, block_type=bt, title=ti))
        await session.commit()

    resp = await client.get("/api/subjects/anatomy/topics/brachial-plexus")
    assert resp.status_code == 200
    data = resp.json()
    blocks = data["blocks"]
    assert len(blocks) == 3
    assert [b["block_type"] for b in blocks] == ["overview", "atlas", "mcq"]


@pytest.mark.asyncio
async def test_bookmark_create_list_delete(client, auth_headers):
    headers = auth_headers("student")

    created = await client.post(
        "/api/me/bookmarks",
        json={"target_type": "topic", "target_slug": "brachial-plexus", "title": "Brachial Plexus"},
        headers=headers,
    )
    assert created.status_code == 201
    bid = created.json()["id"]

    listed = await client.get("/api/me/bookmarks", headers=headers)
    assert listed.status_code == 200
    assert any(b["id"] == bid for b in listed.json())

    deleted = await client.delete(f"/api/me/bookmarks/{bid}", headers=headers)
    assert deleted.status_code == 204

    listed2 = await client.get("/api/me/bookmarks", headers=headers)
    assert all(b["id"] != bid for b in listed2.json())


@pytest.mark.asyncio
async def test_note_create_update_delete(client, auth_headers):
    headers = auth_headers("student")

    created = await client.post(
        "/api/me/notes",
        json={"target_type": "topic", "target_slug": "femoral-triangle", "body": "Remember NAV."},
        headers=headers,
    )
    assert created.status_code == 201
    nid = created.json()["id"]

    updated = await client.patch(
        f"/api/me/notes/{nid}", json={"body": "NAV = Nerve, Artery, Vein", "is_pinned": True}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["body"] == "NAV = Nerve, Artery, Vein"
    assert updated.json()["is_pinned"] is True

    deleted = await client.delete(f"/api/me/notes/{nid}", headers=headers)
    assert deleted.status_code == 204
