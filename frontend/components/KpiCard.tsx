import { formatDate, formatMoney } from "@/lib/format";
import DeltaBadge from "./DeltaBadge";
import type { KpiCategoria } from "@/lib/types";

export default function KpiCard({
  titulo,
  subtitulo,
  kpi,
  accentClassName,
}: {
  titulo: string;
  subtitulo: string;
  kpi: KpiCategoria;
  accentClassName: string;
}) {
  return (
    <div className="rounded-lg border border-line-border bg-surface-card p-5 transition-colors hover:bg-surface-cardhover">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${accentClassName}`} />
            <p className="text-sm font-medium text-ink-secondary">{titulo}</p>
          </div>
          <p className="mt-0.5 text-[11px] text-ink-muted">{subtitulo}</p>
        </div>
        <span className="text-[11px] text-ink-muted">{formatDate(kpi.fecha_actual)}</span>
      </div>

      <p className="tabular mt-3 text-3xl font-semibold text-ink-primary">
        {formatMoney(kpi.precio_actual, 0)}
        <span className="ml-1 text-sm font-normal text-ink-muted">/kg vivo</span>
      </p>

      <div className="mt-4 grid grid-cols-3 gap-3 border-t border-line-grid pt-3">
        <DeltaBadge label="Semanal" value={kpi.variacion_semanal_pct} />
        <DeltaBadge label="Mensual" value={kpi.variacion_mensual_pct} />
        <DeltaBadge label="Anual" value={kpi.variacion_anual_pct} />
      </div>
    </div>
  );
}
