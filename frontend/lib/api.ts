import type { DashboardResponse, KpiCategoria, PriceRecord, SituacionCategoria } from "./types";

/**
 * URL del backend.
 *
 * En producción se recomienda API_URL (variable del servidor). Se mantiene
 * compatibilidad con NEXT_PUBLIC_API_URL para instalaciones ya existentes.
 */
const rawApiUrl =
  process.env.API_URL ||
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export const API_URL = rawApiUrl.replace(/\/$/, "");

const RETRYABLE_STATUS = new Set([502, 503, 504]);

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function cleanErrorBody(body: string): string {
  const trimmed = body.trim();
  if (!trimmed) return "sin detalle";
  if (/^<!doctype html/i.test(trimmed) || /^<html/i.test(trimmed)) {
    return "el servidor todavía se está iniciando o devolvió una página de error";
  }
  return trimmed.slice(0, 300);
}

async function fetchJson<T>(path: string, revalidateSeconds = 60): Promise<T> {
  const url = `${API_URL}${path}`;
  let lastError = "";

  // Render Free puede tardar en despertar. Reintentamos automáticamente.
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const res = await fetch(url, {
        next: { revalidate: revalidateSeconds },
        headers: { Accept: "application/json" },
      });

      if (res.ok) return res.json() as Promise<T>;

      const body = await res.text().catch(() => "");
      lastError = `HTTP ${res.status}: ${cleanErrorBody(body)}`;

      if (!RETRYABLE_STATUS.has(res.status) || attempt === 3) break;
    } catch (error) {
      lastError = error instanceof Error ? error.message : "error de conexión";
      if (attempt === 3) break;
    }

    await sleep(attempt * 2500);
  }

  throw new Error(
    `No se pudo consultar ${path} en ${API_URL}. ${lastError}. ` +
      "En el plan gratuito de Render, esperá unos segundos y recargá la página."
  );
}

export function getDashboard(): Promise<DashboardResponse> {
  return fetchJson<DashboardResponse>("/api/dashboard", 300);
}

export function getSituacionActual(): Promise<SituacionCategoria[]> {
  return fetchJson<SituacionCategoria[]>("/api/situacion-actual", 300);
}

export function getKpiCategoria(categoria: string): Promise<KpiCategoria> {
  return fetchJson<KpiCategoria>(`/api/dashboard/kpi/${encodeURIComponent(categoria)}`, 300);
}

export interface FiltrosHistorico {
  categoria?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  anio?: number;
  peso_min?: number;
  peso_max?: number;
}

export function getHistorico(filtros: FiltrosHistorico = {}): Promise<PriceRecord[]> {
  const params = new URLSearchParams();
  Object.entries(filtros).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  });
  const qs = params.toString();
  return fetchJson<PriceRecord[]>(`/api/precios/historico${qs ? `?${qs}` : ""}`, 120);
}

export function getCategorias(): Promise<{ categorias_oficiales: string[]; categorias_con_datos: string[] }> {
  return fetchJson("/api/categorias", 3600);
}
