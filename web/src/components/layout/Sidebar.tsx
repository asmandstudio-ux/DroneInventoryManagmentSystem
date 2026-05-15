"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/providers/AuthProvider";

type NavItem = { href: string; label: string };

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Missions" },
  { href: "/dashboard/warehouses", label: "Warehouses" },
  { href: "/dashboard/scans", label: "Scans" },
  { href: "/dashboard/reports", label: "Reports" }
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="px-4 py-4">
        <div className="text-sm font-semibold text-zinc-100">Drone IMS</div>
        <div className="text-xs text-zinc-400">Warehouse ops dashboard</div>
      </div>

      <nav className="flex-1 space-y-1 px-2">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "block rounded-md px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-900 hover:text-zinc-50",
                active && "bg-zinc-900 text-zinc-50"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-800 p-3">
        <div className="mb-3">
          <div className="text-xs text-zinc-500">Signed in as</div>
          <div className="text-sm text-zinc-100">{user?.email ?? "—"}</div>
          <div className="text-xs text-zinc-400">{user?.role ?? ""}</div>
        </div>
        <Button variant="secondary" size="sm" className="w-full" onClick={logout}>
          Log out
        </Button>
      </div>
    </aside>
  );
}
