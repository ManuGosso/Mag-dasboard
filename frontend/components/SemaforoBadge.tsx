import clsx from "clsx";

const CONFIG = {
  verde: { color: "bg-status-good", texto: "text-status-good", label: "Precio bajo (histórico)" },
  amarillo: { color: "bg-status-warning", texto: "text-status-warning", label: "Precio normal" },
  rojo: { color: "bg-status-critical", texto: "text-status-critical", label: "Precio elevado" },
} as const;

export default function SemaforoBadge({ estado }: { estado: "verde" | "amarillo" | "rojo" }) {
  const cfg = CONFIG[estado];
  return (
    <span className={clsx("inline-flex items-center gap-1.5 rounded-full border border-line-border bg-surface-page px-2.5 py-1 text-xs font-medium", cfg.texto)}>
      <span className={clsx("h-2 w-2 rounded-full", cfg.color)} />
      {cfg.label}
    </span>
  );
}
