"""MEDFREE content pack (Step 19 — Content Expansion).

A structured, data-driven expansion of first-year learning content. Each entry is
idempotently seeded (matched by a stable key) so re-running is safe. Content is
intentionally curated to be medically reasonable and pedagogically useful; it is
NOT authoritative and must still pass medical review before any clinical claim is
treated as definitive (spec §55, §72).

Organised so it scales: add to STRUCTURES / TOPICS / QUESTIONS / VIVA /
FLASHCARDS / PRACTICALS / BOOKS and re-run the seeder.
"""

# ---------------------------------------------------------------------------
# Struct: (preferred_name, latin_name, region, system, description, clinical)
# ---------------------------------------------------------------------------
UPPER_LIMB_STRUCTURES = [
    ("Axillary Artery", "Arteria axillaris", "upper-limb", "cardiovascular",
     "Continuation of subclavian artery; divided by pectoralis minor into three parts.",
     "Compressible at the lateral axillary wall; common site of traumatic injury."),
    ("Radial Nerve", "Nervus radialis", "upper-limb", "nervous",
     "Terminal branch of posterior cord; supplies extensor compartment of the arm and forearm.",
     "Radial nerve injury → wrist drop; common with humeral shaft fracture."),
    ("Ulnar Nerve", "Nervus ulnaris", "upper-limb", "nervous",
     "Terminal branch of medial cord; runs in ulnar groove and supplies intrinsic hand muscles.",
     "Ulnar groove compression → 'claw hand'; ring & little finger paresthesia."),
    ("Scapula", "Scapula", "upper-limb", "skeletal",
     "Flat triangular bone of the shoulder girdle with spine, acromion and glenoid.",
     "Winging after long thoracic nerve injury."),
    ("Humerus", "Humerus", "upper-limb", "skeletal",
     "Long bone of the arm; radial nerve grooves the posterior aspect.",
     "Surgical neck fracture risks axillary nerve injury; shaft fracture risks radial nerve."),
    ("Biceps Brachii", "Musculus biceps brachii", "upper-limb", "muscular",
     "Two-headed flexor of the shoulder and elbow; tendon inserts on radial tuberosity.",
     "Distal tendon rupture; biceps reflex (C5–C6)."),
    ("Carpal Tunnel", "Canalis carpi", "upper-limb", "muscular",
     "Fibrous tunnel between carpal bones and flexor retinaculum containing median nerve and flexor tendons.",
     "Compression → carpal tunnel syndrome: thenar wasting, median distribution paresthesia."),
]

THORAX_STRUCTURES = [
    ("Heart", "Cor", "thorax", "cardiovascular",
     "Four-chambered muscular pump in the mediastinum; base directed posteriorly.",
     "Auscultation points; ischaemic heart disease in clinical cases."),
    ("Lung", "Pulmo", "thorax", "respiratory",
     "Paired spongy organ of respiration; right lung has three lobes, left two.",
     "Pleural effusion; lung cancer; lobar collapse in clinical vignettes."),
    ("Aorta", "Aorta", "thorax", "cardiovascular",
     "Largest artery; thoracic aorta descends posteriorly to become abdominal aorta.",
     "Aortic dissection — a hypertensive emergency."),
    ("Trachea", "Trachea", "thorax", "respiratory",
     "Cartilaginous airway from larynx to main bronchi; bifurcates at T4/5.",
     "Tracheal deviation; foreign body aspiration (right main bronchus more common)."),
    ("Diaphragm", "Diaphragma", "thorax", "muscular",
     "Dome-shaped muscle separating thorax from abdomen; main muscle of respiration.",
     "Phrenic nerve (C3–C5) paralysis → paradoxical movement."),
]

ABDOMEN_STRUCTURES = [
    ("Liver", "Hepar", "abdomen", "digestive",
     "Largest gland; right-located organ in the upper abdomen with portal circulation.",
     "Cirrhosis, hepatomegaly, liver function tests in clinical cases."),
    ("Kidney", "Ren", "abdomen", "urinary",
     "Retroperitoneal bean-shaped organ; renal artery enters hilum.",
     "Renal colic; nephrotic syndrome; electrolyte disturbances."),
    ("Spleen", "Lien", "abdomen", "digestive",
     "Left upper-abdominal lymphatic organ; single largest collection of lymphoid tissue.",
     "Splenic rupture after trauma; left-upper-abdomen crescent sign on imaging."),
    ("Stomach", "Gaster", "abdomen", "digestive",
     "J-shaped organ of the gut; produces acid and intrinsic factor.",
     "Peptic ulcer; gastric carcinoma; anaemia from intrinsic factor loss."),
    ("Appendix", "Appendix vermiformis", "abdomen", "digestive",
     "Vermiform diverticulum of the caecum; located at McBurney's point.",
     "Acute appendicitis — rebound tenderness at McBurney's point."),
]

