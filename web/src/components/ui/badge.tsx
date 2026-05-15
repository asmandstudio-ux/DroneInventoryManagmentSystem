import * as React from "react";
import { cn } from "@/lib/cn";

export type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
};

const tones: Record<NonNullable<BadgeProps["tone"]>, string> = {
  neutral: "bg-zinc-800 text-zinc-100",
  success: "bg-emerald-600/20 text-emerald-200 ring-1 ring-emerald-600/40",
  warning: "bg-amber-500/20 text-amber-200 ring-1 ring-amber-500/40",
  danger: "bg-red-600/20 text-red-200 ring-1 ring-red-600/40",
  info: "bg-indigo-600/20 text-indigo-200 ring-1 ring-indigo-600/40"
};

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-1 text-xs font-medium",
        tones[tone],
        className
      )}
      {...props}
    />
  );
}

