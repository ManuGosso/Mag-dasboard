"use client";

import { useEffect, useMemo, useState } from "react";
import FiltersBar, { FiltrosState } from "@/components/FiltersBar";
import PriceChart from "@/components/PriceChart";
import { getHistorico } from "@/lib/api";
import { CATEGORIAS } from "@/lib/types";
import type { PriceRecord } from "@/lib/types";

const FILTROS_VACIOS: FiltrosState = {
  categoria: "",
  anio: "",
  fecha_desde: "",
  fecha_hasta: "",
  peso_min: "",
  peso_max: "",
};

export default function HistoricoPage() {
  const [filtros, setFiltros] = useState<FiltrosState>(FILTROS_VACIOS);
  const [registros, setRegistros] = useState<PriceRecord[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCargando(true);
    setError(null);

    getHistorico({
      categoria: filtros.categoria || undefined,
      anio: filtros.anio ? Number(filtros.anio) : undefined,
      fecha_desde: filtros.fecha_desde || undefined,
      fecha_hasta: filtros.fecha_hasta || undefined,
      peso_min: filtros.peso_min ? Number(filtros.peso_min) : undefined,
      peso_max: filtros.peso_max ? Number(filtros.peso_max) : undefined,
    })
      .then((data) => {
        if (!cancelado) setRegistros(data);
      })
      .catch((err) => {
        if (!cancelado) setError(err?.message ?? "Error al cargar datos");
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });

    return () => {
      cancelado = true;
    };
  }, [filtros]);

  const categoriasPresentes = useMemo(() => {
    const set = new Set(registros.map((r) => r.categoria));
    return CATEGORIAS.filter((c) => set.has(c));
  }, [registros]);

  const registrosTernero = useMemo(
    () => registros.filter((r) => r.categoria === "Terneros"),
    [registros]
  );
  const registrosNovillo = useMemo(
    () => registros.filter((r) => r.categoria === "Novillos +430 kg"),
    [registros]
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-primary">Histórico de precios</h1>
        <p className="text-sm text-ink-muted">
          Evolución de precios por categoría, con filtros por fecha, año, categoría y peso.
        </p>
      </div>

      <FiltersBar filtros={filtros} onChange={setFiltros} onReset={() => setFiltros(FILTROS_VACIOS)} />

      {error && (
        <div className="rounded-md border border-status-critical/40 bg-status-critical/10 p-3 text-sm text-status-critical">
          {error}
        </div>
      )}

      {cargando ? (
        <div className="rounded-lg border border-line-border bg-surface-card p-10 text-center text-sm text-ink-muted">
          Cargando datos…
        </div>
      ) : (
        <>
          {!filtros.categoria && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <PriceChart
                registros={registrosTernero}
                categorias={["Terneros"]}
                titulo="Evolución del ternero"
                subtitulo="$/kg vivo"
              />
              <PriceChart
                registros={registrosNovillo}
                categorias={["Novillos +430 kg"]}
                titulo="Evolución del novillo"
                subtitulo="$/kg vivo"
              />
            </div>
          )}

          <PriceChart
            registros={registros}
            categorias={filtros.categoria ? [filtros.categoria] : categoriasPresentes}
            titulo={filtros.categoria ? `Evolución — ${filtros.categoria}` : "Evolución por categoría"}
            subtitulo={`${registros.length.toLocaleString("es-AR")} registros en el rango seleccionado`}
            altura={420}
          />
        </>
      )}
    </div>
  );
}
