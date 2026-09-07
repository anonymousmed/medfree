"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, Card } from "@medfree/ui";
import { useAuth } from "@/components/AuthProvider";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { signIn, supabase } = useAuth();
  const router = useRouter();

  async function handleSignIn(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    const res = await signIn(email, password);
    setLoading(false);
    if (res.error) setMessage(res.error);
    else router.push("/");
  }

  return (
    <div className="mx-auto max-w-md">
      <Card>
        <h1 className="text-xl font-bold">Welcome back</h1>
        <p className="mt-1 text-sm text-ink-3">Sign in to continue your medical university.</p>
        <form onSubmit={handleSignIn} className="mt-5 space-y-3">
          <input
            type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="h-11 w-full rounded-xl border border-surface-2 bg-surface-2/50 px-3 text-sm focus:border-accent focus:outline-none" required
          />
          <input
            type="password" placeholder="Password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="h-11 w-full rounded-xl border border-surface-2 bg-surface-2/50 px-3 text-sm focus:border-accent focus:outline-none" required
          />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </Button>
        </form>
        {message && <p className="mt-3 text-sm text-accent">{message}</p>}
        <div className="mt-4 flex items-center justify-between text-sm">
          <Link href="/auth/signup" className="text-accent hover:underline">Create account</Link>
          <Link href="/auth/reset" className="text-accent hover:underline">Forgot password?</Link>
        </div>
        <button
          onClick={async () => {
            if (!supabase) { setMessage("Supabase not configured"); return; }
            await supabase.auth.signInWithOAuth({ provider: "google" });
          }}
          className="mt-3 w-full rounded-xl border border-surface-2 bg-surface-2 py-3 text-sm font-medium hover:bg-surface-3"
        >
          Continue with Google
        </button>
      </Card>
    </div>
  );
}
