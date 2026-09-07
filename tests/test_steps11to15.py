"""Steps 11–15: Flashcards, Practicals, AI/RAG, Gamification, Ads/Announcements."""
import pytest


# --- Step 11: Flashcards ------------------------------------------------------
@pytest.mark.asyncio
async def test_flashcards_list_and_stats(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.practice import Flashcard

    async with AsyncSession(db_engine) as session:
        session.add(Flashcard(subject_slug="anatomy", front="Q?", back="A."))
        session.add(Flashcard(subject_slug="anatomy", front="Q2?", back="A2."))
        await session.commit()

    listed = await client.get("/api/flashcards?subject=anatomy", headers=auth_headers("student"))
    assert listed.status_code == 200
    assert len(listed.json()) >= 2

    stats = await client.get("/api/flashcards/stats", headers=auth_headers("student"))
    assert stats.status_code == 200
    assert stats.json()["total_cards"] >= 2
    # Both cards are never-reviewed → due.
    assert stats.json()["due_now"] >= 2


@pytest.mark.asyncio
async def test_flashcard_review_updates_due(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.practice import Flashcard

    async with AsyncSession(db_engine) as session:
        f = Flashcard(subject_slug="anatomy", front="Roots?", back="C5-T1")
        session.add(f)
        await session.flush()
        cid = f.id
        await session.commit()

    headers = auth_headers("student")
    review = await client.post(f"/api/flashcards/{cid}/review", json={"quality": 5}, headers=headers)
    assert review.status_code == 200
    assert review.json()["interval_days"] >= 1
    assert review.json()["due_at"]

    # After review, the card should no longer be "never reviewed"; due_now reflects
    # only past-due reviews (it will be scheduled in the future → not due now).
    stats = await client.get("/api/flashcards/stats", headers=headers)
    # reviewed count >= 1
    assert stats.json()["reviewed"] >= 1


# --- Step 12: Practicals -------------------------------------------------------
@pytest.mark.asyncio
async def test_practicals_detail_with_steps(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.practice import Practical, PracticalStep

    async with AsyncSession(db_engine) as session:
        p = Practical(subject_slug="physiology", title="BP", is_published=True)
        session.add(p)
        await session.flush()
        pid = p.id
        session.add(PracticalStep(practical_id=pid, position=0, step_text="Apply cuff."))
        session.add(PracticalStep(practical_id=pid, position=1, step_text="Inflate."))
        await session.commit()

    detail = await client.get(f"/api/practicals/{pid}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["id"] == pid
    assert len(data["steps"]) == 2
    assert data["steps"][0]["step_text"] == "Apply cuff."


@pytest.mark.asyncio
async def test_practicals_list_filters(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.practice import Practical

    async with AsyncSession(db_engine) as session:
        session.add(Practical(subject_slug="anatomy", title="Bones", is_published=True))
        session.add(Practical(subject_slug="physiology", title="BP", is_published=True))
        session.add(Practical(subject_slug="biochemistry", title="Unpublished", is_published=False))
        await session.commit()

    resp = await client.get("/api/practicals?subject=anatomy")
    assert resp.status_code == 200
    titles = [p["title"] for p in resp.json()]
    assert "Bones" in titles
    assert "Unpublished" not in titles


# --- Step 13: AI / RAG -----------------------------------------------------------
@pytest.mark.asyncio
async def test_ai_ingestion_policy(client):
    resp = await client.get("/api/ai/ingestion-policy")
    assert resp.status_code == 200
    data = resp.json()
    assert data["unknown_is_excluded"] is True
    assert data["review_required_is_excluded"] is True


@pytest.mark.asyncio
async def test_ai_ask_returns_cited_sources(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.atlas import AnatomicalStructure

    async with AsyncSession(db_engine) as session:
        session.add(AnatomicalStructure(preferred_name="Brachial Plexus",
                                        description="Formed by ventral rami of C5–T1.",
                                        status="verified"))
        await session.commit()

    resp = await client.post("/api/ai/ask", json={"question": "What forms the brachial plexus?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["disclaimer"]
    assert isinstance(data["sources"], list)


# --- Step 14: Gamification -------------------------------------------------------
@pytest.mark.asyncio
async def test_gamification_summary(client, db_engine, auth_headers):
    headers = auth_headers("student")
    # First call computes baseline (no activity → streak 0 or 1, xp 0).
    resp = await client.get("/api/gamification/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "streak" in data
    assert "xp" in data
    assert "badges" in data


@pytest.mark.asyncio
async def test_gamification_awards_xp_and_badges(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.progress import UserProgress

    async with AsyncSession(db_engine) as session:
        from app.models.user import User, UserRole

        # Ensure user exists with a stable id; auth provisions on first authed call.
        pass

    headers = auth_headers("student")
    # Complete a topic to earn XP + first_topic badge.
    completed = await client.post(
        "/api/progress/topics",
        json={"subject_slug": "anatomy", "topic_slug": "x", "state": "completed", "mastery": 100},
        headers=headers,
    )
    assert completed.status_code == 200

    summary = await client.get("/api/gamification/summary", headers=headers)
    data = summary.json()
    assert data["xp"] >= 20
    assert data["topics_completed"] >= 1
    assert any(b["key"] == "first_topic" for b in data["badges"])


# --- Step 15: Ads / Announcements ---------------------------------------------
@pytest.mark.asyncio
async def test_public_banner_and_announcement(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.content_platform import Ad, Announcement

    async with AsyncSession(db_engine) as session:
        session.add(Ad(placement="homepage", title="Start with Atlas", target_url="/atlas", is_active=True))
        session.add(Announcement(kind="system", title="Welcome", body="Hi", is_active=True))
        await session.commit()

    banner = await client.get("/api/ads?placement=homepage")
    assert banner.status_code == 200
    assert banner.json()["title"] == "Start with Atlas"

    ann = await client.get("/api/announcements")
    assert ann.status_code == 200
    assert any(a["title"] == "Welcome" for a in ann.json())


@pytest.mark.asyncio
async def test_ad_write_requires_admin(client, auth_headers):
    # Student cannot create an ad (admin-only).
    resp = await client.post(
        "/api/admin/ads",
        json={"placement": "homepage", "title": "Should not happen"},
        headers=auth_headers("student"),
    )
    assert resp.status_code == 403

    admin = await client.post(
        "/api/admin/ads",
        json={"placement": "homepage", "title": "Ok", "target_url": "/atlas", "is_active": True},
        headers=auth_headers("content_admin"),
    )
    assert admin.status_code == 201