HEAD_NECK_STRUCTURES = [
    ("Carotid Artery", "Arteria carotis communis", "head-neck", "cardiovascular",
     "Common carotid bifurcates into internal and external carotid at C4 level.",
     "Carotid bruit; carotid sinus massage for paroxysmal tachycardia."),
    ("Thyroid Gland", "Glandula thyroidea", "head-neck", "endocrine",
     "Endocrine gland in the anterior neck secreting thyroid hormones.",
     "Goitre, hypothyroidism/hyperthyroidism; recurrent laryngeal nerve injury."),
    ("Facial Nerve", "Nervus facialis", "head-neck", "nervous",
     "Seventh cranial nerve; provides motor supply to facial expression muscles.",
     "Bell's palsy; differentiate upper vs lower motor neuron facial palsy."),
    ("Parotid Gland", "Glandula parotidea", "head-neck", "digestive",
     "Largest salivary gland; pierced by facial nerve.",
     "Parotitis (mumps); facial nerve injury during parotid surgery."),
]

NEURO_STRUCTURES = [
    ("Spinal Cord", "Medulla spinalis", "neuroanatomy", "nervous",
     "Relays between brain and body; ends at L1/L2 (conus medullaris).",
     "Spinal cord syndromes; lumbar puncture below L2."),
    ("Cerebellum", "Cerebellum", "neuroanatomy", "nervous",
     "Coordinates movement, balance and posture.",
     "Cerebellar ataxia; intention tremor; dysdiadochokinesis."),
    ("Internal Capsule", "Capsula interna", "neuroanatomy", "nervous",
     "Major white-matter pathway connecting cerebral cortex to brainstem/spinal cord.",
     "Lacunar stroke → contralateral hemiplegia ('face-arm-leg')."),
]

STRUCTURES = (
    UPPER_LIMB_STRUCTURES + THORAX_STRUCTURES + ABDOMEN_STRUCTURES
    + HEAD_NECK_STRUCTURES + NEURO_STRUCTURES
)

# ---------------------------------------------------------------------------
# Topics: (subject_slug, slug, title, summary) — each gets a full block set.
# ---------------------------------------------------------------------------
TOPICS = [
    ("anatomy", "axilla", "Axilla", "Pyramidal space of the upper limb bounded by the axillary walls; route for neurovascular structures."),
    ("anatomy", "shoulder-region", "Shoulder Joint", "Synovial ball-and-socket joint with a wide range of movement and a prone-to-dislocation labrum."),
    ("anatomy", "thoracic-cage", "Thoracic Cage", "Osteocartilaginous cage protecting thoracic viscera and supporting respiration."),
    ("anatomy", "inguinal-region", "Inguinal Region", "Groin region of the anterior abdominal wall; site of hernias."),
    ("physiology", "cardiac-cycle", "Cardiac Cycle", "Sequence of mechanical events of the heart from atrial contraction to ventricular relaxation."),
    ("physiology", "respiratory-physiology", "Respiratory Physiology", "Mechanics of breathing, lung volumes and gas exchange."),
    ("physiology", "renal-physiology", "Renal Physiology", "Filtration, reabsorption and secretion underlying urine formation."),
    ("physiology", "nerve-conduction", "Nerve Conduction", "Resting membrane potential and action potential propagation along axons."),
    ("biochemistry", "glycolysis", "Glycolysis", "Cytoplasmic pathway converting glucose to pyruvate with net ATP yield."),
    ("biochemistry", "krebs-cycle", "Krebs Cycle", "Mitochondrial oxidative pathway oxidising acetyl-CoA to CO2."),
    ("biochemistry", "protein-synthesis", "Protein Synthesis", "Transcription and translation directing protein synthesis."),
]

# Map a topic slug to the Atlas region for its 3D/Atlas block.
BLOCK_REGION_MAP = {
    "axilla": "upper-limb",
    "shoulder-region": "upper-limb",
    "thoracic-cage": "thorax",
    "inguinal-region": "abdomen",
    "cardiac-cycle": "thorax",
    "breathing": "thorax",
}


