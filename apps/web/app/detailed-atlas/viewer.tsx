"use client";

import { useEffect, useRef, useState } from "react";

const DETAILED_ATLAS_URL = "https://human-atlas-seven.vercel.app/";

export function DetailedAtlasViewer() {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [max, setMax] = useState(false);

  // Track real fullscreen state (via the browser's Fullscreen API).
  useEffect(() => {
    const onChange = () => setFullscreen(document.fullscreenElement === wrapperRef.current);
    document.addEventListener("fullscreenchange", onChange);
    return () => document.removeEventListener("fullscreenchange", onChange);
  }, []);

  async function toggleFullscreen() {
    const el = wrapperRef.current;
    if (!el) return;
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await el.requestFullscreen();
    } catch (e) {
      // Some embedded/preview contexts block the Fullscreen API. Fall back to
      // the "max" mode, which expands the viewer to the full viewport height.
      setMax((m) => !m);
    }
  }

  // Esc key exits fullscreen handled natively by the browser; also reset max.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMax(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div ref={wrapperRef} className="overflow-hidden rounded-xl border border-ink-2/15 bg-bg-2/40">
      <div className="flex items-center justify-between gap-2 border-b border-ink-2/10 bg-bg-2/60 px-3 py-2">
        <span className="text-sm font-medium text-ink-2">Detailed Human Atlas · live explorer</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setMax((m) => !m)}
            className="rounded-lg border border-ink-2/15 px-3 py-1.5 text-xs font-medium text-ink-2 transition hover:border-accent/40 hover:text-accent"
          >
            {max ? "Reduce height" : "Tall view"}
          </button>
          <button
            type="button"
            onClick={toggleFullscreen}
            className="rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-white transition hover:brightness-110"
          >
            {fullscreen ? "Exit fullscreen" : "Fullscreen"}
          </button>
        </div>
      </div>
      <iframe
        src={DETAILED_ATLAS_URL}
        title="Detailed Human Atlas"
        className={`w-full ${max ? "h-screen" : "h-[70vh]"}`}
        sandbox="allow-scripts allow-same-origin allow-popups allow-pointer-lock allow-orientation-lock"
        loading="lazy"
        allow="fullscreen; autoplay; xr-spatial-tracking"
      />
    </div>
  );
}
