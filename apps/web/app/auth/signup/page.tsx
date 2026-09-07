"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button, Card } from "@medfree/ui";
import { useAuth } from "@/components/AuthProvider";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { signUp } = useAuth();
  const router = useRouter();

  async function handleSignUp(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    const res = await signUp(email, password);
    setLoading(false);
    if (res.error) setMessage(res.error);
    else if (res.needsConfirm) setMessage("Check your email to confirm your account.");
    else router.push("/");
  }

  return (
    <div className="mx-auto max-w-md">
      <Card>
        <h1 className="text-xl font-bold">Create your account</h1>
        <p className="mt-1 text-sm text-ink-3">Start your free medical university journey.</p>
        <form onSubmit={handleSignUp} className="mt-5 space-y-3">
          <input type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="h-11 w-full rounded-xl border border-surface-2 bg-surface-2/50 px-3 text-sm focus:border-accent focus:outline-none" required />
          <input type="password" placeholder="Password" value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="h-11 w-full rounded-xl border border-surface-2 bg-surface-2/50 px-3 text-sm focus:border-accent focus:outline-none" required minLength={6} />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Creating…" : "Create account"}
          </Button>
        </form>
        {message && <p className="mt-3 text-sm text-accent">{message}</p>}
        <p className="mt-4 text-sm text-ink-3">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-accent hover:underline">Sign in</Link>
        </p>
      </Card>
    </div>
  );
}
