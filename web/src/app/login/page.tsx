import { Suspense } from "react";
import { LoginClient } from "./LoginClient";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-4">
          <div className="w-full max-w-sm rounded-xl border border-zinc-800 bg-zinc-950 p-6">
            <div className="text-sm text-zinc-200">Loading…</div>
          </div>
        </div>
      }
    >
      <LoginClient />
    </Suspense>
  );
}
