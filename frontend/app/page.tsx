import KpiCard from "@/components/KpiCard";
import RelationCard from "@/components/RelationCard";
import PriceChart from "@/components/PriceChart";
import SemaforoBadge from "@/components/SemaforoBadge";
import { getDashboard, getHistorico, getSituacionActual } from "@/lib/api";
import { formatDate } from "@/lib/format";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  try {
    const [dashboard, situacion] = await Promise.all([getDashboard(), getSituacionActual()]);

    const [historicoTernero, historicoNovillo] = await Promise.all([
      getHistorico({ categoria: dashboard.ternero.categoria }),
      getHistorico({ categoria: dashboard.novillo.categoria }),
    ]);

    return (
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-xl font-semibold text-ink-primary">Dashboard principal</h1>
          <p className="text-sm text-ink-muted">
            Última actualización: {formatDate(dashboard.actualizado_en)}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <KpiCard
            titulo="Ternero (compra)"
            subtitulo={dashboard.ternero.categoria}
            kpi={dashboard.ternero}
            accentClassName="bg-series-1"
          />
          <KpiCard
            titulo="Novillo (venta)"
            subtitulo={dashboard.novillo.categoria}
            kpi={dashboard.novillo}
            accentClassName="bg-series-4"
          />
          <RelationCard relacion={dashboard.relacion_compra_venta} />
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <PriceChart
            registros={historicoTernero}
            categorias={[dashboard.ternero.categoria]}
            titulo={`Evolución del ${dashboard.ternero.categoria.toLowerCase()}`}
            subtitulo="Últimos 5 años · $/kg vivo"
          />
          <PriceChart
            registros={historicoNovillo}
            categorias={[dashboard.novillo.categoria]}
            titulo={`Evolución del ${dashboard.novillo.categoria.toLowerCase()}`}
            subtitulo="Últimos 5 años · $/kg vivo"
          />
        </div>

        <div className="rounded-lg border border-line-border bg-surface-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-ink-primary">
              Situación actual por categoría
            </h3>
            <Link href="/situacion" className="text-xs text-series-1 hover:underline">
              Ver análisis completo →
            </Link>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {situacion.map((s) => (
              <div
                key={s.categoria}
                className="flex items-center justify-between rounded-md border border-line-grid px-3 py-2.5"
              >
                <div>
                  <p className="text-xs font-medium text-ink-secondary">{s.categoria}</p>
                  <p className="tabular text-sm font-semibold text-ink-primary">
                    ${s.precio_actual.toLocaleString("es-AR")}
                  </p>
                </div>
                <SemaforoBadge estado={s.semaforo} />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  } catch (error: any) {
    return <SinDatos mensaje={error?.message} />;
  }
}

function SinDatos({ mensaje }: { mensaje?: string }) {
  return (
    <div className="mx-auto mt-16 max-w-lg rounded-lg border border-line-border bg-surface-card p-8 text-center">
      <h2 className="text-lg font-semibold text-ink-primary">Todavía no hay datos cargados</h2>
      <p className="mt-2 text-sm text-ink-secondary">
        Verificá que el backend esté corriendo (<code className="text-ink-primary">uvicorn app.main:app</code>)
        y que hayas ejecutado el seed de datos de muestra o el scraper:
      </p>
      <pre className="mt-3 overflow-x-auto rounded-md bg-surface-page p-3 text-left text-xs text-ink-secondary">
        cd backend{"\n"}
        python -m app.seed.generate_sample_data
      </pre>
      {mensaje && (
        <div className="mt-4 rounded-md border border-line-grid bg-surface-page p-3 text-left">
          <p className="text-xs font-medium text-ink-secondary">Problema de conexión</p>
          <p className="mt-1 break-words text-[11px] text-ink-muted">{mensaje}</p>
          <p className="mt-2 text-[11px] text-ink-muted">
            El plan gratuito de Render puede tardar hasta un minuto en iniciar. Esperá unos segundos y recargá.
          </p>
        </div>
      )}
    </div>
  );
}
