export default function RelationCard({ relacion }: { relacion: number | null }) {
  return (
    <div className="rounded-lg border border-line-border bg-surface-card p-5">
      <p className="text-sm font-medium text-ink-secondary">Relación compra/venta</p>
      <p className="mt-0.5 text-[11px] text-ink-muted">
        Precio ternero ($/kg vivo) ÷ precio novillo ($/kg vivo)
      </p>

      <p className="tabular mt-3 text-3xl font-semibold text-ink-primary">
        {relacion !== null ? relacion.toFixed(2) : "—"}
      </p>

      <p className="mt-4 border-t border-line-grid pt-3 text-xs leading-relaxed text-ink-muted">
        {relacion !== null && relacion > 1
          ? "El ternero de compra cuesta más por kilo que el novillo de venta: la relación es desfavorable para la recría/invernada."
          : "El ternero de compra cuesta menos por kilo que el novillo de venta: la relación favorece a la recría/invernada."}
      </p>
    </div>
  );
}
