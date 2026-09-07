"""Steps 6–10: Atlas Advanced, Resource Library, Admin, MCQ quiz, Viva."""
import pytest


# --- Step 6: Atlas Advanced --------------------------------------------------
@pytest.mark.asyncio
async def test_atlas_systems(client):
    resp = await client.get("/api/atlas/systems")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_atlas_relations_requires_structure(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.atlas import AnatomicalRegion, AnatomicalRelationship, AnatomicalStructure

    async with AsyncSession(db_engine) as session:
        r = AnatomicalRegion(slug="rel-test", name="Rel Test")
        session.add(r)
        await session.flush()
        a = AnatomicalStructure(preferred_name="Nerve A", region_id=r.id, status="verified")
        b = AnatomicalStructure(preferred_name="Muscle B", region_id=r.id, status="verified")
        session.add_all([a, b])
        await session.flush()
        aid, bid = a.id, b.id
        session.add(AnatomicalRelationship(structure_a=aid, structure_b=bid, relation_type="supplies"))
        await session.commit()

    resp = await client.get(f"/api/atlas/structures/{aid}/relations")
    assert resp.status_code == 200
    rels = resp.json()
    assert any(rel["related_structure"] == "Muscle B" for rel in rels)


@pytest.mark.asyncio
async def test_atlas_annotations(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.atlas import AnatomicalStructure, AtlasAnnotation, AtlasModel

    async with AsyncSession(db_engine) as session:
        s = AnatomicalStructure(preferred_name="Sternum", status="verified")
        session.add(s)
        await session.flush()
        m = AtlasModel(title="M", file_key="m.glb", is_published=True)
        session.add(m)
        await session.flush()
        mid = m.id
        sid = s.id
        session.add(AtlasAnnotation(model_id=mid, structure_id=sid, label="Manubrium"))
        await session.commit()

    resp = await client.get(f"/api/atlas/structures/{sid}/annotations")
    assert resp.status_code == 200
    assert any(a["label"] == "Manubrium" for a in resp.json())


# --- Step 7: Resource Library -------------------------------------------------
@pytest.mark.asyncio
async def test_books_list_and_detail(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.content import Author, Book, BookChapter, License, Resource

    async with AsyncSession(db_engine) as session:
        lic = License(name="CC BY 4.0")
        session.add(lic)
        await session.flush()
        author = Author(name="OpenStax")
        session.add(author)
        await session.flush()
        res = Resource(title="Test Book", resource_type="book", license_id=lic.id,
                       rights_status="open_license", review_status="published", visibility="public")
        session.add(res)
        await session.flush()
        book = Book(resource_id=res.id, author_id=author.id, title="Test Book", subject_slug="anatomy")
        session.add(book)
        await session.flush()
        bid = book.id
        session.add(BookChapter(book_id=bid, title="Chapter 1", chapter_index=0, topic_slug="x"))
        await session.commit()

    list_resp = await client.get("/api/books?subject=anatomy")
    assert list_resp.status_code == 200
    assert any(b["id"] == bid for b in list_resp.json())

    detail = await client.get(f"/api/books/{bid}")
    assert detail.status_code == 200
    assert detail.json()["license_name"] == "CC BY 4.0"
    assert len(detail.json()["chapters"]) == 1


@pytest.mark.asyncio
async def test_global_search(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.atlas import AnatomicalStructure

    async with AsyncSession(db_engine) as session:
        s = AnatomicalStructure(preferred_name="Median Nerve", status="verified")
        session.add(s)
        await session.commit()

    resp = await client.get("/api/search?q=median")
    assert resp.status_code == 200
    results = resp.json()
    assert any(r["type"] == "structure" and "Median" in r["title"] for r in results)


# --- Step 8: Admin ------------------------------------------------------------
@pytest.mark.asyncio
async def test_admin_stats_admin_only(client, auth_headers):
    # Student gets 403; admin gets 200.
    student = await client.get("/api/admin/stats", headers=auth_headers("student"))
    assert student.status_code == 403

    admin = await client.get("/api/admin/stats", headers=auth_headers("content_admin"))
    assert admin.status_code == 200
    assert "resources" in admin.json()


@pytest.mark.asyncio
async def test_admin_review_workflow_blocks_unknown_rights(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.content import Resource

    async with AsyncSession(db_engine) as session:
        r = Resource(title="Unknown Rights", resource_type="book", rights_status="review_required",
                     review_status="draft", visibility="private")
        session.add(r)
        await session.flush()
        rid = r.id
        await session.commit()

    # Approve should be blocked (rights_status=review_required).
    resp = await client.post(
        f"/api/admin/resources/{rid}/review", json={"decision": "approve"},
        headers=auth_headers("content_admin"),
    )
    assert resp.status_code == 422

    # Reject is allowed.
    reject = await client.post(
        f"/api/admin/resources/{rid}/review", json={"decision": "reject"},
        headers=auth_headers("content_admin"),
    )
    assert reject.status_code == 200
    assert reject.json()["review_status"] == "rejected"


@pytest.mark.asyncio
async def test_admin_atlas_model_ingest_requires_license(client, db_engine, auth_headers):
    # Missing license -> 422 (rights gate on 3D assets).
    resp = await client.post(
        "/api/admin/atlas/models",
        json={"title": "Model", "file_key": "m.glb"},
        headers=auth_headers("content_admin"),
    )
    assert resp.status_code == 422

    with_license = await client.post(
        "/api/admin/atlas/models",
        json={"title": "Model", "file_key": "m.glb", "license": "CC BY-SA 2.1 JP", "region_slug": "upper-limb"},
        headers=auth_headers("content_admin"),
    )
    assert with_license.status_code == 201
    assert with_license.json()["review_status"] == "review_required"


# --- Step 9: MCQ quiz ---------------------------------------------------------
@pytest.mark.asyncio
async def test_quiz_batch_scores(client, db_engine, auth_headers):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.practice import Question, QuestionOption

    async with AsyncSession(db_engine) as session:
        q1 = Question(subject_slug="anatomy", stem="Q1?", is_published=True)
        session.add(q1)
        await session.flush()
        o = QuestionOption(question_id=q1.id, option_text="Correct", is_correct=True)
        wrong = QuestionOption(question_id=q1.id, option_text="Wrong", is_correct=False)
        session.add_all([o, wrong])
        await session.flush()
        qid, oid, wid = q1.id, o.id, wrong.id
        await session.commit()

    # One correct, one wrong.
    resp = await client.post(
        "/api/questions/quiz",
        json={"answers": [
            {"question_id": qid, "selected_option_id": oid},
            {"question_id": qid, "selected_option_id": wid},
        ]},
        headers=auth_headers("student"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["correct"] == 1
    assert data["accuracy"] == 50.0


# --- Step 10: Viva ------------------------------------------------------------
@pytest.mark.asyncio
async def test_viva_count(client, db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.practice import VivaQuestion

    async with AsyncSession(db_engine) as session:
        session.add(VivaQuestion(subject_slug="anatomy", prompt="P?", model_answer="A", is_published=True))
        await session.commit()

    resp = await client.get("/api/viva/count")
    assert resp.status_code == 200
    assert resp.json()["total_viva"] >= 1
