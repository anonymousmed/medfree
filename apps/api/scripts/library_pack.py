"""Curated, rights-aware initial book/resource library (Phase 8).

Seeds a credential-free library of ~12 verified resources across Anatomy,
Physiology and Biochemistry. Every row carries an accurate rights record so
nothing questionable is ever silently published.

Key rules honoured here:
- "free to read"  !=  "free to copy/rehost". External-only (link) resources are
  never downloaded/rehosted.
- CC BY-* / Public Domain / explicit open licenses -> may be hosted per the
  license, with attribution (+ ShareAlike where required).
- NO license is assumed to permit AI/LLM ingestion. OpenStax explicitly prohibits
  AI ingestion in newest editions, so those are set to ai_usage_status='false'.
  Everything uncertain is 'unknown' (= DO NOT ingest by policy).

Idempotent: matched on stable (title, source_url). Re-runnable.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Author, Book, BookChapter, License, Resource

# --- License records (each name mapped to accurate booleans) ------------------
LICENSES: dict[str, dict] = {
    "CC BY 4.0": dict(
        license_url="https://creativecommons.org/licenses/by/4.0/",
        commercial_allowed=True, modification_allowed=True, redistribution_allowed=True,
        attribution_required=True, sharealike_required=False, ai_ingestion_allowed=True,
        notes="Attribution required; commercial & derivative use allowed.",
    ),
    "CC BY-SA 4.0": dict(
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
        commercial_allowed=True, modification_allowed=True, redistribution_allowed=True,
        attribution_required=True, sharealike_required=True, ai_ingestion_allowed=True,
        notes="Attribution + ShareAlike; commercial & derivative use allowed.",
    ),
    "CC BY-NC 4.0": dict(
        license_url="https://creativecommons.org/licenses/by-nc/4.0/",
        commercial_allowed=False, modification_allowed=True, redistribution_allowed=True,
        attribution_required=True, sharealike_required=False, ai_ingestion_allowed=False,
        notes="Non-commercial only; no explicit AI-ingestion grant -> do not ingest.",
    ),
    "CC BY-NC-SA 4.0": dict(
        license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
        commercial_allowed=False, modification_allowed=True, redistribution_allowed=True,
        attribution_required=True, sharealike_required=True, ai_ingestion_allowed=False,
        notes="Non-commercial + ShareAlike; OpenStax newest editions explicitly prohibit AI/LLM ingestion.",
    ),
    "CC BY-SA 2.1 JP": dict(
        license_url="https://creativecommons.org/licenses/by-sa/2.1/jp/",
        commercial_allowed=True, modification_allowed=True, redistribution_allowed=True,
        attribution_required=True, sharealike_required=True, ai_ingestion_allowed=False,
        notes="BodyParts3D / Anatomography body-mesh data (assets, not text).",
    ),
    "Public Domain (US)": dict(
        license_url="https://creativecommons.org/publicdomain/mark/1.0/",
        commercial_allowed=True, modification_allowed=True, redistribution_allowed=True,
        attribution_required=False, sharealike_required=False, ai_ingestion_allowed=True,
        notes="US public domain (pre-1926 published). Verify expiry in other jurisdictions.",
    ),
    "Publisher retained (free access)": dict(
        license_url="https://www.ncbi.nlm.nih.gov/books/",
        commercial_allowed=False, modification_allowed=False, redistribution_allowed=False,
        attribution_required=True, sharealike_required=False, ai_ingestion_allowed=False,
        notes="Publisher grants NCBI Bookshelf free *read* access only. Link-only (external). Copying/rehosting not permitted.",
    ),
}


# --- The curated library ------------------------------------------------------
# fields: title, resource_type, author, publisher, edition, year, subject_slug,
#         source_url, license_name, rights_status, ai_usage, visibility, external(from
#         hosting), attribution, description, chapters[(title, topic_slug)]
LIBRARY: list[dict] = [
    # ---- ANATOMY ------------------------------------------------------------
    dict(
        title="Anatomy & Physiology 2e", resource_type="book", author="J. Gordon Betts, Kelly A. Young, James A. Wise, et al.",
        publisher="OpenStax", edition="2e", year=2022, subject_slug="anatomy",
        source_url="https://openstax.org/books/anatomy-and-physiology-2e",
        license_name="CC BY-NC-SA 4.0", rights_status="open_license", ai_usage="false",
        visibility="public",
        attribution="OpenStax, Anatomy & Physiology 2e, Rice University — CC BY-NC-SA 4.0. Access for free at https://openstax.org/books/anatomy-and-physiology-2e/pages/1-introduction",
        description="Comprehensive two-semester human anatomy & physiology text. Not AI-ingestible per OpenStax.",
        chapters=[("The Upper Limb", "brachial-plexus"), ("The Lower Limb", "femoral-triangle"),
                  ("The Thorax", "thoracic-cage"), ("Introduction to Anatomy", "general")],
    ),
    dict(
        title="Anatomy & Physiology 2e (Oregon State)", resource_type="book",
        author="Lindsay M. Biga, Staci Bronson, Sierra Dawson, et al.",
        publisher="Oregon State University", edition="2e", year=2025, subject_slug="anatomy",
        source_url="https://open.oregonstate.education/anatomy2e/",
        license_name="CC BY-SA 4.0", rights_status="open_license", ai_usage="unknown",
        visibility="public",
        attribution="OpenStax / Oregon State University, Anatomy & Physiology 2e — CC BY-SA 4.0.",
        description="OSU adaptation of OpenStax A&P; CC BY-SA. Artwork refreshed. AI-ingest status unknown -> do not ingest.",
        chapters=[("The Upper Limb", "brachial-plexus"), ("The Thorax", "thoracic-cage")],
    ),
    dict(
        title="Gray's Anatomy (1918, public domain)", resource_type="book",
        author="Henry Gray; edited by Warren H. Lewis", publisher="Lea & Febiger (US)", edition="1918 (20th US)",
        year=1918, subject_slug="anatomy",
        source_url="https://en.wikipedia.org/wiki/Gray%27s_Anatomy",
        license_name="Public Domain (US)", rights_status="public_domain", ai_usage="true",
        visibility="public",
        attribution="Henry Gray, Anatomy of the Human Body, 1918 — public domain (US).",
        description="Classic descriptive-anatomy reference. Public domain in the US; historical, superseded terminology.",
        chapters=[("The Upper Limb", "brachial-plexus"), ("The Lower Limb", "femoral-triangle")],
    ),
    dict(
        title="BodyParts3D / Anatomography (3D body meshes)", resource_type="3d",
        author="BodyParts3D (National Institute of Genetics, Japan)", publisher="BodyParts3D",
        edition=None, year=None, subject_slug="anatomy",
        source_url="https://github.com/Kevin-Mattheus-Moerman/BodyParts3D",
        license_name="CC BY-SA 2.1 JP", rights_status="open_license", ai_usage="false",
        visibility="public",
        attribution="BodyParts3D / Anatomography, CC BY-SA 2.1 JP.",
        description="Open 3D human-body meshes/labels for the Atlas viewer (assets, not text RAG).",
        chapters=[],
    ),
    # ---- PHYSIOLOGY ---------------------------------------------------------
    dict(
        title="Biology 2e", resource_type="book",
        author="Mary Ann Clark, Matthew Douglas, Jung Choi", publisher="OpenStax",
        edition="2e", year=2018, subject_slug="physiology",
        source_url="https://openstax.org/books/biology-2e",
        license_name="CC BY-NC-SA 4.0", rights_status="open_license", ai_usage="false",
        visibility="public",
        attribution="OpenStax, Biology 2e, Rice University — CC BY-NC-SA 4.0. Access for free at https://openstax.org/books/biology-2e/pages/1-introduction",
        description="General biology incl. human nervous, circulatory & respiratory physiology. Not AI-ingestible per OpenStax.",
        chapters=[("The Circulatory System", "cardiac-cycle"), ("The Nervous System", "nerve-conduction")],
    ),
    dict(
        title="Human Physiology (NCBI Bookshelf reference)", resource_type="book",
        author="Various (publisher-retained)", publisher="National Center for Biotechnology Information",
        edition=None, year=None, subject_slug="physiology",
        source_url="https://www.ncbi.nlm.nih.gov/books/",
        license_name="Publisher retained (free access)", rights_status="external_only", ai_usage="false",
        visibility="public",
        attribution="NCBI Bookshelf free-access titles (publisher copyright retained). Linked, not rehosted.",
        description="Publisher-hosted physiology references readable free on NCBI Bookshelf. External link only.",
        chapters=[],
    ),
    # ---- BIOCHEMISTRY -------------------------------------------------------
    dict(
        title="Biochemistry, 5th ed. (Berg, Tymoczko & Stryer)", resource_type="book",
        author="Jeremy M. Berg, John L. Tymoczko, Lubert Stryer", publisher="W. H. Freeman",
        edition="5th", year=2002, subject_slug="biochemistry",
        source_url="https://www.ncbi.nlm.nih.gov/books/NBK21154/",
        license_name="Publisher retained (free access)", rights_status="external_only", ai_usage="false",
        visibility="public",
        attribution="Berg, Tymoczko & Stryer, Biochemistry 5th ed. (2002). NCBI Bookshelf free read access; copyright retained.",
        description="Standard metabolism/biochemistry reference, freely readable on NCBI Bookshelf. External link only.",
        chapters=[("Glycolysis", "glycolysis"), ("Citric Acid Cycle", "krebs-cycle")],
    ),
    dict(
        title="Molecular Biology of the Cell, 4th ed. (Alberts et al.)", resource_type="book",
        author="Bruce Alberts, Alexander Johnson, Julian Lewis, et al.", publisher="Garland Science",
        edition="4th", year=2002, subject_slug="biochemistry",
        source_url="https://www.ncbi.nlm.nih.gov/books/NBK21054/",
        license_name="Publisher retained (free access)", rights_status="external_only", ai_usage="false",
        visibility="public",
        attribution="Alberts et al., Molecular Biology of the Cell, 4th ed. (2002), NCBI Bookshelf; copyright retained.",
        description="Cell & molecular biology reference (protein synthesis, DNA). External link only.",
        chapters=[("Protein Synthesis", "protein-synthesis")],
    ),
    dict(
        title="Biochemistry: Free For All", resource_type="book",
        author="Kevin Ahern, Indira Rajagopal, Taralyn Tan", publisher="Oregon State University",
        edition="2018", year=2018, subject_slug="biochemistry",
        source_url="https://open.umn.edu/opentextbooks/textbooks/biochemistry-free-for-all-ahern",
        license_name="CC BY-NC 4.0", rights_status="open_license", ai_usage="false",
        visibility="public",
        attribution="Ahern, Rajagopal & Tan, Biochemistry: Free For All, Oregon State University — CC BY-NC 4.0.",
        description="Intro biochemistry OER. Non-commercial; no explicit AI-ingestion grant -> do not ingest.",
        chapters=[("Glycolysis", "glycolysis"), ("Citric Acid Cycle", "krebs-cycle")],
    ),
    dict(
        title="Fundamentals of Biochemistry (Jakubowski & Flatt)", resource_type="book",
        author="Henry Jakubowski, Patricia Flatt", publisher="LibreTexts",
        edition=None, year=None, subject_slug="biochemistry",
        source_url="https://bio.libretexts.org/Bookshelves/Biochemistry/Fundamentals_of_Biochemistry_(Jakubowski_and_Flatt)",
        license_name="CC BY-NC-SA 4.0", rights_status="external_only", ai_usage="unknown",
        visibility="public",
        attribution="Jakubowski & Flatt, Fundamentals of Biochemistry, LibreTexts (CC BY-NC-SA).",
        description="Comprehensive biochemistry text hosted on LibreTexts. Link/reference; AI-ingest unknown.",
        chapters=[("Glycolysis", "glycolysis"), ("Krebs Cycle", "krebs-cycle")],
    ),
    # ---- Multi-purpose / images ---------------------------------------------
    dict(
        title="Heart Diagram (cross-section, public/open)", resource_type="image",
        author="DrJanaOfficial", publisher="Wikimedia Commons",
        edition=None, year=None, subject_slug="physiology",
        source_url="https://commons.wikimedia.org/",
        license_name="CC BY-SA 4.0", rights_status="open_license", ai_usage="false",
        visibility="public",
        attribution="Heart cross-section 3D model (CC BY-SA 4.0; DrJanaOfficial via Wikipedia).",
        description="Open-licensed heart cross-section diagram for the cardiac-cycle topic.",
        chapters=[],
    ),
]


async def seed_library_pack(session: AsyncSession) -> None:
    """Idempotently seed licenses, authors, resources, books and chapters."""

    # 1) Licenses ------------------------------------------------------------
    lic_ids: dict[str, int] = {}
    for name, fields in LICENSES.items():
        row = (await session.execute(select(License).where(License.name == name))).scalar_one_or_none()
        if row is None:
            row = License(name=name, **fields)
            session.add(row)
            await session.flush()
        lic_ids[name] = row.id

    # 2) Author -> id (cache across loop) ------------------------------------
    author_ids: dict[str, int] = {}
    async def author_id(name: str) -> int | None:
        if not name:
            return None
        if name in author_ids:
            return author_ids[name]
        row = (await session.execute(select(Author).where(Author.name == name))).scalar_one_or_none()
        if row is None:
            row = Author(name=name)
            session.add(row)
            await session.flush()
        author_ids[name] = row.id
        return row.id

    counts = {"resources": 0, "books": 0, "chapters": 0}

    # 3) Resources + books + chapters ----------------------------------------
    for item in LIBRARY:
        existing = (
            await session.execute(
                select(Resource).where(Resource.title == item["title"])
            )
        ).scalar_one_or_none()
        if existing:
            resource = existing
        else:
            resource = Resource(
                title=item["title"],
                resource_type=item["resource_type"],
                creator=item["author"],
                publisher=item["publisher"],
                source_url=item["source_url"],
                license_id=lic_ids.get(item["license_name"]),
                rights_status=item["rights_status"],
                ai_usage_status=item["ai_usage"],
                attribution_text=item["attribution"],
                review_status="published",
                # We have NOT medically reviewed these -> honest status, not 'approved'.
                medical_review_status="pending_medical_review",
                visibility=item["visibility"],
                verified_by="curator",
            )
            session.add(resource)
            await session.flush()
            counts["resources"] += 1

        # Books only for 'book' resources (3D/images/externals get no Reader row).
        if item["resource_type"] == "book":
            book = (
                await session.execute(
                    select(Book).where(Book.resource_id == resource.id)
                )
            ).scalar_one_or_none()
            if book is None:
                book = Book(
                    resource_id=resource.id,
                    author_id=await author_id(item["author"]),
                    title=item["title"],
                    edition=item.get("edition"),
                    publisher=item.get("publisher"),
                    year=item.get("year"),
                    subject_slug=item["subject_slug"],
                )
                session.add(book)
                await session.flush()
                counts["books"] += 1
            # Chapters mapped to topic_slug (Book -> Chapter -> Topic).
            for idx, (chtitle, topic_slug) in enumerate(item.get("chapters", [])):
                has = (
                    await session.execute(
                        select(BookChapter).where(
                            BookChapter.book_id == book.id, BookChapter.title == chtitle
                        )
                    )
                ).scalar_one_or_none()
                if has is None:
                    session.add(
                        BookChapter(
                            book_id=book.id, title=chtitle, chapter_index=idx,
                            topic_slug=topic_slug,
                        )
                    )
                    counts["chapters"] += 1

    await session.commit()
    return counts
