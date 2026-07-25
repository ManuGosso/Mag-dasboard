export type Categoria =
  | "Terneros"
  | "Novillitos 300-390 kg"
  | "Novillitos 391-430 kg"
  | "Novillos +430 kg"
  | "Vaquillonas"
  | "Vacas";

export const CATEGORIAS: Categoria[] = [
  "Terneros",
  "Novillitos 300-390 kg",
  "Novillitos 391-430 kg",
  "Novillos +430 kg",
  "Vaquillonas",
  "Vacas",
];

export interface PriceRecord {
  id: number;
  fecha: string;
  categoria: string;
  peso_promedio: number | null;
  precio_promedio: number;
  precio_maximo: number | null;
  precio_minimo: number | null;
  cabezas: number | null;
  kg_comercializados: number | null;
  fuente: string;
}

export interface KpiCategoria {
  categoria: string;
  precio_actual: number;
  fecha_actual: string;
  variacion_semanal_pct: number | null;
  variacion_mensual_pct: number | null;
  variacion_anual_pct: number | null;
}

export interface DashboardResponse {
  ternero: KpiCategoria;
  novillo: KpiCategoria;
  relacion_compra_venta: number | null;
  actualizado_en: string;
}

export interface SituacionCategoria {
  categoria: string;
  precio_actual: number;
  promedio_12m: number | null;
  promedio_24m: number | null;
  maximo_historico: number | null;
  minimo_historico: number | null;
  variacion_vs_promedio_12m_pct: number | null;
  semaforo: "verde" | "amarillo" | "rojo";
}
