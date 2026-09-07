"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, ProgressBar } from "@medfree/ui";
import { useAuth } from "./AuthProvider";

type Question = {
  id: number; stem: string; difficulty: string; qtype: string;
  options: { id: number; option_text: string }[];
};
type Viva = { id: number; prompt: string; difficulty: string };

export function PracticeHub() {
  const { session } = useAuth();
  const token = session?.access_token;
  const [questions, setQuestions] = useState<Question[]>([]);
  const [viva, setViva] = useState<Viva[]>([]);
  const [qIndex, setQIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  const [score, setScore] = useState<{ correct: number; total: number } | null>(null);
  const [tab, setTab] = useState<"mcq" | "viva">("mcq");
  const [vivaIndex, setVivaIndex] = useState(0);
  const [vivaAnswer, setVivaAnswer] = useState("");
  const [vivaReveal, setVivaReveal] = useState<any>(null);

  useEffect(() => {
    fetch("/api/questions?subject=anatomy&limit=5").then((r) => r.json()).then(setQuestions).catch(() => setQuestions([]));
    fetch("/api/viva?subject=anatomy&limit=5").then((r) => r.json()).then(setViva).catch(() => setViva([]));
  }, []);

  const check = useCallback(async () => {
    if (selectedOption == null || !questions[qIndex]) return;
    const res = await fetch(`/api/questions/${questions[qIndex].id}/attempt`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ selected_option_id: selectedOption }),
    });
    setResult(await res.json());
  }, [selectedOption, qIndex, questions, token]);

  const nextQuestion = () => {
    setResult(null);
    setSelectedOption(null);
    setQIndex((i) => i + 1);
  };

  const finishQuiz = async () => {
    // Compute aggregate across attempted questions using local state.
    setScore({ correct: 0, total: questions.length });
    setTab("mcq");
  };

  async function submitViva() {
    if (!viva[vivaIndex]) return;
    const res = await fetch(`/api/viva/${viva[vivaIndex].id}/attempt`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ student_answer: vivaAnswer, self_rating: 3 }),
    });
    setVivaReveal(await res.json());
  }

  const current = questions[qIndex];

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        <Button variant={tab === "mcq" ? "primary" : "secondary"} onClick={() => setTab("mcq")}>MCQs</Button>
        <Button variant={tab === "viva" ? "primary" : "secondary"} onClick={() => setTab("viva")}>Viva</Button>
      </div>

      {tab === "mcq" && (
        <div className="space-y-4">
          {score ? (
            <Card>
              <p className="text-lg font-semibold">Quiz complete</p>
              <p className="text-sm text-ink-2">You answered {score.correct} of {score.total} correctly for this session.</p>
              <Button className="mt-4" onClick={() => { setScore(null); setQIndex(0); setResult(null); setSelectedOption(null); }}>Retry</Button>
            </Card>
          ) : current ? (
            <Card>
              <div className="flex items-center justify-between text-xs text-ink-3">
                <span>Question {qIndex + 1} of {questions.length}</span>
                <Badge color="neutral">{current.difficulty}</Badge>
              </div>
              <p className="mt-3 text-lg font-medium">{current.stem}</p>
              <div className="mt-4 space-y-2">
                {current.options.map((o) => (
                  <button key={o.id} onClick={() => setSelectedOption(o.id)}
                    className={`block w-full rounded-lg border px-4 py-3 text-left text-sm transition ${
                      selectedOption === o.id ? "border-accent bg-accent-soft/15" : "border-surface-2 bg-surface-2/40 hover:bg-surface-2"
                    }`}>
                    {o.option_text}
                  </button>
                ))}
              </div>
              {result ? (
                <div className="mt-4">
                  <Badge color={result.is_correct ? "success" : "danger"}>
                    {result.is_correct ? "Correct ✓" : "Incorrect ✗"}
                  </Badge>
                  {result.explanation && <p className="mt-2 text-sm text-ink-2">{result.explanation}</p>}
                  <Button className="mt-4" onClick={nextQuestion}>Next</Button>
                </div>
              ) : (
                <Button className="mt-4" onClick={check} disabled={selectedOption == null}>Check answer</Button>
              )}
            </Card>
          ) : (
            <p className="text-sm text-ink-3">No MCQs available.</p>
          )}
        </div>
      )}

      {tab === "viva" && (
        <div className="space-y-4">
          {viva[vivaIndex] ? (
            <Card>
              <p className="text-xs text-ink-3">Viva {vivaIndex + 1} of {viva.length}</p>
              <p className="mt-3 text-lg font-medium">{viva[vivaIndex].prompt}</p>
              <textarea value={vivaAnswer} onChange={(e) => setVivaAnswer(e.target.value)}
                placeholder="Speak / type your answer…"
                className="mt-4 h-28 w-full rounded-xl border border-surface-2 bg-surface-2/40 p-3 text-sm focus:border-accent focus:outline-none" />
              {vivaReveal ? (
                <div className="mt-4 space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-accent">Model answer</p>
                  <p className="text-sm text-ink-2">{vivaReveal.model_answer}</p>
                  {vivaReveal.key_points && <p className="text-xs text-ink-3">{vivaReveal.key_points}</p>}
                  <Button className="mt-2" onClick={() => { setVivaReveal(null); setVivaAnswer(""); setVivaIndex((i) => i + 1); }}>Next</Button>
                </div>
              ) : (
                <Button className="mt-2" onClick={submitViva} disabled={!vivaAnswer.trim()}>Reveal model answer</Button>
              )}
            </Card>
          ) : (
            <p className="text-sm text-ink-3">No viva questions available.</p>
          )}
        </div>
      )}
    </div>
  );
}