# ---------------------------------------------------------------------------
# Block generator: builds 11 structured blocks per topic.
# ---------------------------------------------------------------------------
def blocks_for(title: str, slug: str, summary: str, region: str | None = None):
    return [
        ("overview", "Quick Overview", summary, None),
        ("objectives", "Learning Objectives",
         f"- Explain the key structures and functions of {title}.\n- Relate {title} to clinical practice.\n- Interpret the relevant diagrams and data.", None),
        ("atlas", "Human Atlas / 3D", f"Explore {title} in the interactive 3D Human Atlas.",
         '{"type":"atlas","region":"%s"}' % (region or "upper-limb")),
        ("diagram", "Interactive Diagram", f"Interactive schematic of {title}. Toggle layers to build understanding.", None),
        ("clinical", "Clinical Correlation",
         f"Common clinical scenarios involving {title}, and how to interpret the findings.", None),
        ("mcq", "MCQs", f"Attempt questions on {title}.", '{"type":"mcq","topic":"%s"}' % slug),
        ("viva", "Viva", f"Practice oral exam questions on {title}.", '{"type":"viva","topic":"%s"}' % slug),
        ("flashcards", "Flashcards", f"Active-recall flashcards for {title}.", '{"type":"flashcard","topic":"%s"}' % slug),
        ("practical", "Practical / Spotter", f"Identify and demonstrate {title}.", '{"type":"practical","topic":"%s"}' % slug),
        ("books", "Books & Research", "Refer to OpenStax, Gray's Anatomy for Students, and NCBI Bookshelf.", None),
        ("revision", "Revision", f"Quick recap of {title}: key points, diagrams and mnemonics.", None),
    ]


# ---------------------------------------------------------------------------
# Questions: (subject_slug, topic_slug, difficulty, stem, options[4], correct_idx, explanation)
# ---------------------------------------------------------------------------
QUESTIONS = [
    ("anatomy", "axilla", "easy", "Which structure forms the lateral wall of the axilla?", ["Pectoralis major & minor", "Serratus anterior", "Humerus", "Latissimus dorsi"], 0, "The lateral wall is formed by the intertubercular groove of the humerus."),
    ("anatomy", "shoulder-region", "easy", "The most commonly dislocated joint is:", ["Hip", "Shoulder", "Knee", "Elbow"], 1, "The shoulder dislocates most commonly, usually anteriorly."),
    ("anatomy", "thoracic-cage", "medium", "Which rib attaches only to the transverse process of C7?", ["1st", "Cervical rib -> may be present", "11th", "12th"], 1, "A cervical rib is a congenital anomaly at C7."),
    ("anatomy", "inguinal-region", "medium", "The inguinal ligament is formed by:", ["External oblique aponeurosis", "Internal oblique", "Transversus abdominis", "Fascia lata"], 0, "The lower border of the external oblique aponeurosis forms the inguinal ligament."),
    ("physiology", "cardiac-cycle", "easy", "The first heart sound (S1) coincides with:", ["Atrial systole", "Closure of AV valves", "Closure of semilunar valves", "Opening of AV valves"], 1, "S1 marks the onset of ventricular systole and closure of the AV valves."),
    ("physiology", "respiratory-physiology", "easy", "The volume of air moved in and out with each breath is:", ["Tidal volume", "Vital capacity", "Residual volume", "Minute volume"], 0, "Tidal volume is ~500 mL of air per breath."),
    ("physiology", "renal-physiology", "medium", "The glomerular filtration barrier does NOT normally allow passage of:", ["Water", "Electrolytes", "Albumin", "Urea"], 2, "The filtration barrier excludes proteins such as albumin."),
    ("physiology", "nerve-conduction", "medium", "The resting membrane potential is maintained primarily by:", ["Na+/K+-ATPase", "Voltage-gated channels", "T-tubules", "Sarcoplasmic reticulum"], 0, "The sodium-potassium pump maintains the ionic gradients underlying the resting potential."),
    ("biochemistry", "glycolysis", "easy", "Net ATP yield per glucose molecule in glycolysis is:", ["1", "2", "4", "6"], 1, "Glycolysis yields a net of 2 ATP per glucose."),
    ("biochemistry", "krebs-cycle", "medium", "Which is NOT a product of one turn of the Krebs cycle?", ["2 CO2", "3 NADH", "1 FADH2", "4 ATP directly"], 3, "The Krebs cycle produces GTP (equivalent to ATP) but not 4 ATP directly."),
    ("biochemistry", "protein-synthesis", "medium", "Transcription of DNA occurs in the:", ["Cytoplasm", "Nucleus", "Ribosome", "Golgi apparatus"], 1, "Transcription of DNA to mRNA occurs in the nucleus."),
]


