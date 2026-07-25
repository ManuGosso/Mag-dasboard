"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import clsx from "clsx";

const LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/historico", label: "Histórico de precios" },
  { href: "/situacion", label: "Situación actual" },
];

export default function NavBar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-line-border bg-surface-page/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-series-1 text-xs font-bold text-white">
            MAG
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-ink-primary">
              Tablero Ganadero
            </p>
            <p className="text-[11px] text-ink-muted">Mercado Agroganadero de Cañuelas</p>
          </div>
        </div>

        <nav className="hidden items-center gap-1 md:flex">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={clsx(
                  "rounded-md px-3 py-1.5 text-sm transition-colors",
                  active
                    ? "bg-surface-card text-ink-primary"
                    : "text-ink-secondary hover:bg-surface-card hover:text-ink-primary"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <button
          className="rounded-md border border-line-border p-2 text-ink-secondary md:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Abrir menu"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {open && (
        <nav className="flex flex-col gap-1 border-t border-line-border px-4 py-2 md:hidden">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={clsx(
                  "rounded-md px-3 py-2 text-sm",
                  active
                    ? "bg-surface-card text-ink-primary"
                    : "text-ink-secondary hover:bg-surface-card hover:text-ink-primary"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      )}
    </header>
  );
}
