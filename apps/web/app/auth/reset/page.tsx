"use client";

import { useState } from "react";
import { Button, Card } from "@medfree/ui";
import { useAuth } from "@/components/AuthProvider";

export default function ResetPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { resetPassword } = useAuth();

  async function handleReset(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    const res = await resetPassword(email);
    setLoading(false);
    if (res.error) setMessage(res.error);
    else setMessage("If that account exists, a reset link has been sent.");
  }

  return (
    <div className="mx-auto max-w-md">
      <Card>
        <h1 className="text-xl font-bold">Reset password</h1>
        <p className="mt-1 text-sm text-ink-3">Enter your email and we'll send a recovery link.</p>
        <form onSubmit={handleReset} className="mt-5 space-y-3">
          <input type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="h-11 w-full rounded-xl border border-surface-2 bg-surface-2/50 px-3 text-sm focus:border-accent focus:outline-none" required />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Sending…" : "Send reset link"}
          </Button>
        </form>
        {message && <p className="mt-3 text-sm text-accent">{message}</p>}
      </Card>
    </div>
  );
}
