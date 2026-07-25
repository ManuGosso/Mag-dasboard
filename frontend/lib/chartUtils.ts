import type { PriceRecord } from "./types";
import { CATEGORIAS } from "./types";

export const CATEGORIA_COLOR: Record<string, string> = {
  [CATEGORIAS[0]]: "#3987e5", // blue
  [CATEGORIAS[1]]: "#008300", // green
  [CATEGORIAS[2]]: "#d55181", // magenta
  [CATEGORIAS[3]]: "#c98500", // yellow
  [CATEGORIAS[4]]: "#199e70", // aqua
  [CATEGORIAS[5]]: "#d95926", // orange
};

export interface PuntoPivot {
  fecha: string;
  [categoria: string]: string | number | null;
}

/** Pivotea una lista de PriceRecord (varias categorias, varias fechas) a
 * una serie por fecha con una columna por categoria, lista para Recharts. */
export function pivotearPorFecha(registros: PriceRecord[]): PuntoPivot[] {
  const porFecha = new Map<string, PuntoPivot>();
  for (const r of registros) {
    if (!porFecha.has(r.fecha)) {
      porFecha.set(r.fecha, { fecha: r.fecha });
    }
    porFecha.get(r.fecha)![r.categoria] = r.precio_promedio;
  }
  return Array.from(porFecha.values()).sort((a, b) => a.fecha.localeCompare(b.fecha));
}
