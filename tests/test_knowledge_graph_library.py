"""Regression tests for the curriculum knowledge graph and the rights-aware library.

Verifies:
- topics expose prerequisites / related / next in the topic-detail endpoint
- the curated library seeds rights-aware resources (no fabricated URLs, correct
  AI-ingestion status for OpenStax, external-only rows never rehosted)
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.content import Resource
from app.models.subject import LINK_NEXT, LINK_PREREQUISITE, LINK_RELATED, Subject, Topic, TopicLink
from scripts.library_pack import seed_library_pack


@pytest.mark.asyncio
async def test_topic_detail_exposes_knowledge_graph(db_engine, client):
    sf = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with sf() as s:
        subj = Subject(slug="anatomy", title="Anatomy", sort_order=1, is_active=True)
        s.add(subj)
        await s.flush()
        a = Topic(subject_id=subj.id, slug="axilla", title="Axilla", difficulty="intermediate", is_published=True)
        b = Topic(subject_id=subj.id, slug="brachial-plexus", title="Brachial Plexus", difficulty="advanced", is_published=True)
        c = Topic(subject_id=subj.id, slug="median-nerve", title="Median Nerve", difficulty="advanced", is_published=True)
        s.add_all([a, b, c])
        await s.flush()
        s.add_all([
            TopicLink(from_topic_id=a.id, to_topic_id=b.id, link_type=LINK_PREREQUISITE),
            TopicLink(from_topic_id=b.id, to_topic_id=c.id, link_type=LINK_NEXT),
            TopicLink(from_topic_id=b.id, to_topic_id=a.id, link_type=LINK_RELATED),
        ])
        await s.commit()

    resp = await client.get(f"/api/subjects/anatomy/topics/brachial-plexus")
    assert resp.status_code == 200
    data = resp.json()
    assert data["difficulty"] == "advanced"
    prereqs = [p["slug"] for p in data["prerequisites"]]
    nxt = [p["slug"] for p in data["next_topics"]]
    related = [p["slug"] for p in data["related"]]
    assert "axilla" in prereqs
    assert "median-nerve" in nxt
    assert "axilla" in related


@pytest.mark.asyncio
async def test_library_pack_seeds_rights_aware_resources(db_engine):
    sf = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with sf() as s:
        counts = await seed_library_pack(s)
        resources = (await s.execute(select(Resource))).scalars().all()
        assert len(resources) >= 10

        # 1) No fabricated URLs.
        assert all(r.source_url and "example.com" not in r.source_url for r in resources)

        # 2) OpenStax A&P -> CC BY-NC-SA 4.0 with AI ingestion OFF.
        oap = next(r for r in resources if r.title.startswith("Anatomy & Physiology 2e"))
        assert oap.ai_usage_status == "false"
        assert oap.medical_review_status != "approved"  # honest: not medically reviewed

        # 3) External-only (NCBI / publisher-retained) must never be rehosted
        #    nor ingested (only explicit 'true' may be; 'unknown' = do not ingest).
        for r in resources:
            if r.rights_status == "external_only":
                assert r.local_storage_key is None
                assert r.source_url  # has a source to link to
                assert r.ai_usage_status != "true"

        # 4) Every resource carries a rights status + review status.
        assert all(r.rights_status and r.review_status for r in resources)
        assert counts["resources"] >= 10
