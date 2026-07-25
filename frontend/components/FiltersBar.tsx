"use client";

import type { ReactNode } from "react";
import { CATEGORIAS } from "@/lib/types";

export interface FiltrosState {
  categoria: string;
  anio: string;
  fecha_desde: string;
  fecha_hasta: string;
  peso_min: string;
  peso_max: string;
}

const ANIOS = Array.from({ length: 6 }, (_, i) => new Date().getFullYear() - i);

export default function FiltersBar({
  filtros,
  onChange,
  onReset,
}: {
  filtros: FiltrosState;
  onChange: (f: FiltrosState) => void;
  onReset: () => void;
}) {
  function set<K extends keyof FiltrosState>(key: K, value: FiltrosState[K]) {
    onChange({ ...filtros, [key]: value });
  }

  return (
    <div className="flex flex-wrap items-end gap-3 rounded-lg border border-line-border bg-surface-card p-4">
      <Field label="Categoría">
        <select
          value={filtros.categoria}
          onChange={(e) => set("categoria", e.target.value)}
          className="input"
        >
          <option value="">Todas</option>
          {CATEGORIAS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Año">
        <select value={filtros.anio} onChange={(e) => set("anio", e.target.value)} className="input">
          <option value="">Últimos 5 años</option>
          {ANIOS.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Fecha desde">
        <input
          type="date"
          value={filtros.fecha_desde}
          onChange={(e) => set("fecha_desde", e.target.value)}
          className="input"
        />
      </Field>

      <Field label="Fecha hasta">
        <input
          type="date"
          value={filtros.fecha_hasta}
          onChange={(e) => set("fecha_hasta", e.target.value)}
          className="input"
        />
      </Field>

      <Field label="Peso mín. (kg)">
        <input
          type="number"
          placeholder="—"
          value={filtros.peso_min}
          onChange={(e) => set("peso_min", e.target.value)}
          className="input w-24"
        />
      </Field>

      <Field label="Peso máx. (kg)">
        <input
          type="number"
          placeholder="—"
          value={filtros.peso_max}
          onChange={(e) => set("peso_max", e.target.value)}
          className="input w-24"
        />
      </Field>

      <button
        onClick={onReset}
        className="ml-auto rounded-md border border-line-border px-3 py-1.5 text-xs text-ink-secondary hover:bg-surface-cardhover"
      >
        Limpiar filtros
      </button>

      <style jsx global>{`
        .input {
          background-color: #0d0d0d;
          border: 1px solid #383835;
          border-radius: 6px;
          padding: 6px 8px;
          font-size: 12.5px;
          color: #ffffff;
          min-width: 130px;
        }
        .input:focus {
          outline: none;
          border-color: #3987e5;
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] text-ink-muted">{label}</span>
      {children}
    </label>
  );
}
