import clsx from "clsx";
import { formatPct } from "@/lib/format";

export default function DeltaBadge({
  value,
  label,
}: {
  value: number | null | undefined;
  label?: string;
}) {
  const positivo = value !== null && value !== undefined && value > 0;
  const negativo = value !== null && value !== undefined && value < 0;

  return (
    <div className="flex flex-col items-start gap-0.5">
      {label && <span className="text-[11px] text-ink-muted">{label}</span>}
      <span
        className={clsx(
          "tabular inline-flex items-center gap-1 text-sm font-medium",
          positivo && "text-status-good",
          negativo && "text-status-critical",
          !positivo && !negativo && "text-ink-muted"
        )}
      >
        {positivo && (
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M5 1.5L8.5 7H1.5L5 1.5Z" fill="currentColor" />
          </svg>
        )}
        {negativo && (
          <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
            <path d="M5 8.5L1.5 3H8.5L5 8.5Z" fill="currentColor" />
          </svg>
        )}
        {formatPct(value)}
      </span>
    </div>
  );
}
