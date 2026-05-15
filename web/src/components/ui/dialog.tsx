"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";

type DialogProps = {
  open: boolean;
  title?: string;
  description?: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
};

export function Dialog({ open, title, description, onClose, children, footer }: DialogProps) {
  const [mounted, setMounted] = React.useState(false);
  const panelRef = React.useRef<HTMLDivElement | null>(null);
  const titleId = React.useId();
  const descriptionId = React.useId();

  React.useEffect(() => setMounted(true), []);

  React.useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    // Focus the dialog panel for keyboard users.
    panelRef.current?.focus();
    return () => prev?.focus();
  }, [open]);

  React.useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  React.useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  React.useEffect(() => {
    if (!open) return;
    const panel = panelRef.current;
    if (!panel) return;

    const getFocusable = () => {
      const selectors = [
        'a[href]:not([tabindex="-1"])',
        'button:not([disabled]):not([tabindex="-1"])',
        'input:not([disabled]):not([tabindex="-1"])',
        'select:not([disabled]):not([tabindex="-1"])',
        'textarea:not([disabled]):not([tabindex="-1"])',
        '[tabindex]:not([tabindex="-1"])'
      ];
      const nodes = Array.from(panel.querySelectorAll<HTMLElement>(selectors.join(",")));
      // Filter out elements that are not actually visible/focusable.
      return nodes.filter((el) => el.offsetParent !== null);
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Tab") return;
      const focusable = getFocusable();
      if (focusable.length === 0) {
        e.preventDefault();
        panel.focus();
        return;
      }
      const first = focusable[0]!;
      const last = focusable[focusable.length - 1]!;

      if (e.shiftKey) {
        if (document.activeElement === first || document.activeElement === panel) {
          e.preventDefault();
          last.focus();
        }
        return;
      }

      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  if (!open || !mounted) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? titleId : undefined}
      aria-describedby={description ? descriptionId : undefined}
      aria-label={!title ? "Dialog" : undefined}
      onMouseDown={(e) => {
        // Close when clicking the backdrop.
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="absolute inset-0 bg-black/60" />
      <div
        ref={panelRef}
        tabIndex={-1}
        className={cn(
          "relative z-10 w-full max-w-2xl rounded-lg border border-zinc-800 bg-zinc-950 shadow-xl",
          "outline-none"
        )}
      >
        {(title || description) && (
          <div className="border-b border-zinc-800 px-4 py-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                {title && (
                  <div id={titleId} className="truncate text-sm font-semibold text-zinc-50">
                    {title}
                  </div>
                )}
                {description && (
                  <div id={descriptionId} className="mt-1 text-xs text-zinc-400">
                    {description}
                  </div>
                )}
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="shrink-0"
                onClick={onClose}
                aria-label="Close dialog"
              >
                ✕
              </Button>
            </div>
          </div>
        )}

        <div className="max-h-[70vh] overflow-auto px-4 py-4">{children}</div>

        {footer && <div className="border-t border-zinc-800 px-4 py-3">{footer}</div>}
      </div>
    </div>,
    document.body
  );
}
