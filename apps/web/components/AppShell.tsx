"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";
import { NAV_ITEMS } from "@medfree/config";
import { useTheme, type Theme } from "./ThemeProvider";
import { useAuth } from "./AuthProvider";
import { TimeOnSiteTimer } from "./TimeOnSiteTimer";

function Icon({ name, className }: { name: string; className?: string }) {
  const paths: Record<string, ReactNode> = {
    home: <path d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1v-10.5Z" />,
    atlas: (
      <>
        <path d="M12 3c-3 3-3 6 0 9s3 6 0 9" />
        <path d="M12 3c3 3 3 6 0 9s-3 6 0 9" />
        <circle cx="12" cy="12" r="1.4" />
      </>
    ),
    learn: <path d="M12 3 2 8l10 5 10-5-10-5Z M2 12v6l10 5 10-5v-6" />,
    practice: <path d="M9 3h6v4l2 2a5 5 0 0 1-10 0l2-2V3Z M12 15v6" />,
    library: <path d="M4 19V5h4v14H4Zm6 0V6h6v13h-6Zm8 0V5h2v14h-2Z" />,
    progress: <path d="M4 20V10M10 20V4M16 20v-7M22 20H2" />,
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m21 21-4.3-4.3" />
      </>
    ),
    theme: <path d="M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9Z" />,
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {paths[name] ?? paths.home}
    </svg>
  );
}

function SearchBox() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<{ type: string; id: number; title: string; subtitle?: string; href?: string }[]>([]);
  const [open, setOpen] = useState(false);

  async function onChange(v: string) {
    setQ(v);
    if (v.length < 2) { setResults([]); setOpen(false); return; }
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(v)}`);
      const data = await res.json();
      setResults(data);
      setOpen(true);
    } catch {
      setResults([]);
    }
  }

  const typeLabel: Record<string, string> = {
    structure: "🧠 Atlas", topic: "📘 Learn", book: "📚 Book",
    resource: "📄 Resource", question: "❓ MCQ", viva: "🗣️ Viva",
  };

  return (
    <div className="relative w-full max-w-md">
      <div className="flex h-10 items-center gap-2 rounded-xl border border-surface-2 bg-surface-1 px-3 focus-within:border-accent">
        <Icon name="search" className="h-4 w-4 text-ink-3" />
        <input
          value={q}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Search anatomy, topics, books…"
          className="w-full bg-transparent text-sm text-ink-1 placeholder:text-ink-3 focus:outline-none"
        />
      </div>
      {open && results.length > 0 && (
        <div className="absolute z-40 mt-2 max-h-96 w-full overflow-auto rounded-xl border border-surface-2 bg-surface-1 shadow-lg">
          {results.map((r, i) => (
            <Link key={`${r.type}-${r.id}`} href={r.href ?? "#"} onClick={() => setOpen(false)}
              className="flex items-center gap-3 border-b border-surface-2 px-3 py-2.5 text-sm hover:bg-surface-2 last:border-0">
              <span className="text-xs">{typeLabel[r.type] ?? r.type}</span>
              <span className="truncate text-ink-1">{r.title}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();
  const themes: Theme[] = ["dark", "light", "midnight", "oled"];
  const labels: Record<Theme, string> = {
    dark: "Dark",
    light: "Light",
    midnight: "Midnight",
    oled: "OLED",
  };
  return (
    <div className="flex items-center gap-1 rounded-xl border border-surface-2 bg-surface-1 p-1">
      <Icon name="theme" className="mx-1 h-4 w-4 text-ink-3" />
      {themes.map((t) => (
        <button
          key={t}
          onClick={() => setTheme(t)}
          title={labels[t]}
          className={`rounded-lg px-2 py-1 text-xs ${
            theme === t ? "bg-accent text-white" : "text-ink-2 hover:bg-surface-2"
          }`}
        >
          {labels[t][0]}
        </button>
      ))}
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { session, signOut, supabase } = useAuth();

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <div className="min-h-[100dvh]">
      {/* Top bar */}
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-surface-2 bg-surface-0/90 px-4 backdrop-blur md:px-8">
        <Link href="/" className="flex items-center gap-2 font-bold tracking-tight">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-white">
            <Icon name="atlas" className="h-5 w-5" />
          </span>
          <span className="hidden sm:inline">MEDFREE</span>
        </Link>
        <div className="flex-1 hidden md:flex justify-center">
          <SearchBox />
        </div>
        <div className="ml-auto flex items-center gap-2">
          <ThemeSwitcher />
          <TimeOnSiteTimer compact />
          {session ? (
            <div className="flex items-center gap-2">
              <span className="hidden rounded-lg bg-surface-2 px-3 py-1.5 text-sm text-ink-2 sm:inline">
                {session.user.email}
              </span>
              <button
                onClick={() => signOut().then(() => router.push("/"))}
                className="rounded-xl bg-surface-2 px-3 py-2 text-sm font-medium hover:bg-surface-3"
              >
                Sign out
              </button>
            </div>
          ) : (
            <Link href="/auth/login" className="rounded-xl bg-surface-2 px-4 py-2 text-sm font-medium hover:bg-surface-3">
              Sign in
            </Link>
          )}
        </div>
      </header>

      <div className="flex">
        {/* Desktop / tablet sidebar */}
        <aside className="sticky top-16 hidden h-[calc(100dvh-4rem)] w-60 shrink-0 border-r border-surface-2 bg-surface-0 px-3 py-6 lg:block">
          <nav className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  isActive(item.href)
                    ? "bg-accent-soft/20 text-accent"
                    : "text-ink-2 hover:bg-surface-2"
                }`}
              >
                <Icon name={item.icon} className="h-5 w-5" />
                {item.label}
                {item.featured && (
                  <span className="ml-auto rounded-full bg-accent/15 px-2 py-0.5 text-[10px] text-accent">
                    Featured
                  </span>
                )}
              </Link>
            ))}
          </nav>

          <div className="mt-8">
            <TimeOnSiteTimer />
          </div>
        </aside>

        {/* Mobile bottom nav */}
        <div className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-around border-t border-surface-2 bg-surface-0/95 py-2 backdrop-blur lg:hidden">
          {NAV_ITEMS.slice(0, 5).map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-1 text-[10px] ${
                isActive(item.href) ? "text-accent" : "text-ink-3"
              }`}
            >
              <Icon name={item.icon} className="h-5 w-5" />
              {item.label}
            </Link>
          ))}
        </div>

        {/* Main content */}
        <main className="flex-1 px-4 pb-24 pt-6 md:px-8 lg:pb-8">{children}</main>
      </div>
    </div>
  );
}
