"use client";

import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { formatDate, formatMoney } from "@/lib/format";
import { pivotearPorFecha, CATEGORIA_COLOR } from "@/lib/chartUtils";
import type { PriceRecord } from "@/lib/types";

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-line-border bg-surface-card px-3 py-2 shadow-lg">
      <p className="mb-1 text-xs text-ink-muted">{formatDate(label)}</p>
      {payload.map((entry: any) => (
        <div key={entry.dataKey} className="flex items-center gap-2 text-xs">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-ink-secondary">{entry.dataKey}:</span>
          <span className="tabular font-medium text-ink-primary">{formatMoney(entry.value, 0)}</span>
        </div>
      ))}
    </div>
  );
}

export default function PriceChart({
  registros,
  categorias,
  titulo,
  subtitulo,
  altura = 340,
}: {
  registros: PriceRecord[];
  categorias: string[];
  titulo: string;
  subtitulo?: string;
  altura?: number;
}) {
  const [vistaTabla, setVistaTabla] = useState(false);
  const data = useMemo(() => pivotearPorFecha(registros), [registros]);

  const sinDatos = registros.length === 0;

  return (
    <div className="rounded-lg border border-line-border bg-surface-card p-5">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-ink-primary">{titulo}</h3>
          {subtitulo && <p className="text-[11px] text-ink-muted">{subtitulo}</p>}
        </div>
        <button
          onClick={() => setVistaTabla((v) => !v)}
          className="rounded-md border border-line-border px-2.5 py-1 text-[11px] text-ink-secondary hover:bg-surface-cardhover"
        >
          {vistaTabla ? "Ver gráfico" : "Ver tabla"}
        </button>
      </div>

      {sinDatos ? (
        <div
          className="flex items-center justify-center text-sm text-ink-muted"
          style={{ height: altura }}
        >
          Sin datos para los filtros seleccionados.
        </div>
      ) : vistaTabla ? (
        <div className="max-h-[340px] overflow-auto">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-surface-card">
              <tr className="border-b border-line-grid text-ink-muted">
                <th className="py-1.5 pr-3 font-medium">Fecha</th>
                {categorias.map((c) => (
                  <th key={c} className="py-1.5 pr-3 font-medium">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={row.fecha} className="tabular border-b border-line-grid/50 text-ink-secondary">
                  <td className="py-1.5 pr-3">{formatDate(row.fecha)}</td>
                  {categorias.map((c) => (
                    <td key={c} className="py-1.5 pr-3">
                      {row[c] !== undefined ? formatMoney(row[c] as number, 0) : "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={altura}>
          <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 4 }}>
            <CartesianGrid stroke="#2c2c2a" strokeDasharray="0" vertical={false} />
            <XAxis
              dataKey="fecha"
              tickFormatter={(v) => formatDate(v)}
              stroke="#898781"
              tick={{ fill: "#898781", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "#383835" }}
              minTickGap={40}
            />
            <YAxis
              stroke="#898781"
              tick={{ fill: "#898781", fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={64}
              tickFormatter={(v) => `$${Math.round(v / 100) / 10}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            {categorias.length > 1 && (
              <Legend
                wrapperStyle={{ fontSize: 11, color: "#c3c2b7" }}
                iconType="circle"
                iconSize={8}
              />
            )}
            {categorias.map((c) => (
              <Line
                key={c}
                type="monotone"
                dataKey={c}
                stroke={CATEGORIA_COLOR[c] || "#3987e5"}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2, stroke: "#1a1a19" }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
