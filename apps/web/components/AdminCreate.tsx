"use client";

import { useState } from "react";
import { Badge, Button, Card, SectionHeading } from "@medfree/ui";
import { useAuth } from "./AuthProvider";

type Kind = "mcq" | "viva" | "flashcard" | "practical";
const KINDS: { key: Kind; label: string }[] = [
  { key: "mcq", label: "MCQ / Question" },
  { key: "viva", label: "Viva question" },
  { key: "flashcard", label: "Flashcard" },
  { key: "practical", label: "Practical" },
];
const SUBJECTS = ["anatomy", "physiology", "biochemistry"];

const input = "mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 text-sm focus:border-accent focus:outline-none";
const label = "block text-xs font-medium text-ink-3";

type Option = { option_text: string; is_correct: boolean; sort_order: number };
type Step = { step_text: string; observation: string; position: number };
type Msg = { type: "ok" | "err"; text: string } | null;

export function AdminCreate() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [kind, setKind] = useState<Kind>("mcq");
  const [mode, setMode] = useState<"single" | "bulk">("single");
  const [msg, setMsg] = useState<Msg>(null);
  const [busy, setBusy] = useState(false);
  const [importText, setImportText] = useState("");

  // Shared
  const [subject, setSubject] = useState("anatomy");
  const [topic, setTopic] = useState("");
  const [published, setPublished] = useState(true);

  // MCQ
  const [stem, setStem] = useState("");
  const [explanation, setExplanation] = useState("");
  const [reference, setReference] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [imageUrl, setImageUrl] = useState("");
  const [options, setOptions] = useState<Option[]>([
    { option_text: "", is_correct: true, sort_order: 0 },
    { option_text: "", is_correct: false, sort_order: 1 },
  ]);

  // Viva
  const [prompt, setPrompt] = useState("");
  const [modelAnswer, setModelAnswer] = useState("");
  const [keyPoints, setKeyPoints] = useState("");

  // Flashcard
  const [front, setFront] = useState("");
  const [back, setBack] = useState("");
  const [cardType, setCardType] = useState("basic");

  // Practical
  const [pTitle, setPTitle] = useState("");
  const [pObjective, setPObjective] = useState("");
  const [pRequirements, setPRequirements] = useState("");
  const [pPrinciple, setPPrinciple] = useState("");
  const [pPrep, setPPrep] = useState("");
  const [pObservation, setPObservation] = useState("");
  const [pInterpretation, setPInterpretation] = useState("");
  const [pMistakes, setPMistakes] = useState("");
  const [pSafety, setPSafety] = useState("");
  const [pClinical, setPClinical] = useState("");
  const [pReference, setPReference] = useState("");
  const [pVideo, setPVideo] = useState("");
  const [steps, setSteps] = useState<Step[]>([{ step_text: "", observation: "", position: 0 }]);

  const headers = (): Record<string, string> => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  });

  async function post<T>(path: string, body: unknown, okMsg: string) {
    setBusy(true);
    setMsg(null);
    try {
      const res = await fetch(path, { method: "POST", headers: headers(), body: JSON.stringify(body) });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail ?? res.statusText);
      setMsg({ type: "ok", text: `${okMsg} (id: ${data.id ?? "created"})` });
      return data;
    } catch (e: any) {
      setMsg({ type: "err", text: e?.message ?? "Failed to create." });
      return null;
    } finally {
      setBusy(false);
    }
  }

  const commonMeta = () => ({
    subject_slug: subject,
    topic_slug: topic || null,
    is_published: published,
  });

  async function submitMcq() {
    if (!stem.trim()) return setMsg({ type: "err", text: "Enter the question stem." });
    const cleanOpts = options.filter((o) => o.option_text.trim()).map((o, i) => ({ ...o, sort_order: i }));
    if (!cleanOpts.some((o) => o.is_correct)) return setMsg({ type: "err", text: "Mark at least one option as correct." });
    await post("/api/admin/content/questions", {
      ...commonMeta(),
      stem, difficulty, explanation: explanation || null, reference: reference || null, image_url: imageUrl || null,
      options: cleanOpts,
    }, "MCQ created");
  }

  async function submitViva() {
    if (!prompt.trim() || !modelAnswer.trim()) return setMsg({ type: "err", text: "Enter the prompt and model answer." });
    await post("/api/admin/content/viva", { ...commonMeta(), prompt, model_answer: modelAnswer, key_points: keyPoints || null, difficulty }, "Viva question created");
  }

  async function submitFlashcard() {
    if (!front.trim() || !back.trim()) return setMsg({ type: "err", text: "Enter both sides of the card." });
    await post("/api/admin/content/flashcards", { ...commonMeta(), front, back, card_type: cardType }, "Flashcard created");
  }

  async function submitPractical() {
    if (!pTitle.trim()) return setMsg({ type: "err", text: "Enter a practical title." });
    const cleanSteps = steps.filter((s) => s.step_text.trim()).map((s, i) => ({ ...s, position: i }));
    await post("/api/admin/content/practicals", {
      ...commonMeta(),
      title: pTitle,
      objective: pObjective || null, requirements: pRequirements || null, principle: pPrinciple || null,
      preparation: pPrep || null, observation: pObservation || null, interpretation: pInterpretation || null,
      common_mistakes: pMistakes || null, safety_notes: pSafety || null, clinical_significance: pClinical || null,
      reference_text: pReference || null, video_url: pVideo || null,
      steps: cleanSteps,
    }, "Practical created");
  }

  // ----- Bulk import -----
  const resourceType: Record<Kind, string> = {
    mcq: "questions", viva: "viva", flashcard: "flashcards", practical: "practicals",
  };

  const template: Record<Kind, string> = {
    mcq: JSON.stringify([
      { subject_slug: "anatomy", topic_slug: "upper-limb", stem: "Which nerve innervates the thenar muscles?", difficulty: "medium", explanation: "Median nerve", is_published: true, options: [ { option_text: "Median nerve", is_correct: true }, { option_text: "Radial nerve", is_correct: false }, { option_text: "Ulnar nerve", is_correct: false } ] },
    ], null, 2),
    viva: JSON.stringify([{ subject_slug: "physiology", topic_slug: "cardiac", prompt: "Explain Starling's law of the heart.", model_answer: "…", key_points: "…", difficulty: "medium", is_published: true }], null, 2),
    flashcard: JSON.stringify([{ subject_slug: "anatomy", topic_slug: "upper-limb", front: "What is the carpal tunnel?", back: "A fibro-osseous canal…", card_type: "basic" }], null, 2),
    practical: JSON.stringify([{ subject_slug: "anatomy", topic_slug: "upper-limb", title: "Brachial plexus examination", objective: "…", is_published: true, steps: [ { step_text: "Inspect the shoulder" }, { step_text: "Test thenar muscles" } ] }], null, 2),
  };

  async function runImport() {
    let items: unknown;
    try {
      items = JSON.parse(importText);
    } catch {
      return setMsg({ type: "err", text: "Invalid JSON. Paste a JSON array (see template)." });
    }
    if (!Array.isArray(items)) return setMsg({ type: "err", text: "JSON must be an array of items." });
    setBusy(true);
    setMsg(null);
    try {
      const res = await fetch("/api/admin/content/import", {
        method: "POST", headers: headers(),
        body: JSON.stringify({ resource_type: resourceType[kind], items }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data?.detail ?? res.statusText);
      setMsg({ type: "ok", text: `Imported ${data.created} ${resourceType[kind]}. Skipped ${data.skipped} invalid. (ids: ${data.ids?.length ?? 0})` });
      setImportText("");
    } catch (e: any) {
      setMsg({ type: "err", text: e?.message ?? "Import failed." });
    } finally {
      setBusy(false);
    }
  }

  async function onImportFile(f: File | undefined) {
    if (!f) return;
    const text = await f.text();
    setImportText(text);
    setMsg(null);
  }

  if (!token) return <Card className="p-6 text-center text-ink-2">Sign in with an admin account to create content.</Card>;

  const setOpt = (i: number, patch: Partial<Option>) =>
    setOptions((o) => o.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  const setStep = (i: number, patch: Partial<Step>) =>
    setSteps((s) => s.map((x, j) => (j === i ? { ...x, ...patch } : x)));

  return (
    <div className="space-y-6">
      <SectionHeading eyebrow="Admin authoring" title="Create content" subtitle="Add MCQs, viva questions, flashcards and practicals — one at a time, or bulk import many at once." />

      <div className="flex flex-wrap gap-2">
        {KINDS.map((k) => (
          <button key={k.key} onClick={() => { setKind(k.key); setMsg(null); }}
            className={`rounded-full px-4 py-2 text-sm ${kind === k.key ? "bg-accent text-white" : "border border-surface-2 text-ink-2 hover:border-accent/40"}`}>
            {k.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        {(["single", "bulk"] as const).map((m) => (
          <button key={m} onClick={() => { setMode(m); setMsg(null); }}
            className={`rounded-xl px-4 py-2 text-sm font-medium ${mode === m ? "bg-accent text-white" : "border border-surface-2 text-ink-2 hover:border-accent/40"}`}>
            {m === "single" ? "Add one" : "Bulk import"}
          </button>
        ))}
        {mode === "bulk" && (
          <button onClick={() => { setImportText(template[kind]); setMsg(null); }}
            className="rounded-xl border border-accent/40 px-4 py-2 text-sm text-accent hover:bg-accent/10">
            Load template
          </button>
        )}
      </div>

      {msg && <p className={`text-sm ${msg.type === "ok" ? "text-accent" : "text-red-400"}`}>{msg.text}</p>}

      {mode === "bulk" && (
        <Card className="space-y-4 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold">Bulk import {resourceType[kind]}</p>
              <p className="text-xs text-ink-3">
                Paste a JSON array below (or drop a .json file). Each item uses the same fields as
                the single form. Invalid items are skipped and reported. Supports up to 2,000 items.
              </p>
            </div>
            <Badge color="accent">{resourceType[kind]}</Badge>
          </div>
          <label className={label}>
            Paste JSON array
            <textarea value={importText} onChange={(e) => setImportText(e.target.value)} rows={14} spellCheck={false}
              className="mt-1 w-full rounded-xl border border-surface-2 bg-surface-1 px-3 py-2 font-mono text-xs focus:border-accent focus:outline-none"
              placeholder={template[kind]} />
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={runImport} disabled={busy}>{busy ? "Importing…" : `Import ${resourceType[kind]}`}</Button>
            <label className="cursor-pointer rounded-xl border border-surface-2 px-4 py-2 text-sm font-medium text-ink-2 hover:border-accent/40">
              Upload .json file
              <input type="file" accept=".json,application/json" className="hidden" onChange={(e) => onImportFile(e.target.files?.[0])} />
            </label>
          </div>
        </Card>
      )}

      {mode === "single" && (
        <>
      {/* Subject / topic / published — shared */}
      <Card className="p-5">
        <div className="grid gap-3 sm:grid-cols-3">
          <label className={label}>
            Subject
            <select value={subject} onChange={(e) => setSubject(e.target.value)} className={input}>
              {SUBJECTS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className={label}>
            Topic slug <span className="text-ink-3">(optional)</span>
            <input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. upper-limb" className={input} />
          </label>
          <label className={label}>
            Visibility
            <select value={published ? "pub" : "draft"} onChange={(e) => setPublished(e.target.value === "pub")} className={input}>
              <option value="pub">Published (public)</option>
              <option value="draft">Draft (hidden)</option>
            </select>
          </label>
        </div>
      </Card>

      {kind === "mcq" && (
        <Card className="space-y-4 p-5">
          <div className="flex items-center justify-between">
            <p className="font-semibold">MCQ / single-best-answer</p>
            <Badge color="accent">questions</Badge>
          </div>
          <label className={label}>Question stem
            <textarea value={stem} onChange={(e) => setStem(e.target.value)} rows={3} className={input} placeholder="Which nerve innervates the thenar muscles?" />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className={label}>Difficulty
              <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className={input}>
                <option value="basic">Basic</option><option value="medium">Medium</option><option value="advanced">Advanced</option>
              </select>
            </label>
            <label className={label}>Image URL <span className="text-ink-3">(optional)</span>
              <input value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} className={input} placeholder="https://…" />
            </label>
          </div>
          <div className="space-y-2">
            <p className="text-xs font-medium text-ink-3">Options — tick the correct one(s)</p>
            {options.map((o, i) => (
              <div key={i} className="flex items-center gap-2">
                <input type="checkbox" checked={o.is_correct} onChange={(e) => setOpt(i, { is_correct: e.target.checked })}
                  className="h-4 w-4 accent-[var(--accent)]" />
                <input value={o.option_text} onChange={(e) => setOpt(i, { option_text: e.target.value })}
                  placeholder={`Option ${i + 1}`} className={input} />
                <button type="button" onClick={() => setOptions((x) => x.filter((_, j) => j !== i))}
                  className="text-xs text-ink-3 hover:text-red-400" disabled={options.length <= 2}>Remove</button>
              </div>
            ))}
            <button type="button" onClick={() => setOptions((x) => [...x, { option_text: "", is_correct: false, sort_order: x.length }])}
              className="text-xs text-accent">+ Add option</button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className={label}>Explanation <span className="text-ink-3">(shown after answering)</span>
              <textarea value={explanation} onChange={(e) => setExplanation(e.target.value)} rows={2} className={input} />
            </label>
            <label className={label}>Reference
              <input value={reference} onChange={(e) => setReference(e.target.value)} className={input} />
            </label>
          </div>
          <Button onClick={submitMcq} disabled={busy}>{busy ? "Creating…" : "Create MCQ"}</Button>
        </Card>
      )}

      {kind === "viva" && (
        <Card className="space-y-4 p-5">
          <div className="flex items-center justify-between">
            <p className="font-semibold">Viva question</p>
            <Badge color="accent">viva</Badge>
          </div>
          <label className={label}>Prompt
            <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={2} className={input} placeholder="Explain Starling's law of the heart." />
          </label>
          <label className={label}>Model answer
            <textarea value={modelAnswer} onChange={(e) => setModelAnswer(e.target.value)} rows={3} className={input} />
          </label>
          <label className={label}>Key points <span className="text-ink-3">(separated by newlines)</span>
            <textarea value={keyPoints} onChange={(e) => setKeyPoints(e.target.value)} rows={2} className={input} />
          </label>
          <label className={label}>Difficulty
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className={input}>
              <option value="basic">Basic</option><option value="medium">Medium</option><option value="advanced">Advanced</option>
            </select>
          </label>
          <Button onClick={submitViva} disabled={busy}>{busy ? "Creating…" : "Create viva"}</Button>
        </Card>
      )}

      {kind === "flashcard" && (
        <Card className="space-y-4 p-5">
          <div className="flex items-center justify-between">
            <p className="font-semibold">Flashcard (front / back)</p>
            <Badge color="accent">flashcards</Badge>
          </div>
          <label className={label}>Front (question / term)
            <textarea value={front} onChange={(e) => setFront(e.target.value)} rows={2} className={input} placeholder="What is Km?" />
          </label>
          <label className={label}>Back (answer / definition)
            <textarea value={back} onChange={(e) => setBack(e.target.value)} rows={2} className={input} placeholder="Michaelis constant." />
          </label>
          <label className={label}>Card type
            <select value={cardType} onChange={(e) => setCardType(e.target.value)} className={input}>
              <option value="basic">Basic</option><option value="cloze">Cloze</option><option value="image">Image</option>
            </select>
          </label>
          <Button onClick={submitFlashcard} disabled={busy}>{busy ? "Creating…" : "Create flashcard"}</Button>
        </Card>
      )}

      {kind === "practical" && (
        <Card className="space-y-4 p-5">
          <div className="flex items-center justify-between">
            <p className="font-semibold">Practical</p>
            <Badge color="accent">practicals</Badge>
          </div>
          <label className={label}>Title
            <input value={pTitle} onChange={(e) => setPTitle(e.target.value)} className={input} placeholder="Brachial plexus examination" />
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className={label}>Objective
              <textarea value={pObjective} onChange={(e) => setPObjective(e.target.value)} rows={2} className={input} />
            </label>
            <label className={label}>Requirements
              <textarea value={pRequirements} onChange={(e) => setPRequirements(e.target.value)} rows={2} className={input} />
            </label>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className={label}>Principle
              <textarea value={pPrinciple} onChange={(e) => setPPrinciple(e.target.value)} rows={2} className={input} />
            </label>
            <label className={label}>Preparation
              <textarea value={pPrep} onChange={(e) => setPPrep(e.target.value)} rows={2} className={input} />
            </label>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className={label}>Observation
              <textarea value={pObservation} onChange={(e) => setPObservation(e.target.value)} rows={2} className={input} />
            </label>
            <label className={label}>Interpretation
              <textarea value={pInterpretation} onChange={(e) => setPInterpretation(e.target.value)} rows={2} className={input} />
            </label>
          </div>
          <label className={label}>Video URL <span className="text-ink-3">(optional)</span>
            <input value={pVideo} onChange={(e) => setPVideo(e.target.value)} className={input} />
          </label>
          <div className="space-y-2">
            <p className="text-xs font-medium text-ink-3">Steps (in order)</p>
            {steps.map((s, i) => (
              <div key={i} className="flex items-center gap-2">
                <input value={s.step_text} onChange={(e) => setStep(i, { step_text: e.target.value })}
                  placeholder={`Step ${i + 1}`} className={input} />
                <button type="button" onClick={() => setSteps((x) => x.filter((_, j) => j !== i))}
                  className="text-xs text-ink-3 hover:text-red-400" disabled={steps.length <= 1}>Remove</button>
              </div>
            ))}
            <button type="button" onClick={() => setSteps((x) => [...x, { step_text: "", observation: "", position: x.length }])}
              className="text-xs text-accent">+ Add step</button>
          </div>
          <Button onClick={submitPractical} disabled={busy}>{busy ? "Creating…" : "Create practical"}</Button>
        </Card>
      )}
        </>
      )}
    </div>
  );
}