# ---------------------------------------------------------------------------
# Viva: (subject_slug, topic_slug, prompt, model_answer, key_points)
# ---------------------------------------------------------------------------
VIVA = [
    ("anatomy", "axilla", "What are the contents of the axilla?", "Axillary artery, vein, brachial plexus cords, lymph nodes, and axillary fat.", "Artery, vein, plexus, lymph nodes, fat."),
    ("anatomy", "shoulder-region", "Describe the rotator cuff muscles.", "Supraspinatus, infraspinatus, teres minor, subscapularis (SITS).", "SITS: 4 muscles; stabilize the shoulder."),
    ("anatomy", "thoracic-cage", "How many ribs are there typically?", "Usually 12 pairs (24 ribs).", "12 pairs; 1-7 true, 8-12 false."),
    ("physiology", "cardiac-cycle", "Define cardiac output.", "Cardiac output = stroke volume × heart rate (~5 L/min).", "CO = SV × HR."),
    ("physiology", "respiratory-physiology", "What is the vital capacity?", "Maximum volume of air exhaled after a maximal inspiration.", "Tidal + inspiratory reserve + expiratory reserve."),
    ("physiology", "renal-physiology", "What is the glomerular filtration rate?", "Volume of filtrate formed per minute (~125 mL/min).", "GFR ~125 mL/min."),
    ("biochemistry", "glycolysis", "Where does glycolysis occur?", "In the cytoplasm of cells.", "Cytoplasmic pathway; net 2 ATP."),
    ("biochemistry", "krebs-cycle", "Where does the Krebs cycle occur?", "In the mitochondrial matrix.", "Mitochondrial matrix."),
]


# ---------------------------------------------------------------------------
# Flashcards: (subject_slug, topic_slug, front, back)
# ---------------------------------------------------------------------------
FLASHCARDS = [
    ("anatomy", "axilla", "What forms the anterior wall of the axilla?", "Pectoralis major and pectoralis minor."),
    ("anatomy", "shoulder-region", "Name the rotator cuff muscles (SITS).", "Supraspinatus, infraspinatus, teres minor, subscapularis."),
    ("anatomy", "thoracic-cage", "True ribs are:", "Ribs 1–7."),
    ("anatomy", "inguinal-region", "Hesselbach's triangle boundaries.", "Inguinal ligament, rectus abdominis, inferior epigastric artery."),
    ("physiology", "cardiac-cycle", "What is stroke volume?", "Blood ejected per ventricular beat (~70 mL)."),
    ("physiology", "respiratory-physiology", "Define residual volume.", "Air remaining in lungs after maximal expiration."),
    ("physiology", "renal-physiology", "Normal GFR in adults.", "~125 mL/min or 180 L/day."),
    ("physiology", "nerve-conduction", "Resting membrane potential value.", "~-70 mV."),
    ("biochemistry", "glycolysis", "Final product of glycolysis.", "Pyruvate (2 ATP net)."),
    ("biochemistry", "krebs-cycle", "First step of the Krebs cycle.", "Acetyl-CoA combines with oxaloacetate to form citrate."),
    ("biochemistry", "protein-synthesis", "Site of translation.", "Ribosomes."),
]


# ---------------------------------------------------------------------------
# Practicals: (subject_slug, title, objective, requirements, principle, steps[])
# ---------------------------------------------------------------------------
PRACTICALS = [
    ("anatomy", "Surface Marking of the Heart", "Outline the surface markings of the heart on the chest wall.",
     "Skeleton/mannikin, marker pen, surface anatomy landmarks.",
     "Project the heart's borders onto the anterior chest wall.", [
        "Identify the sternal angle and xiphisternum.",
        "Mark the apex beat (left 5th intercostal space, midclavicular line).",
        "Join the borders to create the cardiac outline."]),
    ("physiology", "ECG Recording", "Record and interpret a standard 12-lead ECG.",
     "ECG machine, electrodes, conductive gel, subject at rest.",
     "ECG records the electrical activity of the heart; calculate rate and rhythm.", [
        "Prepare skin and attach limb + chest electrodes.",
        "Record a 10-second rhythm strip and standard leads.",
        "Identify rate, rhythm, and any ST/T changes."]),
    ("biochemistry", "Urine Analysis", "Perform a routine urine examination (physical, chemical, microscopic).",
     "Urine sample, reagent strips, centrifuge, microscope.",
     "Physical/chemical/microscopic analysis informs renal and systemic disease.", [
        "Observe colour, appearance and odour.",
        "Test with reagent strips for protein, glucose, blood and pH.",
        "Centrifuge and examine the sediment microscopically."]),
]
