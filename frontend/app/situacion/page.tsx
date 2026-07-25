import SemaforoBadge from "@/components/SemaforoBadge";
import { getSituacionActual } from "@/lib/api";
import { formatMoney, formatPct } from "@/lib/format";
import clsx from "clsx";

export const dynamic = "force-dynamic";

const SEMAFORO_BAR = {
  verde: "bg-status-good",
  amarillo: "bg-status-warning",
  rojo: "bg-status-critical",
} as const;

export default async function SituacionPage() {
  let situacion: Awaited<ReturnType<typeof getSituacionActual>> = [];
  let error: string | null = null;

  try {
    situacion = await getSituacionActual();
  } catch (e: any) {
    error = e?.message ?? "No se pudo cargar la situación actual";
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-primary">Situación actual del mercado</h1>
        <p className="text-sm text-ink-muted">
          Precio actual comparado contra el promedio de 12 y 24 meses, y contra el máximo/mínimo
          histórico registrado.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-4 rounded-lg border border-line-border bg-surface-card p-4 text-xs">
        <Leyenda color="bg-status-good" texto="Verde — precio bajo respecto al histórico" />
        <Leyenda color="bg-status-warning" texto="Amarillo — precio normal" />
        <Leyenda color="bg-status-critical" texto="Rojo — precio elevado respecto al histórico" />
      </div>

      {error && (
        <div className="rounded-md border border-status-critical/40 bg-status-critical/10 p-4 text-sm text-status-critical">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {situacion.map((s) => {
          const min = s.minimo_historico ?? 0;
          const max = s.maximo_historico ?? 0;
          const rango = Math.max(max - min, 1);
          const posActual = Math.min(Math.max(((s.precio_actual - min) / rango) * 100, 0), 100);
          const posProm12 =
            s.promedio_12m !== null
              ? Math.min(Math.max(((s.promedio_12m - min) / rango) * 100, 0), 100)
              : null;

          return (
            <div key={s.categoria} className="rounded-lg border border-line-border bg-surface-card p-5">
              <div className="flex items-start justify-between">
                <h3 className="text-sm font-semibold text-ink-primary">{s.categoria}</h3>
                <SemaforoBadge estado={s.semaforo} />
              </div>

              <div className="mt-3 flex items-baseline gap-2">
                <span className="tabular text-2xl font-semibold text-ink-primary">
                  {formatMoney(s.precio_actual, 0)}
                </span>
                <span className="text-xs text-ink-muted">/kg vivo actual</span>
              </div>

              <div className="mt-4">
                <div className="relative h-2 rounded-full bg-line-grid">
                  <div
                    className={clsx("absolute inset-y-0 left-0 rounded-full", SEMAFORO_BAR[s.semaforo])}
                    style={{ width: `${posActual}%`, opacity: 0.85 }}
                  />
                  {posProm12 !== null && (
                    <div
                      className="absolute top-1/2 h-3 w-0.5 -translate-y-1/2 bg-ink-primary/70"
                      style={{ left: `${posProm12}%` }}
                      title="Promedio 12 meses"
                    />
                  )}
                </div>
                <div className="mt-1 flex justify-between text-[10px] text-ink-muted">
                  <span>Mín. hist. {formatMoney(min, 0)}</span>
                  <span>Máx. hist. {formatMoney(max, 0)}</span>
                </div>
              </div>

              <dl className="mt-4 grid grid-cols-2 gap-y-2 border-t border-line-grid pt-3 text-xs">
                <dt className="text-ink-muted">Promedio 12 meses</dt>
                <dd className="tabular text-right text-ink-secondary">
                  {formatMoney(s.promedio_12m, 0)}
                </dd>
                <dt className="text-ink-muted">Promedio 24 meses</dt>
                <dd className="tabular text-right text-ink-secondary">
                  {formatMoney(s.promedio_24m, 0)}
                </dd>
                <dt className="text-ink-muted">Vs. promedio 12 meses</dt>
                <dd className="tabular text-right text-ink-secondary">
                  {formatPct(s.variacion_vs_promedio_12m_pct)}
                </dd>
              </dl>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Leyenda({ color, texto }: { color: string; texto: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-ink-secondary">
      <span className={clsx("h-2 w-2 rounded-full", color)} />
      {texto}
    </span>
  );
}
