"""Seed a local/dev database with representative MEDFREE content.

Run from apps/api:
    ./.venv/bin/python -m scripts.seed_dev

Creates tables (idempotent create_all) and inserts a starter dataset:
- Atlas regions / systems / structures
- Subjects / topics
- A license + an admin-ish resource
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import (
    Ad,
    AnatomicalRegion,
    AnatomicalRelationship,
    AnatomicalStructure,
    AnatomicalSystem,
    Announcement,
    AtlasAnnotation,
    AtlasModel,
    AtlasModelPart,
    Author,
    Book,
    BookChapter,
    Flashcard,
    License,
    Practical,
    PracticalStep,
    Question,
    QuestionOption,
    Resource,
    Subject,
    Topic,
    TopicBlock,
    VivaQuestion,
)

# Import all models so they register on Base.metadata.
import app.models  # noqa: F401

from scripts.seed_content import seed_content_pack
from scripts.library_pack import seed_library_pack

DATABASE_URL = "sqlite+aiosqlite:///./medfree.db"

REGIONS = [
    ("upper-limb", "Upper Limb"),
    ("thorax", "Thorax"),
    ("abdomen", "Abdomen"),
    ("pelvis", "Pelvis & Perineum"),
    ("head-neck", "Head & Neck"),
    ("back", "Back"),
    ("neuroanatomy", "Neuroanatomy"),
]

SYSTEMS = [
    ("skeletal", "Skeletal"),
    ("muscular", "Muscular"),
    ("nervous", "Nervous"),
    ("cardiovascular", "Cardiovascular"),
    ("respiratory", "Respiratory"),
    ("digestive", "Digestive"),
    ("urinary", "Urinary"),
]

STRUCTURES = [
    # (preferred_name, latin_name, region, system, description, clinical)
    ("Brachial Plexus", "Plexus brachialis", "upper-limb", "nervous",
     "Network of nerves supplying the upper limb, formed by ventral rami of C5–T1.",
     "Erb's palsy: C5–C6 injury; Klumpke's: C8–T1 injury."),
    ("Median Nerve", "Nervus medianus", "upper-limb", "nervous",
     "Mixed nerve of the upper limb supplying most forearm flexors and thenar muscles.",
     "Carpal tunnel syndrome; 'hand of benediction' in high lesions."),
    ("Brachial Artery", "Arteria brachialis", "upper-limb", "cardiovascular",
     "Main artery of the arm; continuation of axillary artery at teres major.",
     "Pulse felt in cubital fossa; used for BP measurement."),
    ("Femoral Triangle", "Trigonum femorale", "pelvis", "muscular",
     "Subinguinal space bounded by inguinal ligament, sartorius and adductor longus.",
     "Common site for femoral pulse and nerve blocks."),
    ("Sternum", "Sternum", "thorax", "skeletal",
     "Flat bone in anterior midline of the thorax; manubrium, body and xiphoid.",
     "Site for bone marrow aspiration and cardiac compressions."),
]

SUBJECTS = [
    ("anatomy", "Anatomy", "Gross & regional anatomy with the Human Atlas.", "#f0abfc"),
    ("physiology", "Physiology", "How the body works — simulations & practicals.", "#38bdf8"),
    ("biochemistry", "Biochemistry", "Pathways, reactions and clinical correlations.", "#4ade80"),
]

TOPICS = [
    ("anatomy", "brachial-plexus", "Brachial Plexus",
     "Roots, trunks, divisions, cords and branches forming the nerve supply of the upper limb."),
    ("anatomy", "femoral-triangle", "Femoral Triangle",
     "Boundaries and contents — the femoral nerve, artery and vein."),
    ("anatomy", "median-nerve", "Median Nerve",
     "Course, branches and clinical lesions."),
]

# Structured learning blocks for the canonical topic learning flow.
BLOCKS = [
    ("overview", "Quick Overview",
     "A network of nerves supplying the upper limb, formed by the ventral rami of C5–T1. It passes from the neck, through the axilla, to the upper limb.", None),
    ("objectives", "Learning Objectives",
     "- Name the roots, trunks, divisions, cords and branches.\n- Describe the course from spinal cord to upper limb.\n- Relate clinical lesions (Erb's, Klumpke's) to specific parts.", None),
    ("atlas", "Human Atlas / 3D", "Explore this structure in the interactive 3D Human Atlas.",
     '{"type":"atlas","region":"upper-limb","structure":"brachial-plexus"}'),
    ("diagram", "Interactive Diagram",
     "Roots → Trunks → Divisions → Cords → Branches. Toggle each level to build the plexus step by step.", None),
    ("clinical", "Clinical Correlation",
     "Erb's palsy (C5–C6) → waiter's tip position. Klumpke's palsy (C8–T1) → claw hand. Trauma, birth injury, and anaesthetic positioning are key causes.", None),
    ("mcq", "MCQs", "Attempt questions on the brachial plexus.", '{"type":"mcq","topic":"brachial-plexus"}'),
    ("viva", "Viva", "Practice oral exam questions with model answers.", '{"type":"viva","topic":"brachial-plexus"}'),
    ("flashcards", "Flashcards", "Spaced-repetition cards for active recall.", '{"type":"flashcard","topic":"brachial-plexus"}'),
    ("practical", "Practical / Spotter", "Identify the plexus and its branches on a specimen or in surface anatomy.", '{"type":"practical","topic":"brachial-plexus"}'),
    ("books", "Books & Research",
     "OpenStax Anatomy & Physiology, Gray's Anatomy for Students, NCBI Bookshelf.", None),
    ("revision", "Revision", "Quick recap: C5–T1 → trunks → divisions → cords → branches.", None),
]


async def run() -> None:
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        # Regions
        region_ids: dict[str, int] = {}
        for slug, name in REGIONS:
            existing = (
                await session.execute(
                    select(AnatomicalRegion).where(AnatomicalRegion.slug == slug)
                )
            ).scalar_one_or_none()
            if existing:
                region_ids[slug] = existing.id
            else:
                obj = AnatomicalRegion(slug=slug, name=name)
                session.add(obj)
                await session.flush()
                region_ids[slug] = obj.id

        # Systems
        system_ids: dict[str, int] = {}
        for slug, name in SYSTEMS:
            existing = (
                await session.execute(
                    select(AnatomicalSystem).where(AnatomicalSystem.slug == slug)
                )
            ).scalar_one_or_none()
            if existing:
                system_ids[slug] = existing.id
            else:
                obj = AnatomicalSystem(slug=slug, name=name)
                session.add(obj)
                await session.flush()
                system_ids[slug] = obj.id

        # Structures
        for name, latin, region, system, desc, clinical in STRUCTURES:
            existing = (
                await session.execute(
                    select(AnatomicalStructure).where(
                        AnatomicalStructure.preferred_name == name
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    AnatomicalStructure(
                        preferred_name=name,
                        latin_name=latin,
                        region_id=region_ids.get(region),
                        system_id=system_ids.get(system),
                        description=desc,
                        clinical_notes=clinical,
                        status="verified",
                    )
                )

        # Subjects + topics
        subject_ids: dict[str, int] = {}
        for slug, title, desc, color in SUBJECTS:
            existing = (
                await session.execute(select(Subject).where(Subject.slug == slug))
            ).scalar_one_or_none()
            if existing:
                subject_ids[slug] = existing.id
            else:
                obj = Subject(slug=slug, title=title, description=desc, color=color, is_active=True)
                session.add(obj)
                await session.flush()
                subject_ids[slug] = obj.id

        for subj, slug, title, summary in TOPICS:
            existing = (
                await session.execute(
                    select(Topic).where(Topic.subject_id == subject_ids[subj], Topic.slug == slug)
                )
            ).scalar_one_or_none()
            if existing is None:
                topic = Topic(
                    subject_id=subject_ids[subj],
                    slug=slug,
                    title=title,
                    summary=summary,
                    is_published=True,
                )
                session.add(topic)
                await session.flush()
                for pos, (btype, btitle, content, meta) in enumerate(BLOCKS):
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

        await seed_practice(session)
        await seed_relations(session)
        await seed_atlas_model(session)
        await seed_platform(session)
        await seed_content_pack(session)
        await seed_library_pack(session)
        await seed_knowledge_graph(session)

        await session.commit()
        print("Seed complete.")

    await engine.dispose()


QUESTION_OPTIONS = {
    "brachial": [
        ("Formed by ventral rami of C5–C6", False),
        ("Formed by ventral rami of C5–T1", True),
        ("Formed by ventral rami of T1–T2 only", False),
        ("Formed by dorsal rami of C5–T1", False),
    ],
    "benediction": [
        ("Ulnar nerve lesion", False),
        ("Median nerve lesion", True),
        ("Radial nerve lesion", False),
        ("Axillary nerve lesion", False),
    ],
    "femoral": [
        ("Femoral nerve, artery, vein", True),
        ("Obturator nerve, artery, vein", False),
        ("Sciatic nerve and vessels", False),
        ("Superficial inguinal nodes only", False),
    ],
}


async def seed_practice(session) -> None:
    # MCQs
    async def add_question(subject, topic, slug, stem, difficulty, explanation):
        existing = (
            await session.execute(
                select(Question).where(Question.topic_slug == topic, Question.stem == stem)
            )
        ).scalar_one_or_none()
        if existing:
            return
        q = Question(
            subject_slug=subject,
            topic_slug=topic,
            stem=stem,
            qtype="single_best_answer",
            difficulty=difficulty,
            explanation=explanation,
            is_published=True,
        )
        session.add(q)
        await session.flush()
        for i, (text, correct) in enumerate(QUESTION_OPTIONS[slug]):
            session.add(
                QuestionOption(
                    question_id=q.id, option_text=text, is_correct=correct, sort_order=i
                )
            )

    await add_question("anatomy", "brachial-plexus", "brachial",
                 "The brachial plexus is formed by the ventral rami of which nerve roots?",
                 "easy", "Ventral rami of C5–T1 form the brachial plexus.")
    await add_question("anatomy", "brachial-plexus", "benediction",
                 "A 'hand of benediction' posture is classically associated with which nerve lesion?",
                 "medium", "High median nerve lesion produces the 'hand of benediction'.")
    await add_question("anatomy", "femoral-triangle", "femoral",
                 "Which of the following are the contents of the femoral triangle?",
                 "easy", "Femoral nerve, artery and vein from lateral to medial.")

    # Viva
    viva_bank = [
        ("brachial-plexus", "Enumerate the roots, trunks, divisions, cords and branches of the brachial plexus.",
         "Roots C5–T1 → trunks (superior, middle, inferior) → divisions (anterior/posterior) → cords (lateral, posterior, medial) → branches (musculocutaneous, median, ulnar, radial, axillary).",
         "Remember: 'Really There's Some Dislocated Looking Belly - Missing The Dark Muscular, Median and Ulnar' (Roots, Trunks, Divisions, Cords, Branches)."),
        ("femoral-triangle", "What are the boundaries of the femoral triangle?",
         "Superior: inguinal ligament; Medial: medial border of adductor longus; Lateral: medial border of sartorius; Apex: where sartorius overlaps adductor longus.",
         "NAV = Nerve, Artery, Vein (lateral to medial)."),
        ("median-nerve", "Give the nerve supply of the thenar muscles.",
         "Recurrent branch of the median nerve supplies opponents pollicis, abductor pollicis brevis and the superficial head of flexor pollicis brevis.",
         "LOAF muscles partly; thenar = median (OA, AB, FPB-superficial)."),
    ]
    for topic, prompt, model, key in viva_bank:
        existing = (
            await session.execute(select(VivaQuestion).where(VivaQuestion.prompt == prompt))
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                VivaQuestion(
                    subject_slug="anatomy",
                    topic_slug=topic,
                    prompt=prompt,
                    model_answer=model,
                    key_points=key,
                    difficulty="medium",
                    is_published=True,
                )
            )

    # Flashcards
    cards = [
        ("brachial-plexus", "Which nerve roots form the brachial plexus?", "C5–T1 (ventral rami)."),
        ("brachial-plexus", "What is Klumpke's palsy?", "Injury to C8–T1 roots → intrinsic hand muscle weakness & claw hand."),
        ("femoral-triangle", "NAV in the femoral triangle stands for?", "Nerve, Artery, Vein — lateral to medial."),
        ("median-nerve", "Carpal tunnel syndrome compresses which nerve?", "The median nerve under the flexor retinaculum."),
    ]
    for topic, front, back in cards:
        existing = (
            await session.execute(select(Flashcard).where(Flashcard.front == front))
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                Flashcard(
                    subject_slug="anatomy",
                    topic_slug=topic,
                    front=front,
                    back=back,
                    card_type="basic",
                )
            )

    # Practicals
    practicals = [
        ("anatomy", "Bone & Surface Anatomy Spotter",
         "Identify bones, muscles and surface landmarks on a skeleton / living subject.",
         "Skeleton, prosection/specimen, surface anatomy markers.",
         "Palpate bony landmarks and relate them to underlying structures; identify bones on a specimen.",
         ["Identify the clavicle, acromion and spine of scapula.",
          "Palpate the bicipital groove and medial epicondyle.",
          "Identify blood supply and nerve relations for each bone."]),
        ("physiology", "Blood Pressure Measurement",
         "Measure BP with a sphygmomanometer; interpret systolic/diastolic and Korotkoff sounds.",
         "Sphygmomanometer, stethoscope, subject at rest.",
         "Position arm, inflate cuff 20–30 mmHg above radial pulse, deflate slowly and note Korotkoff sounds.",
         ["Apply cuff to bare upper arm at heart level.",
          "Identify the first (systolic) and fifth (diastolic) Korotkoff sounds.",
          "Record BP in mmHg and compare with normal range."]),
    ]
    for subject, title, objective, requirements, principle, steps in practicals:
        existing = (
            await session.execute(select(Practical).where(Practical.title == title))
        ).scalar_one_or_none()
        if existing is None:
            p = Practical(
                subject_slug=subject,
                title=title,
                objective=objective,
                requirements=requirements,
                principle=principle,
                safety_notes="Follow institutional SOP; obtain consent; avoid excessive cuff inflation.",
                clinical_significance="Accurate BP measurement is essential for diagnosing hypertension.",
                reference_text="Standard practical manual / faculty notes.",
                is_published=True,
            )
            session.add(p)
            await session.flush()
        else:
            # Upsert: enrich pre-existing rows with teaching fields.
            existing.subject_slug = subject
            existing.objective = objective
            existing.requirements = requirements
            existing.principle = principle
            existing.is_published = True
        pid = existing.id if existing is not None else p.id
        existing_steps = {
            s.position for s in (await session.execute(select(PracticalStep).where(PracticalStep.practical_id == pid))).scalars().all()
        }
        for i, st in enumerate(steps):
            if i not in existing_steps:
                session.add(PracticalStep(practical_id=pid, position=i, step_text=st))


async def seed_relations(session) -> None:
    """Add anatomical relationships (e.g. supplies / passes through)."""
    def sid(name: str) -> int | None:
        return None  # resolved lazily below

    brachial = (
        await session.execute(select(AnatomicalStructure).where(AnatomicalStructure.preferred_name == "Brachial Plexus"))
    ).scalar_one_or_none()
    median = (
        await session.execute(select(AnatomicalStructure).where(AnatomicalStructure.preferred_name == "Median Nerve"))
    ).scalar_one_or_none()
    brachial_artery = (
        await session.execute(select(AnatomicalStructure).where(AnatomicalStructure.preferred_name == "Brachial Artery"))
    ).scalar_one_or_none()
    axilla = (
        await session.execute(select(AnatomicalStructure).where(AnatomicalStructure.preferred_name == "Axilla"))
    ).scalar_one_or_none()

    if not brachial or not median:
        return

    existing = (
        await session.execute(
            select(AnatomicalRelationship).where(AnatomicalRelationship.structure_a == brachial.id)
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(AnatomicalRelationship(
            structure_a=brachial.id, structure_b=median.id,
            relation_type="gives_rise_to", description="The brachial plexus gives rise to the median nerve."
        ))
        if axilla:
            session.add(AnatomicalRelationship(
                structure_a=brachial.id, structure_b=axilla.id,
                relation_type="passes_through", description="The plexus passes through the axilla."
            ))
        if brachial_artery:
            session.add(AnatomicalRelationship(
                structure_a=brachial_artery.id, structure_b=median.id,
                relation_type="accompanies", description="The brachial artery accompanies the median nerve in the arm."
            ))


async def seed_atlas_model(session) -> None:
    """Add a sample published 3D model + parts + annotation (rights recorded)."""
    region = (
        await session.execute(select(AnatomicalRegion).where(AnatomicalRegion.slug == "upper-limb"))
    ).scalar_one_or_none()
    existing = (
        await session.execute(select(AtlasModel).where(AtlasModel.file_key == "models/upper-limb.glb"))
    ).scalar_one_or_none()
    if existing:
        return
    model = AtlasModel(
        title="Upper Limb Starter Model",
        file_key="models/upper-limb.glb",
        format="glb",
        license="CC BY-SA 2.1 JP",
        creator="BodyParts3D / MEDFREE",
        region_id=region.id if region else None,
        review_status="approved",
        is_published=True,
    )
    session.add(model)
    await session.flush()

    for name in ["Brachial Plexus", "Median Nerve", "Brachial Artery"]:
        struct = (
            await session.execute(select(AnatomicalStructure).where(AnatomicalStructure.preferred_name == name))
        ).scalar_one_or_none()
        part = AtlasModelPart(model_id=model.id, mesh_name=name.lower().replace(" ", "_") + "_mesh", structure_id=struct.id if struct else None)
        session.add(part)
        await session.flush()
        session.add(AtlasAnnotation(model_id=model.id, structure_id=struct.id if struct else None, label=name))


async def seed_knowledge_graph(session) -> None:
    """Seed curriculum knowledge-graph edges (prerequisite / related / next).

    General across subjects (from_slug -> to_slug). Idempotent.
    """
    from app.models.subject import LINK_NEXT, LINK_PREREQUISITE, LINK_RELATED, Topic, TopicLink

    # (from_slug, to_slug, link_type, label, sort_order)
    EDGES = [
        # Upper limb chain (prerequisite + next form the learning path).
        ("shoulder-region", "brachial-plexus", LINK_PREREQUISITE, "Shoulder region before the plexus", 0),
        ("axilla", "brachial-plexus", LINK_PREREQUISITE, "Know the axilla before the plexus", 1),
        ("shoulder-region", "axilla", LINK_NEXT, "Continue to the axilla", 0),
        ("axilla", "brachial-plexus", LINK_NEXT, "Continue to the brachial plexus", 0),
        ("brachial-plexus", "median-nerve", LINK_PREREQUISITE, "Plexus branches precede the median nerve", 0),
        ("brachial-plexus", "median-nerve", LINK_NEXT, "Continue to the median nerve", 0),
        ("brachial-plexus", "shoulder-region", LINK_RELATED, "Related upper-limb structure", 0),
        ("median-nerve", "nerve-conduction", LINK_RELATED, "Nerve lesions & conduction", 0),
        ("inguinal-region", "femoral-triangle", LINK_PREREQUISITE, "Inguinal region precedes the femoral triangle", 0),
        # Physiology.
        ("thoracic-cage", "cardiac-cycle", LINK_PREREQUISITE, "Thorax before the cardiac cycle", 0),
        ("thoracic-cage", "cardiac-cycle", LINK_NEXT, "Continue to the cardiac cycle", 0),
        ("cardiac-cycle", "respiratory-physiology", LINK_RELATED, "Cardiorespiratory link", 0),
        ("respiratory-physiology", "renal-physiology", LINK_RELATED, "Acid-base / fluid link", 0),
        # Biochemistry.
        ("glycolysis", "krebs-cycle", LINK_PREREQUISITE, "Glycolysis precedes the TCA cycle", 0),
        ("glycolysis", "krebs-cycle", LINK_NEXT, "Continue to the TCA cycle", 0),
        ("krebs-cycle", "protein-synthesis", LINK_RELATED, "Metabolism into biosynthesis", 0),
    ]
    topics = {
        t.slug: t.id
        for t in (await session.execute(select(Topic).where(Topic.slug.in_([e[0] for e in EDGES] + [e[1] for e in EDGES])))).scalars().all()
    }
    for from_slug, to_slug, lt, label, order in EDGES:
        fid, tid = topics.get(from_slug), topics.get(to_slug)
        if not fid or not tid:
            continue
        existing = (
            await session.execute(
                select(TopicLink).where(
                    TopicLink.from_topic_id == fid, TopicLink.to_topic_id == tid,
                    TopicLink.link_type == lt,
                )
            )
        ).scalar_one_or_none()
        if existing:
            continue
        session.add(TopicLink(from_topic_id=fid, to_topic_id=tid, link_type=lt, label=label, sort_order=order))
    await session.commit()


async def seed_platform(session) -> None:
    """Add a welcome announcement and a controlled homepage banner (admin)."""
    ann = (
        await session.execute(select(Announcement).where(Announcement.title == "Welcome to MEDFREE"))
    ).scalar_one_or_none()
    if ann is None:
        session.add(
            Announcement(
                kind="system",
                title="Welcome to MEDFREE",
                body="Your free tablet/desktop-first digital medical university. Explore the Human Atlas to begin.",
                is_active=True,
            )
        )

    ad = (
        await session.execute(select(Ad).where(Ad.campaign_id == "welcome_homepage"))
    ).scalar_one_or_none()
    if ad is None:
        session.add(
            Ad(
                placement="homepage",
                title="Start with the Human Atlas",
                image_key=None,
                target_url="/atlas",
                alt_text="Explore the Human Atlas",
                campaign_id="welcome_homepage",
                priority=1,
                is_active=True,
            )
        )


if __name__ == "__main__":
    asyncio.run(run())
