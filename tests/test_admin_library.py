"""Admin content-authoring: create MCQs, viva, flashcards, practicals (admin-only)."""

import pytest


@pytest.mark.asyncio
async def test_non_admin_cannot_create_question(client, auth_headers):
    resp = await client.post(
        "/api/admin/content/questions",
        json={"subject_slug": "anatomy", "stem": "q?", "options": [{"option_text": "a", "is_correct": True}]},
        headers=auth_headers("student"),
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_admin_creates_mcq(client, auth_headers):
    resp = await client.post(
        "/api/admin/content/questions",
        json={
            "subject_slug": "anatomy",
            "topic_slug": "upper-limb",
            "stem": "Which nerve innervates the thenar muscles?",
            "difficulty": "medium",
            "options": [
                {"option_text": "Median nerve", "is_correct": True, "sort_order": 0},
                {"option_text": "Radial nerve", "is_correct": False, "sort_order": 1},
                {"option_text": "Ulnar nerve", "is_correct": False, "sort_order": 2},
            ],
        },
        headers=auth_headers("super_admin"),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["subject_slug"] == "anatomy"
    assert len(data["options"]) == 3
    correct = [o for o in data["options"] if o["is_correct"]]
    assert len(correct) == 1


@pytest.mark.asyncio
async def test_admin_mcq_requires_a_correct_option(client, auth_headers):
    resp = await client.post(
        "/api/admin/content/questions",
        json={
            "subject_slug": "anatomy",
            "stem": "No correct option?",
            "options": [
                {"option_text": "a", "is_correct": False},
                {"option_text": "b", "is_correct": False},
            ],
        },
        headers=auth_headers("super_admin"),
    )
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_admin_creates_viva_flashcard_practical(client, auth_headers):
    v = await client.post(
        "/api/admin/content/viva",
        json={"subject_slug": "physiology", "prompt": "Explain Starling's law.", "model_answer": "answer", "difficulty": "medium"},
        headers=auth_headers("super_admin"),
    )
    assert v.status_code == 201, v.text
    assert v.json()["subject_slug"] == "physiology"

    f = await client.post(
        "/api/admin/content/flashcards",
        json={"subject_slug": "biochemistry", "front": "What is Km?", "back": "Michaelis constant."},
        headers=auth_headers("super_admin"),
    )
    assert f.status_code == 201, f.text
    assert f.json()["card_type"] == "basic"

    p = await client.post(
        "/api/admin/content/practicals",
        json={
            "subject_slug": "anatomy",
            "title": "Brachial plexus examination",
            "steps": [{"step_text": "Inspect the shoulder"}, {"step_text": "Test thenar muscles"}],
        },
        headers=auth_headers("super_admin"),
    )
    assert p.status_code == 201, p.text
    assert len(p.json()["steps"]) == 2
