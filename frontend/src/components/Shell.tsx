"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { can, useAuth, useRole } from "@/lib/role";
import type { Role } from "@/lib/types";

const NAV: { href: string; label: string; show?: (r: Role) => boolean }[] = [
  { href: "/", label: "Dashboard" },
  { href: "/calendar", label: "Calendar" },
  { href: "/patients", label: "Patients" },
  { href: "/appointments/new", label: "New booking", show: can.book },
  { href: "/reports", label: "Reports", show: can.reports },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const role = useRole();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  if (pathname === "/login") return <>{children}</>;
  const items = NAV.filter((n) => !n.show || n.show(role));

  return (
    <div className="min-h-screen md:flex">
      <aside className="border-b border-slate-200 bg-white md:sticky md:top-0 md:h-screen md:w-56 md:shrink-0 md:border-r md:border-b-0">
        <div className="flex items-center justify-between px-4 py-3 md:py-5">
          <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-teal-700">
            <span aria-hidden>🦷</span> DentalFlow
          </Link>
          <button
            type="button"
            className="rounded-md border border-slate-300 px-2 py-1 text-sm md:hidden"
            aria-expanded={menuOpen}
            aria-controls="main-nav"
            onClick={() => setMenuOpen((o) => !o)}
          >
            Menu
          </button>
        </div>
        <nav id="main-nav" className={`${menuOpen ? "block" : "hidden"} px-2 pb-3 md:block`}>
          <ul className="space-y-1">
            {items.map((n) => {
              const active = isActive(pathname, n.href);
              return (
                <li key={n.href}>
                  <Link
                    href={n.href}
                    onClick={() => setMenuOpen(false)}
                    aria-current={active ? "page" : undefined}
                    className={`block rounded-md px-3 py-2 text-sm font-medium ${
                      active ? "bg-teal-50 text-teal-800" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                    }`}
                  >
                    {n.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="flex items-center justify-end gap-3 border-b border-slate-200 bg-white px-4 py-2.5 md:px-8">
          <span className="text-sm text-slate-600">
            {user?.full_name} <span className="text-xs text-slate-400">({role})</span>
          </span>
          <button type="button" onClick={logout} className="rounded-md border border-slate-300 px-2 py-1 text-sm hover:bg-slate-50">
            Log out
          </button>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}

/** Shows `children` only to roles allowed by `allow`; others get a short message. */
export function RoleGate({ allow, children }: { allow: (r: Role) => boolean; children: ReactNode }) {
  const role = useRole();
  if (allow(role)) return <>{children}</>;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-6 py-10 text-center text-slate-600">
      You don&apos;t have access to this page as <strong>{role}</strong>.
    </div>
  );
}
