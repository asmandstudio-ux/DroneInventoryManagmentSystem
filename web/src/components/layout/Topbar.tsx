"use client";

import { ReactNode } from "react";

export function Topbar({ title, right }: { title: string; right?: ReactNode }) {
  return (
    <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
      <div>
        <h1 className="text-base font-semibold text-zinc-50">{title}</h1>
      </div>
      <div className="flex items-center gap-2">{right}</div>
    </header>
  );
}

