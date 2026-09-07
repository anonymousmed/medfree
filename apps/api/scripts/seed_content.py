"""Seed the Step 19 content pack (curated structures/topics/questions/viva/
flashcards/practicals). Idempotent — matched by stable keys. Call from
``seed_dev.py``.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.atlas import AnatomicalRegion, AnatomicalStructure, AnatomicalSystem
from app.models.practice import (
    Flashcard,
    Practical,
    PracticalStep,
    Question,
    QuestionOption,
    VivaQuestion,
)
from app.models.subject import Subject, Topic, TopicBlock
from scripts.content_pack import (
    BLOCK_REGION_MAP,
    FLASHCARDS,
    PRACTICALS,
    QUESTIONS,
    STRUCTURES,
    TOPICS,
    VIVA,
    blocks_for,
)


async def seed_content_pack(session: AsyncSession) -> None:
    # --- Subjects ------------------------------------------------------------
    subject_ids: dict[str, int] = {}
    for slug in ("anatomy", "physiology", "biochemistry"):
        row = (await session.execute(select(Subject).where(Subject.slug == slug))).scalar_one_or_none()
        if row:
            subject_ids[slug] = row.id

    # --- Regions / systems referenced by structures ---------------------------
    regions = {
        r.slug: r.id
        for r in (await session.execute(select(AnatomicalRegion))).scalars().all()
    }
    systems = {
        s.slug: s.id
        for s in (await session.execute(select(AnatomicalSystem))).scalars().all()
    }

    # --- Structures -----------------------------------------------------------
    for name, latin, region, system, desc, clinical in STRUCTURES:
        existing = (
            await session.execute(
                select(AnatomicalStructure).where(AnatomicalStructure.preferred_name == name)
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(
            AnatomicalStructure(
                preferred_name=name,
                latin_name=latin,
                region_id=regions.get(region),
                system_id=systems.get(system),
                description=desc,
                clinical_notes=clinical,
                status="verified",
            )
        )

    # --- Topics + blocks -------------------------------------------------------
    for subject, slug, title, summary in TOPICS:
        subject_id = subject_ids.get(subject)
        if not subject_id:
            continue
        existing = (
            await session.execute(
                select(Topic).where(Topic.subject_id == subject_id, Topic.slug == slug)
            )
        ).scalar_one_or_none()
        if existing:
            continue
        topic = Topic(
            subject_id=subject_id,
            slug=slug,
            title=title,
            summary=summary,
            is_published=True,
        )
        session.add(topic)
        await session.flush()
        region = BLOCK_REGION_MAP.get(slug)
        for pos, (btype, btitle, content, meta) in enumerate(blocks_for(title, slug, summary, region)):
            session.add(
                TopicBlock(
                    topic_id=topic.id,
                    position=pos,
                    block_type=btype,
                    title=btitle,
                    content=content,
                    meta=meta,
                    is_enabled=True,
                )
            )

    # --- Questions -------------------------------------------------------------
    for subject, topic, difficulty, stem, options, correct_idx, explanation in QUESTIONS:
        existing = (await session.execute(select(Question).where(Question.stem == stem))).scalar_one_or_none()
        if existing:
            continue
        q = Question(
            stem=stem,
            subject_slug=subject,
            topic_slug=topic,
            difficulty=difficulty,
            explanation=explanation,
            qtype="single",
            is_published=True,
        )
        session.add(q)
        await session.flush()
        for idx, opt in enumerate(options):
            session.add(
                QuestionOption(
                    question_id=q.id,
                    option_text=opt,
                    is_correct=(idx == correct_idx),
                )
            )

    # --- Viva -------------------------------------------------------------------
    for subject, topic, prompt, model_answer, key_points in VIVA:
        existing = (await session.execute(select(VivaQuestion).where(VivaQuestion.prompt == prompt))).scalar_one_or_none()
        if existing:
            continue
        session.add(
            VivaQuestion(
                prompt=prompt,
                model_answer=model_answer,
                key_points=key_points,
                subject_slug=subject,
                topic_slug=topic,
                difficulty="medium",
                is_published=True,
            )
        )

    # --- Flashcards ---------------------------------------------------------------
    for subject, topic, front, back in FLASHCARDS:
        existing = (await session.execute(select(Flashcard).where(Flashcard.front == front))).scalar_one_or_none()
        if existing:
            continue
        session.add(
            Flashcard(subject_slug=subject, topic_slug=topic, front=front, back=back, card_type="basic")
        )

    # --- Practicals -----------------------------------------------------------------
    for subject, title, objective, requirements, principle, steps in PRACTICALS:
        existing = (await session.execute(select(Practical).where(Practical.title == title))).scalar_one_or_none()
        if existing:
            continue
        p = Practical(
            subject_slug=subject,
            title=title,
            objective=objective,
            requirements=requirements,
            principle=principle,
            safety_notes="Follow institutional SOP; obtain consent; handle specimens and samples with care.",
            clinical_significance="Bridges the lesson to clinical examination and interpretation.",
            reference_text="Standard practical manual / faculty notes.",
            is_published=True,
        )
        session.add(p)
        await session.flush()
        for i, st in enumerate(steps):
            session.add(PracticalStep(practical_id=p.id, position=i, step_text=st))

    await session.commit()
